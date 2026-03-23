from __future__ import annotations

from backend.app.skills.loader import PromptAssetLoader
from backend.app.state import BMIWorkflowState


def _build_value_proposition_canvas(state: BMIWorkflowState) -> str:
    selected_patterns = ", ".join(state.get("selected_patterns", [])) or "approved patterns"
    customer_profile = state.get("customer_profile", "")
    actionable_insights = state.get("actionable_insights", "")
    PromptAssetLoader().load_skill_asset("cxif-bmi-coach")

    if "onboarding" in customer_profile.lower():
        product_service = f"A guided onboarding experience shaped by {selected_patterns}"
        pain_addressed = "The current setup flow is too complex and slows time-to-value"
        gain_addressed = f"A faster activation path aligned to {selected_patterns}"
        customer_segment = "operational buyers"
        job = "complete onboarding quickly without expert intervention"
        pain = "reducing setup friction and delay"
        gain = "improving early confidence and time-to-value"
    else:
        product_service = f"A lower-friction value delivery path shaped by {selected_patterns}"
        pain_addressed = "Customers still encounter unnecessary effort in the current experience"
        gain_addressed = "A more convenient path to the desired outcome"
        customer_segment = "target customers"
        job = "achieve the desired outcome with less effort"
        pain = "reducing avoidable friction"
        gain = "improving convenience and predictability"

    return "\n".join(
        [
            "## Value Proposition Canvas",
            "",
            "### Value Map",
            "",
            "#### Products & Services",
            "| Type | Product/Service | Relevance |",
            "|------|----------------|-----------|",
            f"| Digital | {product_service} | Core |",
            "| Intangible | Clear activation guidance and confidence-building support | Core |",
            "| Financial | Lower onboarding effort and reduced delivery overhead | Nice-to-have |",
            "",
            "#### Pain Relievers",
            "| Type | Pain Reliever | Pain Addressed | Relevance |",
            "|------|--------------|----------------|-----------|",
            f"| Functional | Streamline the first-run setup into fewer guided steps | {pain_addressed} | Substantial |",
            "| Social | Provide visible progress markers for stakeholders during activation | Delays make the buying team look unprepared in front of stakeholders | Substantial |",
            "| Emotional | Reduce dependence on specialist intervention during setup | Customers feel uncertainty when progress depends on specialist support | Substantial |",
            "",
            "#### Gain Creators",
            "| Type | Gain Creator | Gain Addressed | Relevance |",
            "|------|-------------|----------------|-----------|",
            f"| Functional | Deliver a faster activation path with fewer handoffs | {gain_addressed} | Substantial |",
            "| Social | Help the team demonstrate visible onboarding momentum early | Visible proof that the new model reduces friction for the wider team | Substantial |",
            "| Emotional | Give customers a predictable path to first value without escalation | Confidence that onboarding can be completed without escalation | Substantial |",
            "| Financial | Lower rework and support effort in the activation phase | Less time and overhead spent on setup | Nice-to-have |",
            "",
            "### Ad-Lib Prototype",
            f"> **OUR** {product_service} **HELP** {customer_segment} **WHO WANT TO** {job} **BY** {pain} **AND** {gain}",
            f"> **OUR** activation support model using {selected_patterns} **HELP** {customer_segment} **WHO WANT TO** {job} **BY** {pain} **AND** creating a faster path to first value",
            f"Context anchor: {selected_patterns}. Insight source: {actionable_insights.splitlines()[-1] if actionable_insights else 'No actionable insight summary available.'}",
        ]
    )


def run_step(state: BMIWorkflowState) -> BMIWorkflowState:
    return {
        **state,
        "current_step": "value_proposition",
        "value_proposition_canvas": _build_value_proposition_canvas(state),
    }
