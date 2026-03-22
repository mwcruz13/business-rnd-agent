from __future__ import annotations

from backend.app.patterns.loader import PatternLibraryLoader
from backend.app.skills.loader import PromptAssetLoader
from backend.app.state import BMIWorkflowState


def _load_strategyzer_context() -> set[str]:
    library = PatternLibraryLoader().load_library("strategyzer-pattern-library.json").data
    PromptAssetLoader().load_step_prompt("step2_pattern_matcher")
    return {
        pattern["name"]
        for pattern in library["invent"]["patterns"]
        if pattern.get("status") == "verified"
    }


def _recommend_direction(state: BMIWorkflowState, verified_invent_patterns: set[str]) -> str:
    interpreted_signals = state.get("interpreted_signals") or []
    priority_matrix = state.get("priority_matrix") or []
    first_signal = interpreted_signals[0] if interpreted_signals else {}
    first_priority = priority_matrix[0] if priority_matrix else {}
    zone = str(first_signal.get("zone", ""))
    classification = str(first_signal.get("classification", ""))
    score = first_priority.get("score")

    if classification == "Disruptive — New-Market" or zone in {
        "New-Market Foothold",
        "Nonconsumption",
        "Regulatory / Policy Shift",
        "Business Model Anomaly",
    }:
        pattern_name = "Market Explorers"
        if pattern_name not in verified_invent_patterns:
            raise ValueError("Expected Strategyzer INVENT pattern is not available")
        return (
            "Explore INVENT first.\n"
            f"Recommended patterns: {pattern_name}\n"
            f"Rationale: {zone} with {classification} indicates an opportunity to create demand where incumbents are not optimized to respond.\n"
            f"Evidence used: zone={zone}; classification={classification}; score={score}.\n"
            "Confidence: medium\n"
            "Notes: recommendation generated from the packaged Step 2 prompt and verified Strategyzer INVENT library."
        )

    return (
        "Explore SHIFT first.\n"
        "Recommended patterns: pending_library_source\n"
        f"Rationale: {zone} with {classification} points to an incumbent transformation path, but SHIFT pattern names are not yet populated in the packaged library.\n"
        f"Evidence used: zone={zone}; classification={classification}; score={score}.\n"
        "Confidence: medium\n"
        "Notes: do not set pattern_direction or selected_patterns until the consultant checkpoint approves a direction."
    )


def run_step(state: BMIWorkflowState) -> BMIWorkflowState:
    verified_invent_patterns = _load_strategyzer_context()
    recommendation = _recommend_direction(state, verified_invent_patterns)

    return {
        **state,
        "current_step": "pattern_select",
        "agent_recommendation": recommendation,
    }
