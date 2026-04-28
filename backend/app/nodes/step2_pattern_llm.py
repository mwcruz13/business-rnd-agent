"""Step 2 — Hybrid pattern matcher (deterministic shortlist + LLM reasoning).

Phase 1 (deterministic): the affinity matrix narrows ~21 patterns to 3–4
candidates based on signal zone, classification, and disruption filters.

Phase 2 (LLM): the pattern reasoner selects 1–2 best patterns from the
shortlist using signal evidence and pattern trigger questions.

Fallback: if no LLM is available or the call fails, the full shortlist
is returned so the consultant can decide at the checkpoint.

Design reference: docs/step2-signal-to-pattern-mapping-research.md §5.3/§6.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from backend.app.patterns.loader import PatternLibraryLoader
from backend.app.patterns.pattern_affinity import (
    PatternScore,
    shortlist_patterns,
)
from backend.app.skills.loader import PromptAssetLoader
from backend.app.llm.retry import invoke_with_retry
from backend.app.state import BMIWorkflowState

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Zone normalization (carried over from the original implementation)
# ---------------------------------------------------------------------------

_ZONE_NORMALIZATION: dict[str, str] = {
    "Enabling Tech": "Enabling Technology",
    "Overserved": "Overserved Customers",
    "Regulatory Shift": "Regulatory / Policy Shift",
}

_DISRUPTIVE_CLASSIFICATIONS = {
    "Disruptive — New-Market",
    "Disruptive — Low-End",
    "Disruptive - New-Market",
    "Disruptive - Low-End",
}


def _normalize_zone(zone: str) -> str:
    return _ZONE_NORMALIZATION.get(zone, zone)


# ---------------------------------------------------------------------------
# Signal selection — reused from original
# ---------------------------------------------------------------------------

def _find_best_disruptive_signal(
    interpreted_signals: list[dict],
    priority_matrix: list[dict],
) -> tuple[dict, dict]:
    """Find the highest-priority disruptive signal.

    Returns the best (interpreted_signal, priority_entry) pair.  Falls back
    to the first signal if no disruptive signal exists.
    """
    priority_by_id = {p.get("signal_id"): p for p in priority_matrix}

    best_signal: dict | None = None
    best_priority: dict | None = None
    best_score = -1

    for signal in interpreted_signals:
        classification = str(signal.get("classification", ""))
        if classification not in _DISRUPTIVE_CLASSIFICATIONS:
            continue
        signal_id = signal.get("signal_id")
        priority = priority_by_id.get(signal_id, {})
        score = priority.get("score", 0)
        if score > best_score:
            best_signal = signal
            best_priority = priority
            best_score = score

    if best_signal is None:
        best_signal = interpreted_signals[0] if interpreted_signals else {}
        best_priority = priority_matrix[0] if priority_matrix else {}

    return best_signal, best_priority


# ---------------------------------------------------------------------------
# Pattern library helpers
# ---------------------------------------------------------------------------

def _load_pattern_library() -> dict[str, Any]:
    """Load the full Strategyzer pattern library data."""
    return PatternLibraryLoader().load_library(
        "strategyzer-pattern-library.json"
    ).data


def _get_verified_names(library_data: dict[str, Any]) -> set[str]:
    """Return the set of verified INVENT + SHIFT pattern names."""
    names: set[str] = set()
    for section in ("invent", "shift"):
        for pattern in library_data.get(section, {}).get("patterns", []):
            if pattern.get("status") == "verified":
                names.add(pattern["name"])
    return names


def _get_pattern_context(
    library_data: dict[str, Any],
    shortlist: list[PatternScore],
) -> str:
    """Build a context string with descriptions + trigger questions for the
    shortlisted patterns, to include in the LLM prompt."""
    # Build lookup: name → pattern dict
    lookup: dict[str, dict] = {}
    for section in ("invent", "shift"):
        for p in library_data.get(section, {}).get("patterns", []):
            lookup[p["name"]] = p

    lines: list[str] = []
    for ps in shortlist:
        info = lookup.get(ps.name, {})
        desc = info.get("description", "No description available.")
        trigger = info.get("trigger_question") or info.get("strategic_reflection", "")
        library_label = ps.library.upper()
        lines.append(
            f"- **{ps.name}** ({library_label}): {desc}\n"
            f"  Trigger question: {trigger}"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Phase 1: Deterministic shortlist
# ---------------------------------------------------------------------------

def _run_phase1(
    signal: dict, priority: dict
) -> tuple[str, list[PatternScore], str, str, list[str]]:
    """Run the deterministic affinity shortlister.

    Returns (direction, shortlist, zone, classification, filters).
    """
    zone = _normalize_zone(str(signal.get("zone", "")))
    classification = str(signal.get("classification", ""))
    filters = signal.get("filters") or []
    score = priority.get("score")

    direction, shortlist = shortlist_patterns(
        zone=zone,
        classification=classification,
        filters=filters,
    )
    return direction, shortlist, zone, classification, filters


# ---------------------------------------------------------------------------
# Phase 2: LLM pattern reasoner
# ---------------------------------------------------------------------------

class PatternReasonerOutput(BaseModel):
    """Structured output schema for the LLM pattern reasoner."""
    selected_patterns: list[str] = Field(
        description="1–2 pattern names selected from the shortlist"
    )
    rationale: str = Field(
        description="Explanation connecting signal evidence to the selected patterns"
    )
    evidence_used: str = Field(
        description="Key signal fields that drove the decision"
    )
    confidence: str = Field(description="high, medium, or low")
    notes: str = Field(default="", description="Caveats or suggestions for the consultant")


def _build_phase2_messages(
    signal: dict,
    priority: dict,
    direction: str,
    shortlist: list[PatternScore],
    pattern_context: str,
) -> list[SystemMessage | HumanMessage]:
    """Build the prompt messages for the LLM pattern reasoner."""
    prompt_asset = PromptAssetLoader().load_step_prompt("step2_pattern_matcher")

    system_prompt = prompt_asset.body

    zone = signal.get("zone", "")
    classification = signal.get("classification", "")
    raw_filters = signal.get("filters", [])
    signal_desc = signal.get("signal", "")
    observable = signal.get("observable_behavior", "")
    score = priority.get("score", "")
    tier = priority.get("tier", "")

    # Normalize filters: support both list[str] (legacy) and list[dict] (new schema)
    filter_labels = [
        f["filter_name"] if isinstance(f, dict) else str(f)
        for f in raw_filters
    ]

    user_prompt = (
        f"## Signal Details\n"
        f"- Zone: {zone}\n"
        f"- Classification: {classification}\n"
        f"- Description: {signal_desc}\n"
        f"- Observable behavior: {observable}\n"
        f"- Disruption filters: {', '.join(filter_labels) if filter_labels else 'none'}\n"
        f"- Priority score: {score} (tier: {tier})\n\n"
        f"## Direction: {direction}\n\n"
        f"## Candidate Patterns (select 1–2)\n\n"
        f"{pattern_context}\n"
    )

    return [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]


def _run_phase2(
    signal: dict,
    priority: dict,
    direction: str,
    shortlist: list[PatternScore],
    pattern_context: str,
    llm: BaseChatModel,
    verified_names: set[str],
) -> PatternReasonerOutput | None:
    """Run the LLM pattern reasoner.  Returns None on failure."""
    try:
        messages = _build_phase2_messages(
            signal, priority, direction, shortlist, pattern_context,
        )
        structured_llm = llm.with_structured_output(PatternReasonerOutput)
        result: PatternReasonerOutput = invoke_with_retry(structured_llm, messages, step_name="step2_pattern_reasoner")

        # Validate that selected patterns are from the shortlist
        shortlist_names = {ps.name for ps in shortlist}
        valid = [p for p in result.selected_patterns if p in shortlist_names]
        if not valid:
            logger.warning(
                "LLM returned patterns not in shortlist: %s — falling back",
                result.selected_patterns,
            )
            return None
        result.selected_patterns = valid
        return result
    except Exception:
        logger.exception("Phase 2 LLM pattern reasoner failed — using shortlist fallback")
        return None


# ---------------------------------------------------------------------------
# Recommendation formatting
# ---------------------------------------------------------------------------

def _format_recommendation(
    direction: str,
    selected_patterns: list[str],
    zone: str,
    classification: str,
    score: Any,
    rationale: str,
    confidence: str,
    notes: str,
) -> str:
    """Build a human-readable recommendation string."""
    direction_label = direction.upper()
    patterns_str = ", ".join(selected_patterns) if selected_patterns else "see shortlist"
    return (
        f"Explore {direction_label} first.\n"
        f"Recommended patterns: {patterns_str}\n"
        f"Rationale: {rationale}\n"
        f"Evidence used: zone={zone}; classification={classification}; score={score}.\n"
        f"Confidence: {confidence}\n"
        f"Notes: {notes}"
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_step2_llm(
    state: BMIWorkflowState,
    llm: BaseChatModel | None = None,
) -> BMIWorkflowState:
    """Run the hybrid Step 2 pattern matcher.

    Phase 1 (always): deterministic affinity shortlist.
    Phase 2 (if LLM provided): LLM selects 1–2 from shortlist.
    Fallback: top patterns from Phase 1 shortlist.
    """
    interpreted_signals = state.get("interpreted_signals") or []
    priority_matrix = state.get("priority_matrix") or []

    signal, priority = _find_best_disruptive_signal(interpreted_signals, priority_matrix)

    # Phase 1: deterministic shortlist
    direction, shortlist, zone, classification, filters = _run_phase1(signal, priority)

    # Load library for context and validation
    library_data = _load_pattern_library()
    verified_names = _get_verified_names(library_data)

    score = priority.get("score")
    selected_patterns: list[str] = []
    rationale: str
    confidence: str
    notes: str

    if llm is not None and shortlist:
        # Phase 2: LLM pattern reasoner
        pattern_context = _get_pattern_context(library_data, shortlist)
        result = _run_phase2(
            signal, priority, direction, shortlist,
            pattern_context, llm, verified_names,
        )
        if result is not None:
            selected_patterns = result.selected_patterns
            rationale = result.rationale
            confidence = result.confidence
            notes = result.notes
        else:
            # Phase 2 failed — use Phase 1 shortlist as fallback
            selected_patterns = [ps.name for ps in shortlist[:2]]
            rationale = (
                f"{zone} with {classification} — "
                "selected by affinity matrix (LLM reasoner unavailable)."
            )
            confidence = "medium"
            notes = "Fallback: LLM pattern reasoner failed. Top shortlisted patterns returned."
    elif shortlist:
        # No LLM — use Phase 1 shortlist directly
        selected_patterns = [ps.name for ps in shortlist[:2]]
        rationale = (
            f"{zone} with {classification} indicates "
            "an opportunity aligned with the shortlisted patterns."
        )
        confidence = "medium"
        notes = "Deterministic shortlist only — no LLM reasoning applied."
    else:
        # No shortlist (unknown zone, empty signals)
        selected_patterns = []
        rationale = (
            f"{zone} with {classification} — "
            "no patterns matched in the affinity matrix."
        )
        confidence = "low"
        notes = "The consultant should manually select patterns at the checkpoint."

    recommendation = _format_recommendation(
        direction, selected_patterns, zone, classification,
        score, rationale, confidence, notes,
    )

    result_state: dict = {
        **state,
        "current_step": "pattern_select",
        "agent_recommendation": recommendation,
        "pattern_direction": direction,
        "pattern_rationale": recommendation,
    }
    if selected_patterns:
        result_state["selected_patterns"] = selected_patterns
    return result_state
