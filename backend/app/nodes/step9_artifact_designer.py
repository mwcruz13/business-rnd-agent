"""Step 9 — Artifact Designer.

Translate selected experiment cards into concrete build-ready artifacts.
This step preserves backward compatibility by leaving current_step as pdsa_plan.
"""
from __future__ import annotations

from backend.app.state import BMIWorkflowState


DEFAULT_ARTIFACT_TYPE = "Document Package"


ARTIFACT_TYPES = {
    "Problem Interviews": "Interview Kit",
    "Solution Interviews": "Interview Kit",
    "Landing Page": "Web Page + Analytics",
    "Fake Door": "In-Product Flow",
    "A/B Testing": "Experiment Configuration",
    "Throwaway Prototype": "Interactive Prototype",
    "Usability Testing": "Research Test Kit",
    "Wizard of Oz": "Service Runbook",
    "Mock Sale": "Sales Enablement Kit",
    "Pre-Order Test": "Checkout Flow",
    "Letter of Intent": "Commercial Commitment Pack",
    "Price Testing": "Pricing Script + Survey",
}


def _artifact_type(card_name: str) -> str:
    return ARTIFACT_TYPES.get(card_name, DEFAULT_ARTIFACT_TYPE)


def _default_checklist(card_name: str) -> list[str]:
    if card_name == "Problem Interviews":
        return [
            "Interview screener with inclusion/exclusion criteria",
            "10-question script covering trigger, impact, alternatives, urgency",
            "Evidence capture sheet for quotes, observed behavior, and surprises",
        ]
    if card_name == "Landing Page":
        return [
            "Single value proposition headline and supporting proof points",
            "One primary CTA with conversion event tracking",
            "Traffic source tags and daily conversion dashboard",
        ]
    if card_name == "Throwaway Prototype":
        return [
            "Prototype flow for the 3-5 critical user tasks",
            "Failure-state branch behavior documented",
            "Observer template for time-to-complete and intervention count",
        ]
    if card_name == "Wizard of Oz":
        return [
            "Backstage operator script and handoff checklist",
            "User-facing script that mimics final experience",
            "Escalation rules for edge cases and quality failures",
        ]
    return [
        "Primary artifact ready for pilot execution",
        "Instrumentation to capture behavior and decision evidence",
        "Review checklist to validate evidence quality before decision",
    ]


def _build_artifact_design(card: dict[str, object]) -> dict[str, object]:
    card_name = str(card.get("card_name", "")).strip()
    assumption = str(card.get("assumption", "")).strip()
    artifact_name = str(card.get("asset_needed") or f"{card_name} Evidence Package").strip()
    artifact_type = _artifact_type(card_name)
    objective = (
        f"Create a production-ready artifact package for {card_name} "
        f"to test this assumption: {assumption}"
    )

    return {
        "card_id": card.get("id"),
        "card_name": card_name,
        "assumption": assumption,
        "artifact_name": artifact_name,
        "artifact_type": artifact_type,
        "artifact_objective": objective,
        "artifact_scope": card.get("asset_spec"),
        "deliverable_checklist": _default_checklist(card_name),
        "acceptance_criteria": card.get("asset_acceptance_criteria"),
    }


def run_step(state: BMIWorkflowState) -> BMIWorkflowState:
    """Run Step 9. Uses LLM when available, deterministic fallback otherwise."""
    from backend.app.config import get_settings
    from backend.app.llm.factory import get_chat_model
    from backend.app.nodes.step9_artifact_designer_llm import run_step9_llm

    backend = state.get("llm_backend")
    llm = get_chat_model(get_settings(), backend) if backend else None
    return run_step9_llm(state, llm)
