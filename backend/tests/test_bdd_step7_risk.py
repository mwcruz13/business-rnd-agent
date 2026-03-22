from pytest_bdd import given, scenarios, then, when

from backend.app.nodes.step7_risk import run_step
from backend.app.state import BMIWorkflowState


scenarios("features/step7-risk.feature")


@given("a workflow state with completed Step 6 design outputs", target_fixture="workflow_state")
def workflow_state() -> BMIWorkflowState:
    return {
        "session_id": "session-007",
        "current_step": "design_fit",
        "input_type": "text",
        "llm_backend": "azure",
        "pattern_direction": "shift",
        "selected_patterns": ["Cost Differentiators"],
        "business_model_canvas": "\n".join(
            [
                "## Business Model Canvas",
                "",
                "### Desirability",
                "| Building Block | Description |",
                "|---------------|-------------|",
                "| Customer Segments | Operational buyers and adoption stakeholders seeking faster activation through Cost Differentiators. |",
                "| Value Proposition | A lower-friction onboarding path that reduces setup complexity and accelerates time-to-value. Pattern context: Cost Differentiators. |",
                "| Channels | Direct sales handoff, guided digital onboarding, and in-product activation support. |",
                "| Customer Relationships | Self-service guidance with targeted human support for exceptions. |",
                "",
                "### Feasibility",
                "| Building Block | Description |",
                "|---------------|-------------|",
                "| Key Partnerships | Product, onboarding operations, and support teams aligned around a simplified activation path. |",
                "| Key Activities | Design guided setup flows, monitor activation progress, and intervene on edge cases. |",
                "| Key Resources | Onboarding playbooks, product telemetry, and customer-success expertise. |",
                "",
                "### Viability",
                "| Building Block | Description |",
                "|---------------|-------------|",
                "| Revenue Streams | Existing product revenue protected by faster activation and stronger adoption expansion. |",
                "| Cost Structure | Investment in productized onboarding flows, targeted support, and telemetry instrumentation. |",
            ]
        ),
        "fit_assessment": "\n".join(
            [
                "## Fit Assessment",
                "",
                "### Problem-Solution Fit",
                "| Customer Need (Job/Pain/Gain) | Importance to Customer | Mapped Value Proposition Element | Fit? |",
                "|------------------------------|----------------------|--------------------------------|------|",
                "| Complete onboarding quickly | High | Guided onboarding experience and streamlined setup steps | Strong |",
                "",
                "### Product-Market Fit Status",
                "| Criterion | Status | Evidence |",
                "|-----------|--------|----------|",
                "| Customers care about these jobs, pains, gains | Assumed | Prior workflow outputs point to onboarding friction and demand for faster activation. |",
                "| Value proposition creates real value for customers | Assumed | Prior workflow outputs point to onboarding friction and demand for faster activation. |",
                "| Market interest demonstrated | Unknown | No external validation has been run yet. |",
                "",
                "### Business Model Fit Status",
                "| Dimension | Status | Evidence |",
                "|-----------|--------|----------|",
                "| Desirable — creates value for customers and business | Assumed | Reduced onboarding friction is consistently supported. |",
                "| Feasible — the business model should work | Assumed | The model relies on productized onboarding and targeted support. |",
                "| Viable — will generate more revenue than costs | Unknown | Revenue preservation and cost reduction are not yet measured. |",
            ]
        ),
    }


@when("the Step 7 risk mapper node runs", target_fixture="step7_result")
def step7_result(workflow_state: BMIWorkflowState) -> BMIWorkflowState:
    return run_step(workflow_state)


@then('the workflow current step is "risk_map"')
def assert_current_step(step7_result: BMIWorkflowState) -> None:
    assert step7_result["current_step"] == "risk_map"


@then("the business model canvas is preserved in the workflow state")
def assert_bmc_preserved(workflow_state: BMIWorkflowState, step7_result: BMIWorkflowState) -> None:
    assert step7_result["business_model_canvas"] == workflow_state["business_model_canvas"]


@then("the workflow state contains assumptions")
def assert_assumptions(step7_result: BMIWorkflowState) -> None:
    assert isinstance(step7_result.get("assumptions"), str)
    assert step7_result["assumptions"]


@then("the assumptions use the Precoil EMT headings")
def assert_precoil_headings(step7_result: BMIWorkflowState) -> None:
    assumptions = step7_result["assumptions"]
    assert "## Desirability" in assumptions
    assert "## Viability" in assumptions
    assert "## Feasibility" in assumptions


@then("the assumptions include 9 formatted assumptions")
def assert_assumption_count(step7_result: BMIWorkflowState) -> None:
    assumptions = step7_result["assumptions"]
    formatted_rows = assumptions.count("| Desirable | I believe")
    formatted_rows += assumptions.count("| Viable | I believe")
    formatted_rows += assumptions.count("| Feasible | I believe")
    assert formatted_rows == 9


@then("the assumptions include all DVF categories")
def assert_dvf_categories(step7_result: BMIWorkflowState) -> None:
    assumptions = step7_result["assumptions"]
    assert "| Desirable |" in assumptions
    assert "| Viable |" in assumptions
    assert "| Feasible |" in assumptions


@then("the assumptions include a DVF tension check")
def assert_dvf_tensions(step7_result: BMIWorkflowState) -> None:
    assert "## DVF Tensions" in step7_result["assumptions"]


@then("the assumptions include an importance evidence matrix")
def assert_importance_evidence_matrix(step7_result: BMIWorkflowState) -> None:
    assumptions = step7_result["assumptions"]
    assert "## Importance × Evidence Map" in assumptions
    assert "| Assumption | Category | Quadrant |" in assumptions


@then("the assumptions identify at least one test-first risk")
def assert_test_first(step7_result: BMIWorkflowState) -> None:
    assert "Test first" in step7_result["assumptions"]