from __future__ import annotations

from backend.app.skills.loader import PromptAssetLoader
from backend.app.state import BMIWorkflowState


def _derive_customer_segment(voc_data: str, selected_patterns: list[str]) -> str:
    if "onboarding" in voc_data.lower():
        segment = "Operational buyers navigating onboarding and early activation"
    else:
        segment = "Customers evaluating a lower-friction path to the desired outcome"
    pattern_context = ", ".join(selected_patterns) or "approved patterns"
    return f"{segment}. Opportunity framing is informed by {pattern_context}."


def _build_customer_profile(state: BMIWorkflowState) -> str:
    voc_data = state.get("voc_data", "")
    selected_patterns = state.get("selected_patterns", [])
    pattern_context = ", ".join(selected_patterns) or "approved patterns"
    signal_context = state.get("interpreted_signals", [])
    primary_zone = signal_context[0].get("zone", "identified opportunity") if signal_context else "identified opportunity"
    PromptAssetLoader().load_skill_asset("cxif-bmi-coach")

    customer_segment = _derive_customer_segment(voc_data, selected_patterns)
    return "\n".join(
        [
            "## Customer Empathy Profile",
            "",
            "### Customer Segment",
            customer_segment,
            f"Source context: {primary_zone}. Consultant-approved pattern context: {pattern_context}.",
            "",
            "### Customer Jobs",
            "| Type | Job | Importance |",
            "|------|-----|------------|",
            "| Functional | Complete onboarding quickly without expert intervention | High |",
            "| Social | Demonstrate to peers that adoption is under control | Medium |",
            "| Emotional | Feel confident that the solution will work without rework | High |",
            "| Supporting | Coordinate internal approvals and setup handoffs with less effort | Medium |",
            "",
            "### Customer Pains",
            "| Type | Pain | Severity |",
            "|------|------|----------|",
            "| Functional | The current setup flow is too complex and slows time-to-value | Severe |",
            "| Social | Delays make the buying team look unprepared in front of stakeholders | Moderate |",
            "| Emotional | Customers feel uncertainty when progress depends on specialist support | Severe |",
            "| Ancillary | Repeated follow-up and documentation review adds coordination overhead | Moderate |",
            "",
            "### Customer Gains",
            "| Type | Gain | Relevance |",
            "|------|------|-----------|",
            f"| Functional | A faster activation path aligned to {pattern_context} | Essential |",
            "| Social | Visible proof that the new model reduces friction for the wider team | Desired |",
            "| Emotional | Confidence that onboarding can be completed without escalation | Essential |",
            "| Financial | Less time spent on setup and handoffs lowers adoption cost | Expected |",
        ]
    )


def run_step(state: BMIWorkflowState) -> BMIWorkflowState:
    customer_profile = _build_customer_profile(state)

    return {
        **state,
        "current_step": "empathize",
        "customer_profile": customer_profile,
    }
