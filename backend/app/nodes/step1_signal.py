from __future__ import annotations

from backend.app.patterns.loader import PatternLibraryLoader
from backend.app.skills.loader import PromptAssetLoader
from backend.app.state import BMIWorkflowState


def _load_soc_context() -> tuple[set[str], set[str], dict[range, str]]:
    library = PatternLibraryLoader().load_library("soc-radar-pattern-library.json").data
    PromptAssetLoader().load_skill_asset("soc-radar")

    zones = {zone["name"] for zone in library["signal_zones"]["zones"]}
    filters = {item["name"] for item in library["disruption_filters"]["filters"]}
    action_tiers = {
        range(_range_start(item["score_range"]), _range_end(item["score_range"]) + 1): item["tier"]
        for item in library["scoring"]["action_tiers"]
    }
    return zones, filters, action_tiers


def _range_start(score_range: str) -> int:
    start, _ = score_range.split("-", 1)
    return int(start)


def _range_end(score_range: str) -> int:
    _, end = score_range.split("-", 1)
    return int(end)


def _classify_signal(voc_data: str, valid_zones: set[str], valid_filters: set[str]) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    normalized = voc_data.lower()

    if any(keyword in normalized for keyword in ("complex", "friction", "too many steps", "delay onboarding", "manual")):
        zone = "Overserved Customers"
        classification = "Disruptive — Low-End"
        filter_names = ["Performance Overshoot", "Business Model Conflict"]
        impact = 2
        speed = 2
        signal_text = "Customers delay onboarding because the workflow is more complex than they value"
    elif any(keyword in normalized for keyword in ("small teams", "self-serve", "cannot access", "can't access", "without enterprise")):
        zone = "New-Market Foothold"
        classification = "Disruptive — New-Market"
        filter_names = ["Barrier Removal", "Asymmetric Motivation", "Trajectory"]
        impact = 3
        speed = 3
        signal_text = "Nontraditional buyers can now adopt without the enterprise implementation burden"
    else:
        zone = "Business Model Anomaly"
        classification = "Sustaining"
        filter_names = []
        impact = 1
        speed = 2
        signal_text = "An alternative delivery model appears to be changing how customers access value"

    if zone not in valid_zones:
        raise ValueError(f"Unsupported SOC zone: {zone}")
    if any(filter_name not in valid_filters for filter_name in filter_names):
        raise ValueError("Unsupported SOC disruption filter detected")

    detected_signal = {
        "signal": signal_text,
        "source": voc_data,
        "zone": zone,
    }
    interpreted_signal = {
        **detected_signal,
        "classification": classification,
        "filters": filter_names,
    }
    priority_signal = {
        "signal": signal_text,
        "impact": impact,
        "speed": speed,
        "score": impact * speed,
    }
    return detected_signal, interpreted_signal, priority_signal


def _resolve_tier(score: int, action_tiers: dict[range, str]) -> str:
    for score_range, tier in action_tiers.items():
        if score in score_range:
            return tier
    raise ValueError(f"No SOC action tier configured for score {score}")


def run_step(state: BMIWorkflowState) -> BMIWorkflowState:
    voc_data = state.get("voc_data", "")
    valid_zones, valid_filters, action_tiers = _load_soc_context()
    detected_signal, interpreted_signal, priority_signal = _classify_signal(
        voc_data, valid_zones, valid_filters
    )
    priority_signal["tier"] = _resolve_tier(int(priority_signal["score"]), action_tiers)

    return {
        **state,
        "current_step": "signal_scan",
        "signals": [detected_signal],
        "interpreted_signals": [interpreted_signal],
        "priority_matrix": [priority_signal],
    }
