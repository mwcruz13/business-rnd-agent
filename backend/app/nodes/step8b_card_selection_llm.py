"""Step 8b — Experiment Card Selection.

Select 3-5 ranked experiment cards per assumption using:
1) Assumption content and DVF category
2) Existing evidence level from Step 8a
3) Canonical 44-card experiment library constraints

When existing evidence is already Weak or Medium, lower-evidence cards are
excluded so recommendations do not mechanically restart from the weakest tier.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from backend.app.llm.retry import invoke_with_retry
from backend.app.patterns.loader import PatternLibraryLoader
from backend.app.state import BMIWorkflowState


EVIDENCE_ORDER = {"None": 0, "Weak": 1, "Medium": 2, "Strong": 3}


@dataclass(frozen=True)
class ExperimentCard:
    name: str
    category: str
    evidence_strength: str
    what_it_tests: str
    best_used_when: str
    usually_runs_after: list[str]
    usually_runs_next: list[str]


class CardCandidate(BaseModel):
    card_name: str
    evidence_strength: Literal["Weak", "Medium", "Strong"]
    rationale: str = Field(description="Why this card fits the specific assumption now.")


class AssumptionSelection(BaseModel):
    assumption: str
    category: Literal["Desirability", "Viability", "Feasibility"]
    existing_evidence_level: Literal["None", "Weak", "Medium"]
    candidates: list[CardCandidate] = Field(min_length=3, max_length=5)
    primary_card_name: str
    alternatives_considered: str


class SelectionBatch(BaseModel):
    selections: list[AssumptionSelection]


def _load_cards() -> dict[str, ExperimentCard]:
    library = PatternLibraryLoader().load_library("experiment-library.json").data
    if int(library["metadata"].get("card_count", 0)) != 44:
        raise ValueError("Unexpected experiment card count")
    return {
        item["name"]: ExperimentCard(
            name=item["name"],
            category=item["category"],
            evidence_strength=item["evidence_strength"],
            what_it_tests=item["what_it_tests"],
            best_used_when=item["best_used_when"],
            usually_runs_after=item["usually_runs_after"],
            usually_runs_next=item["usually_runs_next"],
        )
        for item in library["experiments"]
    }


def _min_card_strength(existing_level: str) -> str:
    # If we already have Weak evidence, start at Medium. If Medium, start at Strong.
    if existing_level == "Weak":
        return "Medium"
    if existing_level == "Medium":
        return "Strong"
    return "Weak"


def _allowed_cards_for_assumption(
    cards: dict[str, ExperimentCard],
    category: str,
    existing_level: str,
) -> list[ExperimentCard]:
    min_strength = _min_card_strength(existing_level)
    min_rank = EVIDENCE_ORDER[min_strength]
    candidates = [
        c
        for c in cards.values()
        if c.category == category and EVIDENCE_ORDER[c.evidence_strength] >= min_rank
    ]
    return sorted(candidates, key=lambda c: (EVIDENCE_ORDER[c.evidence_strength], c.name))


def _build_messages(
    state: BMIWorkflowState,
    cards: dict[str, ExperimentCard],
) -> list[SystemMessage | HumanMessage]:
    audits = state.get("assumption_evidence_audit") or []
    if not audits:
        raise ValueError("assumption_evidence_audit is required for Step 8b")

    system_prompt = (
        "You are the Step 8b Card Selection agent for the BMI consultant workflow.\n\n"
        "Select 3-5 canonical experiment cards per audited assumption.\n\n"
        "RULES:\n"
        "- Use ONLY card names from the provided allowed-card list for each assumption.\n"
        "- Pick 3-5 ranked candidates and set primary_card_name to the first one.\n"
        "- Explain why each candidate fits this specific assumption now.\n"
        "- Respect evidence gating:\n"
        "  * existing_evidence_level=None -> allowed starts at Weak\n"
        "  * existing_evidence_level=Weak -> allowed starts at Medium (skip Weak)\n"
        "  * existing_evidence_level=Medium -> allowed starts at Strong (skip Weak/Medium)\n"
        "- Different assumptions in the same category should usually not receive identical top candidates unless their risk language is genuinely equivalent.\n"
        "- Do not hallucinate card names."
    )

    blocks: list[str] = []
    for idx, audit in enumerate(audits, start=1):
        assumption = str(audit.get("assumption", "")).strip()
        category = str(audit.get("category", "")).strip()
        existing = str(audit.get("existing_evidence_level", "None")).strip()
        summary = str(audit.get("evidence_summary", "")).strip()

        allowed = _allowed_cards_for_assumption(cards, category, existing)
        allowed_lines = "\n".join(
            f"- {c.name} [{c.evidence_strength}] | tests: {c.what_it_tests} | best used when: {c.best_used_when}"
            for c in allowed
        )
        blocks.append(
            "\n".join(
                [
                    f"### Assumption {idx}",
                    f"Assumption: {assumption}",
                    f"Category: {category}",
                    f"Existing evidence level: {existing}",
                    f"Evidence summary: {summary or '(none provided)'}",
                    "Allowed cards for this assumption:",
                    allowed_lines or "(none)",
                ]
            )
        )

    user_prompt = (
        "Return one AssumptionSelection per assumption block, in order.\n\n"
        + "\n\n".join(blocks)
    )

    return [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]


def _validate_and_normalize(
    selections: list[AssumptionSelection],
    state: BMIWorkflowState,
    cards: dict[str, ExperimentCard],
) -> list[dict[str, object]]:
    audits = state.get("assumption_evidence_audit") or []
    by_assumption = {s.assumption: s for s in selections}

    normalized: list[dict[str, object]] = []
    for audit in audits:
        assumption = str(audit.get("assumption", "")).strip()
        category = str(audit.get("category", "")).strip()
        existing = str(audit.get("existing_evidence_level", "None")).strip()

        selected = by_assumption.get(assumption)
        allowed_names = {
            c.name
            for c in _allowed_cards_for_assumption(cards, category, existing)
        }

        if selected is None:
            fallback_cards = list(allowed_names)[:3]
            candidates = [
                {
                    "card_name": name,
                    "evidence_strength": cards[name].evidence_strength,
                    "rationale": "Fallback selection because LLM output did not include this assumption.",
                }
                for name in fallback_cards
            ]
            primary = fallback_cards[0] if fallback_cards else None
            normalized.append(
                {
                    "assumption": assumption,
                    "category": category,
                    "existing_evidence_level": existing,
                    "candidates": candidates,
                    "primary_card_name": primary,
                    "alternatives_considered": "Fallback list based on evidence-gated canonical cards.",
                }
            )
            continue

        kept: list[dict[str, object]] = []
        for cand in selected.candidates:
            if cand.card_name not in cards:
                continue
            if cand.card_name not in allowed_names:
                continue
            kept.append(
                {
                    "card_name": cand.card_name,
                    "evidence_strength": cards[cand.card_name].evidence_strength,
                    "rationale": cand.rationale,
                }
            )

        if len(kept) < 3:
            for name in sorted(allowed_names):
                if len(kept) >= 3:
                    break
                if any(c["card_name"] == name for c in kept):
                    continue
                kept.append(
                    {
                        "card_name": name,
                        "evidence_strength": cards[name].evidence_strength,
                        "rationale": "Fallback to complete minimum candidate set.",
                    }
                )

        kept = kept[:5]
        primary = selected.primary_card_name if selected.primary_card_name in {c["card_name"] for c in kept} else kept[0]["card_name"]

        normalized.append(
            {
                "assumption": assumption,
                "category": category,
                "existing_evidence_level": existing,
                "candidates": kept,
                "primary_card_name": primary,
                "alternatives_considered": selected.alternatives_considered,
            }
        )

    return normalized


def _fallback_selection(
    state: BMIWorkflowState,
    cards: dict[str, ExperimentCard],
) -> list[dict[str, object]]:
    selections: list[dict[str, object]] = []
    for audit in state.get("assumption_evidence_audit") or []:
        assumption = str(audit.get("assumption", "")).strip()
        category = str(audit.get("category", "")).strip()
        existing = str(audit.get("existing_evidence_level", "None")).strip()
        allowed = _allowed_cards_for_assumption(cards, category, existing)
        top = allowed[:3]
        selections.append(
            {
                "assumption": assumption,
                "category": category,
                "existing_evidence_level": existing,
                "candidates": [
                    {
                        "card_name": c.name,
                        "evidence_strength": c.evidence_strength,
                        "rationale": "Fallback evidence-gated deterministic selection.",
                    }
                    for c in top
                ],
                "primary_card_name": top[0].name if top else None,
                "alternatives_considered": "Deterministic fallback based on canonical evidence-gated list.",
            }
        )
    return selections


def run_step8b_llm(state: BMIWorkflowState, llm: BaseChatModel | None) -> BMIWorkflowState:
    cards = _load_cards()

    audits = state.get("assumption_evidence_audit") or []
    if not audits:
        return {
            **state,
            "current_step": "card_selection",
            "experiment_card_selections": [],
        }

    if llm is None:
        return {
            **state,
            "current_step": "card_selection",
            "experiment_card_selections": _fallback_selection(state, cards),
        }

    messages = _build_messages(state, cards)
    structured_llm = llm.with_structured_output(SelectionBatch)

    try:
        result: SelectionBatch = invoke_with_retry(
            structured_llm, messages, step_name="step8b_card_selection"
        )
        selections = _validate_and_normalize(result.selections, state, cards)
    except RuntimeError:
        selections = _fallback_selection(state, cards)

    return {
        **state,
        "current_step": "card_selection",
        "experiment_card_selections": selections,
    }
