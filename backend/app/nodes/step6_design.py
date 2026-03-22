from __future__ import annotations

from backend.app.skills.loader import PromptAssetLoader
from backend.app.state import BMIWorkflowState


def _build_business_model_canvas(state: BMIWorkflowState) -> str:
    selected_patterns = ", ".join(state.get("selected_patterns", [])) or "approved patterns"
    value_proposition_canvas = state.get("value_proposition_canvas", "")
    PromptAssetLoader().load_skill_asset("cxif-bmi-coach")

    if "guided onboarding experience" in value_proposition_canvas.lower():
        customer_segments = "Operational buyers and adoption stakeholders seeking faster activation through Cost Differentiators."
        value_proposition = "A lower-friction onboarding path that reduces setup complexity and accelerates time-to-value."
        channels = "Direct sales handoff, guided digital onboarding, and in-product activation support."
        customer_relationships = "Self-service guidance with targeted human support for exceptions."
        key_partnerships = "Product, onboarding operations, and support teams aligned around a simplified activation path."
        key_activities = "Design guided setup flows, monitor activation progress, and intervene on edge cases."
        key_resources = "Onboarding playbooks, product telemetry, and customer-success expertise."
        revenue_streams = "Existing product revenue protected by faster activation and stronger adoption expansion."
        cost_structure = "Investment in productized onboarding flows, targeted support, and telemetry instrumentation."
    else:
        customer_segments = "Customers seeking a lower-friction way to achieve the desired outcome."
        value_proposition = "A simpler, more predictable path to value."
        channels = "Digital onboarding and customer support."
        customer_relationships = "Guided self-service."
        key_partnerships = "Product and support operations."
        key_activities = "Deliver and refine the simplified experience."
        key_resources = "Product workflows and support knowledge."
        revenue_streams = "Protected subscription and expansion revenue."
        cost_structure = "Operational simplification and enablement costs."

    return "\n".join(
        [
            "## Business Model Canvas",
            "",
            "### Desirability",
            "| Building Block | Description |",
            "|---------------|-------------|",
            f"| Customer Segments | {customer_segments} |",
            f"| Value Proposition | {value_proposition} Pattern context: {selected_patterns}. |",
            f"| Channels | {channels} |",
            f"| Customer Relationships | {customer_relationships} |",
            "",
            "### Feasibility",
            "| Building Block | Description |",
            "|---------------|-------------|",
            f"| Key Partnerships | {key_partnerships} |",
            f"| Key Activities | {key_activities} |",
            f"| Key Resources | {key_resources} |",
            "",
            "### Viability",
            "| Building Block | Description |",
            "|---------------|-------------|",
            f"| Revenue Streams | {revenue_streams} |",
            f"| Cost Structure | {cost_structure} |",
        ]
    )


def _build_fit_assessment(state: BMIWorkflowState) -> str:
    value_proposition_canvas = state.get("value_proposition_canvas", "")

    if "guided onboarding experience" in value_proposition_canvas.lower():
        mapped_element = "Guided onboarding experience and streamlined setup steps"
        evidence = "Step 3 and Step 4 outputs consistently point to onboarding friction, delay, and demand for faster activation."
    else:
        mapped_element = "Simplified value delivery path"
        evidence = "Prior workflow outputs suggest convenience and predictability are important but not yet deeply validated."

    return "\n".join(
        [
            "## Fit Assessment",
            "",
            "### Problem-Solution Fit",
            "| Customer Need (Job/Pain/Gain) | Importance to Customer | Mapped Value Proposition Element | Fit? |",
            "|------------------------------|----------------------|--------------------------------|------|",
            f"| Complete onboarding quickly | High | {mapped_element} | Strong |",
            "| Reduce setup friction | High | Guided setup path and visible progress markers | Strong |",
            "| Gain early confidence | High | Predictable activation support model | Partial |",
            "",
            "### Product-Market Fit Status",
            "| Criterion | Status | Evidence |",
            "|-----------|--------|----------|",
            f"| Customers care about these jobs, pains, gains | Assumed | {evidence} |",
            f"| Value proposition creates real value for customers | Assumed | {evidence} |",
            "| Market interest demonstrated | Unknown | No direct external market validation has been run yet in the workflow. |",
            "",
            "### Business Model Fit Status",
            "| Dimension | Status | Evidence |",
            "|-----------|--------|----------|",
            "| Desirable — creates value for customers and business | Assumed | The prior empathy and problem-framing outputs align on reduced onboarding friction. |",
            "| Feasible — the business model should work | Assumed | The model relies on productized onboarding and targeted support rather than a new operating core. |",
            "| Viable — will generate more revenue than costs | Unknown | Revenue preservation and support-cost reduction are plausible but not yet measured. |",
        ]
    )


def run_step(state: BMIWorkflowState) -> BMIWorkflowState:
    return {
        **state,
        "current_step": "design_fit",
        "business_model_canvas": _build_business_model_canvas(state),
        "fit_assessment": _build_fit_assessment(state),
    }
