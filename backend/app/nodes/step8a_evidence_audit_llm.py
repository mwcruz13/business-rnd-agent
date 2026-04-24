"""Step 8a — Evidence Audit.

For each Test-first assumption produced by Step 7, classify what evidence
the upstream Voice-of-Customer / signal context already contains. The
output drives Step 8b card selection: assumptions with existing Weak
evidence skip Weak-tier cards and start their experiment path at the
Medium tier.

LLM-backed. Falls back to ``voc_evidence_strength`` from Step 7 when the
LLM call fails or no test-first assumptions exist.
"""
from __future__ import annotations

from typing import Literal

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from backend.app.llm.retry import invoke_with_retry
from backend.app.state import BMIWorkflowState


# ---------------------------------------------------------------------------
# Output schema
# ---------------------------------------------------------------------------


class EvidenceAudit(BaseModel):
    assumption: str = Field(description="The exact assumption text being audited.")
    category: Literal["Desirability", "Viability", "Feasibility"]
    existing_evidence_level: Literal["None", "Weak", "Medium"] = Field(
        description=(
            "How much evidence already exists for this assumption in the upstream "
            "VoC/signal context. 'None' = silent. 'Weak' = anecdotal/indirect. "
            "'Medium' = direct behavioral observations or multiple corroborating signals. "
            "Never assign 'Strong' — that requires a deliberate experiment."
        )
    )
    evidence_summary: str = Field(
        description=(
            "1-3 sentences describing the actual VoC/signal evidence (or its absence) that "
            "justifies the level. Quote or paraphrase specific upstream content."
        )
    )


class EvidenceAuditList(BaseModel):
    audits: list[EvidenceAudit] = Field(
        description="One audit entry per Test-first assumption, in the same order.",
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _extract_test_first(state: BMIWorkflowState) -> list[dict[str, object]]:
    """Return ordered list of Test-first assumption dicts from step7_structured."""
    structured = state.get("step7_structured") or {}
    rows: list[dict[str, object]] = []
    for cat in structured.get("categories", []):
        category = cat.get("category", "")
        for a in cat.get("assumptions", []):
            if a.get("suggested_quadrant") == "Test first":
                text = a.get("assumption", "")
                if not text.startswith("I believe"):
                    text = f"I believe {text}"
                rows.append({
                    "assumption": text,
                    "category": category,
                    "voc_evidence_strength": a.get("voc_evidence_strength", "None"),
                })
    return rows


def _build_messages(
    state: BMIWorkflowState,
    test_first: list[dict[str, object]],
) -> list[SystemMessage | HumanMessage]:
    voc = str(state.get("voc_data", "")).strip()
    profile = str(state.get("customer_profile", "")).strip()
    signals = state.get("signals") or []
    interpreted = state.get("interpreted_signals") or []

    system_prompt = (
        "You are the Step 8a Evidence Audit agent for the BMI consultant workflow.\n\n"
        "Your task: for each Test-first assumption, classify how much evidence already "
        "exists in the upstream Voice-of-Customer (VoC) and signal context.\n\n"
        "RULES:\n"
        "- Output one audit per assumption, in the same order as the input list.\n"
        "- existing_evidence_level must be one of: None, Weak, Medium.\n"
        "    * None — the VoC and signals are silent on this assumption.\n"
        "    * Weak — anecdotal references, isolated mentions, or indirect signals.\n"
        "    * Medium — direct behavioral observations, multiple corroborating signals, "
        "or sustained customer commentary on the exact concern.\n"
        "- NEVER assign 'Strong' — Strong evidence requires a deliberate experiment.\n"
        "- evidence_summary must quote or paraphrase the actual VoC/signal content that "
        "justifies the level. If evidence is absent, say so explicitly.\n"
        "- Do not invent evidence that is not in the provided context.\n"
        "- Be conservative: when in doubt, assign the lower level."
    )

    assumption_block = "\n".join(
        f"- [{row['category']}] {row['assumption']} "
        f"(Step 7 voc_evidence_strength hint: {row.get('voc_evidence_strength', 'None')})"
        for row in test_first
    )

    signal_block = ""
    if signals:
        signal_block = "\n\n## Signals (Step 1 output)\n" + "\n".join(
            f"- {s.get('summary') or s.get('text') or s}" for s in signals[:25]
        )
    if interpreted:
        signal_block += "\n\n## Interpreted Signals\n" + "\n".join(
            f"- {s.get('summary') or s.get('text') or s}" for s in interpreted[:15]
        )

    user_prompt = (
        f"## Test-first assumptions to audit (in order)\n{assumption_block}\n\n"
        f"## Voice-of-Customer raw input\n{voc[:8000] if voc else '(empty)'}\n\n"
        f"## Customer profile\n{profile[:4000] if profile else '(empty)'}"
        f"{signal_block}"
    )

    return [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]


def _fallback_audits(test_first: list[dict[str, object]]) -> list[dict[str, object]]:
    """Build audits from Step 7's voc_evidence_strength when LLM is unavailable."""
    fallbacks: list[dict[str, object]] = []
    for row in test_first:
        level = row.get("voc_evidence_strength") or "None"
        if level not in {"None", "Weak", "Medium"}:
            level = "None"
        fallbacks.append({
            "assumption": row["assumption"],
            "category": row["category"],
            "existing_evidence_level": level,
            "evidence_summary": (
                f"Fallback level inherited from Step 7 voc_evidence_strength={level}; "
                "no LLM evidence audit was performed."
            ),
        })
    return fallbacks


def _normalize_audits(
    raw_audits: list[EvidenceAudit],
    test_first: list[dict[str, object]],
) -> list[dict[str, object]]:
    """Align LLM audits with the input order, filling gaps from fallbacks."""
    by_assumption = {a.assumption.strip(): a for a in raw_audits}
    aligned: list[dict[str, object]] = []
    fallbacks = _fallback_audits(test_first)
    for row, fb in zip(test_first, fallbacks):
        match = by_assumption.get(row["assumption"].strip())
        if match is None:
            aligned.append(fb)
        else:
            aligned.append({
                "assumption": row["assumption"],
                "category": row["category"],
                "existing_evidence_level": match.existing_evidence_level,
                "evidence_summary": match.evidence_summary,
            })
    return aligned


# ---------------------------------------------------------------------------
# Public entry points
# ---------------------------------------------------------------------------


def run_step8a_llm(
    state: BMIWorkflowState,
    llm: BaseChatModel | None,
) -> BMIWorkflowState:
    """Run the evidence audit. Returns updated state with assumption_evidence_audit."""
    test_first = _extract_test_first(state)

    if not test_first:
        return {
            **state,
            "current_step": "evidence_audit",
            "assumption_evidence_audit": [],
        }

    if llm is None:
        return {
            **state,
            "current_step": "evidence_audit",
            "assumption_evidence_audit": _fallback_audits(test_first),
        }

    messages = _build_messages(state, test_first)
    structured_llm = llm.with_structured_output(EvidenceAuditList)
    try:
        result: EvidenceAuditList = invoke_with_retry(
            structured_llm, messages, step_name="step8a_evidence_audit"
        )
        audits = _normalize_audits(result.audits, test_first)
    except RuntimeError:
        audits = _fallback_audits(test_first)

    return {
        **state,
        "current_step": "evidence_audit",
        "assumption_evidence_audit": audits,
    }
