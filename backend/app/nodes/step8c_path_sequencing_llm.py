"""Step 8c — Path Sequencing.

Build a 3-card evidence path per assumption from Step 8b candidates.
The deterministic pass enforces evidence progression and card-library
ordering hints. An optional LLM pass can refine sequencing rationale.
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


EVIDENCE_ORDER = {"Weak": 1, "Medium": 2, "Strong": 3}


@dataclass(frozen=True)
class ExperimentCard:
    name: str
    category: str
    evidence_strength: str
    usually_runs_after: list[str]
    usually_runs_next: list[str]


class PathCard(BaseModel):
    card_name: str
    evidence_strength: Literal["Weak", "Medium", "Strong"]
    sequence_reason: str


class AssumptionPath(BaseModel):
    assumption: str
    category: Literal["Desirability", "Viability", "Feasibility"]
    existing_evidence_level: Literal["None", "Weak", "Medium"]
    path_cards: list[PathCard] = Field(min_length=3, max_length=3)
    sequencing_rationale: str


class PathBatch(BaseModel):
    paths: list[AssumptionPath]


def _load_cards() -> dict[str, ExperimentCard]:
    library = PatternLibraryLoader().load_library("experiment-library.json").data
    if int(library["metadata"].get("card_count", 0)) != 44:
        raise ValueError("Unexpected experiment card count")
    return {
        item["name"]: ExperimentCard(
            name=item["name"],
            category=item["category"],
            evidence_strength=item["evidence_strength"],
            usually_runs_after=item["usually_runs_after"],
            usually_runs_next=item["usually_runs_next"],
        )
        for item in library["experiments"]
    }


def _find_candidate(selection: dict[str, object], card_name: str) -> dict[str, object] | None:
    for candidate in selection.get("candidates") or []:
        if str(candidate.get("card_name", "")) == card_name:
            return candidate
    return None


def _non_decreasing_cards(
    previous_card: ExperimentCard,
    candidate_names: list[str],
    cards: dict[str, ExperimentCard],
) -> list[str]:
    previous_rank = EVIDENCE_ORDER[cards[previous_card.name].evidence_strength]
    return [
        name
        for name in candidate_names
        if EVIDENCE_ORDER[cards[name].evidence_strength] >= previous_rank
    ]


def _pick_next_name(
    previous_name: str,
    remaining_names: list[str],
    cards: dict[str, ExperimentCard],
) -> str | None:
    if not remaining_names:
        return None

    previous = cards[previous_name]
    non_decreasing = _non_decreasing_cards(previous, remaining_names, cards)
    pool = non_decreasing or remaining_names

    for name in pool:
        card = cards[name]
        if name in previous.usually_runs_next or previous_name in card.usually_runs_after:
            return name
    return pool[0]


def _deterministic_path(
    selection: dict[str, object],
    cards: dict[str, ExperimentCard],
) -> dict[str, object]:
    assumption = str(selection.get("assumption", "")).strip()
    category = str(selection.get("category", "")).strip()
    existing = str(selection.get("existing_evidence_level", "None")).strip()
    primary = str(selection.get("primary_card_name", "")).strip()

    ordered_names = [
        str(candidate.get("card_name", "")).strip()
        for candidate in selection.get("candidates") or []
        if str(candidate.get("card_name", "")).strip() in cards
    ]
    deduped_names: list[str] = []
    for name in ordered_names:
        if name not in deduped_names:
            deduped_names.append(name)

    if primary and primary in deduped_names:
        deduped_names.remove(primary)
        deduped_names.insert(0, primary)

    if not deduped_names:
        return {
            "assumption": assumption,
            "category": category,
            "existing_evidence_level": existing,
            "path_cards": [],
            "sequencing_rationale": "No valid candidates available.",
        }

    first = deduped_names[0]
    remaining = [name for name in deduped_names[1:]]

    second = _pick_next_name(first, remaining, cards)
    if second:
        remaining = [name for name in remaining if name != second]

    third = _pick_next_name(second or first, remaining, cards)

    chosen = [name for name in [first, second, third] if name]
    if len(chosen) < 3:
        for name in deduped_names:
            if len(chosen) >= 3:
                break
            if name not in chosen:
                chosen.append(name)

    chosen = chosen[:3]
    path_cards: list[dict[str, object]] = []
    for idx, name in enumerate(chosen, start=1):
        candidate = _find_candidate(selection, name)
        rationale = str((candidate or {}).get("rationale", "")).strip()
        path_cards.append(
            {
                "card_name": name,
                "evidence_strength": cards[name].evidence_strength,
                "sequence_reason": rationale or f"Step {idx} in the evidence escalation path.",
            }
        )

    return {
        "assumption": assumption,
        "category": category,
        "existing_evidence_level": existing,
        "path_cards": path_cards,
        "sequencing_rationale": "Deterministic sequence based on Step 8b ranking and canonical run-order hints.",
    }


def _build_messages(
    deterministic_paths: list[dict[str, object]],
    selections: list[dict[str, object]],
) -> list[SystemMessage | HumanMessage]:
    system_prompt = (
        "You are the Step 8c Path Sequencing agent for the BMI consultant workflow.\n\n"
        "Given evidence-gated card selections per assumption, produce exactly 3 cards\n"
        "that form a coherent progression from lower to higher confidence.\n\n"
        "RULES:\n"
        "- Use only card names from each assumption's allowed list.\n"
        "- Keep evidence strength non-decreasing across the 3 cards.\n"
        "- Respect sequencing relationships where possible (usually_runs_next / usually_runs_after).\n"
        "- Preserve assumption/category alignment exactly.\n"
        "- Provide concise sequencing rationale for each assumption."
    )

    blocks: list[str] = []
    for idx, (deterministic, selection) in enumerate(zip(deterministic_paths, selections, strict=False), start=1):
        allowed_lines = "\n".join(
            f"- {str(c.get('card_name', '')).strip()} [{str(c.get('evidence_strength', '')).strip()}]"
            for c in selection.get("candidates") or []
        )
        default_path = " -> ".join(
            f"{c['card_name']} [{c['evidence_strength']}]"
            for c in deterministic.get("path_cards") or []
        )
        blocks.append(
            "\n".join(
                [
                    f"### Assumption {idx}",
                    f"Assumption: {deterministic.get('assumption', '')}",
                    f"Category: {deterministic.get('category', '')}",
                    f"Existing evidence level: {deterministic.get('existing_evidence_level', 'None')}",
                    "Allowed cards:",
                    allowed_lines or "(none)",
                    "Deterministic default path:",
                    default_path or "(none)",
                ]
            )
        )

    user_prompt = (
        "Return one AssumptionPath per assumption block, in order.\n\n"
        + "\n\n".join(blocks)
    )
    return [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]


def _is_non_decreasing(path_cards: list[dict[str, object]]) -> bool:
    for i in range(1, len(path_cards)):
        prev_rank = EVIDENCE_ORDER[str(path_cards[i - 1]["evidence_strength"])]
        cur_rank = EVIDENCE_ORDER[str(path_cards[i]["evidence_strength"])]
        if cur_rank < prev_rank:
            return False
    return True


def _normalize_with_fallback(
    llm_paths: list[AssumptionPath],
    deterministic_paths: list[dict[str, object]],
    selections: list[dict[str, object]],
    cards: dict[str, ExperimentCard],
) -> list[dict[str, object]]:
    by_assumption = {p.assumption: p for p in llm_paths}
    normalized: list[dict[str, object]] = []

    for deterministic, selection in zip(deterministic_paths, selections, strict=False):
        assumption = str(deterministic.get("assumption", "")).strip()
        allowed = {
            str(candidate.get("card_name", "")).strip()
            for candidate in selection.get("candidates") or []
            if str(candidate.get("card_name", "")).strip()
        }
        candidate = by_assumption.get(assumption)
        if candidate is None:
            normalized.append(deterministic)
            continue

        candidate_cards = [
            {
                "card_name": c.card_name,
                "evidence_strength": cards[c.card_name].evidence_strength,
                "sequence_reason": c.sequence_reason,
            }
            for c in candidate.path_cards
            if c.card_name in cards and c.card_name in allowed
        ]

        deduped_cards: list[dict[str, object]] = []
        for card in candidate_cards:
            if any(existing["card_name"] == card["card_name"] for existing in deduped_cards):
                continue
            deduped_cards.append(card)

        if len(deduped_cards) != 3 or not _is_non_decreasing(deduped_cards):
            normalized.append(deterministic)
            continue

        normalized.append(
            {
                "assumption": assumption,
                "category": deterministic["category"],
                "existing_evidence_level": deterministic["existing_evidence_level"],
                "path_cards": deduped_cards,
                "sequencing_rationale": candidate.sequencing_rationale,
            }
        )

    return normalized


def run_step8c_llm(state: BMIWorkflowState, llm: BaseChatModel | None) -> BMIWorkflowState:
    selections = state.get("experiment_card_selections") or []
    if not selections:
        return {
            **state,
            "current_step": "path_sequencing",
            "experiment_paths": [],
        }

    cards = _load_cards()
    deterministic_paths = [_deterministic_path(selection, cards) for selection in selections]

    if llm is None:
        return {
            **state,
            "current_step": "path_sequencing",
            "experiment_paths": deterministic_paths,
        }

    messages = _build_messages(deterministic_paths, selections)
    structured_llm = llm.with_structured_output(PathBatch)

    try:
        result: PathBatch = invoke_with_retry(
            structured_llm, messages, step_name="step8c_path_sequencing"
        )
        paths = _normalize_with_fallback(result.paths, deterministic_paths, selections, cards)
    except RuntimeError:
        paths = deterministic_paths

    return {
        **state,
        "current_step": "path_sequencing",
        "experiment_paths": paths,
    }