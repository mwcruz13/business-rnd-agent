from __future__ import annotations

from backend.app.skills.loader import PromptAssetLoader
from backend.app.state import BMIWorkflowState


def _build_value_driver_tree(state: BMIWorkflowState) -> str:
    selected_patterns = ", ".join(state.get("selected_patterns", [])) or "approved patterns"
    customer_profile = state.get("customer_profile", "")
    PromptAssetLoader().load_skill_asset("cxif-bmi-coach")

    if "onboarding" in customer_profile.lower():
        outcome = "Reduce onboarding time-to-value while increasing buyer confidence during activation."
        deliverable = "Simplified onboarding path"
        measure = "Days from signature to first successful value realization"
        baseline = "14 days"
        target = "5 days"
    else:
        outcome = "Improve the customer's ability to achieve the desired outcome with less effort and delay."
        deliverable = "Lower-friction adoption path"
        measure = "Time from initial setup to successful usage"
        baseline = "TBD"
        target = "TBD"

    return "\n".join(
        [
            "## Value Driver Tree",
            "",
            "### Customer Business Outcome",
            f"{outcome} The direction is being explored through {selected_patterns}.",
            "",
            "### Key Deliverables and Success Measures",
            "| Key Deliverable | Success Measure | Baseline | Target | Driver Type |",
            "|----------------|----------------|----------|--------|-------------|",
            f"| {deliverable} | {measure} | {baseline} | {target} | Time |",
            "| Reduced customer rework | Number of setup corrections per onboarding cycle | 4 | 1 | Effort |",
            "| Stronger early confidence | Activation satisfaction score in the first 30 days | 6/10 | 8/10 | Satisfaction |",
        ]
    )


def _build_actionable_insights(state: BMIWorkflowState) -> str:
    selected_patterns = ", ".join(state.get("selected_patterns", [])) or "approved patterns"
    customer_profile = state.get("customer_profile", "")
    if "onboarding" in customer_profile.lower():
        customer_segment = "Operational buyers"
        job = "accelerate onboarding without specialist dependency"
        gain = "they need fast time-to-value and visible progress"
        pain = "today's setup path is complex and creates delays"
    else:
        customer_segment = "Target customers"
        job = "reach the desired outcome with less effort"
        gain = "they want a more convenient and predictable path"
        pain = "the current experience still creates friction"

    return "\n".join(
        [
            "## Context Analysis",
            "",
            "### Value Chain Assessment",
            "| Activity | Role in Value Creation | Weak Link? | Impact on Customer |",
            "|----------|----------------------|------------|-------------------|",
            f"| Onboarding setup | Converts initial demand into realized value | Yes | Delays adoption when the {selected_patterns} direction is not yet reflected in the experience |",
            "",
            "### Customer Journey Friction Points",
            "| Journey Phase | Touchpoint | Customer Experience | Friction Type | Opportunity |",
            "|---------------|-----------|-------------------|---------------|-------------|",
            "| Onboarding Support | Initial configuration and handoff | Customers wait for guidance to complete setup | Delay | Replace high-friction setup steps with a simpler guided path |",
            "",
            "### Actionable Insights",
            f"**{customer_segment}** DOES **{job}** BECAUSE **{gain}** BUT **{pain}**",
            "",
            "### Problem Statements",
            "| # | Problem Statement | Jobs Affected | Pains Addressed | Priority |",
            "|---|------------------|--------------|-----------------|----------|",
            "| 1 | Customers cannot realize value quickly because onboarding still assumes more process complexity than they need. | Accelerate onboarding | Setup friction and delay | High |",
        ]
    )


def run_step(state: BMIWorkflowState) -> BMIWorkflowState:
    return {
        **state,
        "current_step": "measure_define",
        "value_driver_tree": _build_value_driver_tree(state),
        "actionable_insights": _build_actionable_insights(state),
    }
