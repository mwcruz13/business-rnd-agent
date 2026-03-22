from pytest_bdd import given, scenarios, then, when

from backend.app.nodes.step6_design import run_step
from backend.app.state import BMIWorkflowState


scenarios("features/step6-design.feature")


@given("a workflow state with a completed Step 5 value proposition canvas", target_fixture="workflow_state")
def workflow_state() -> BMIWorkflowState:
    return {
        "session_id": "session-006",
        "current_step": "value_proposition",
        "input_type": "text",
        "llm_backend": "azure",
        "pattern_direction": "shift",
        "selected_patterns": ["Cost Differentiators"],
        "customer_profile": "Customer profile placeholder for Step 6 context",
        "actionable_insights": "Problem framing placeholder for Step 6 context",
        "value_proposition_canvas": "\n".join(
            [
                "## Value Proposition Canvas",
                "",
                "### Value Map",
                "",
                "#### Products & Services",
                "| Type | Product/Service | Relevance |",
                "|------|----------------|-----------|",
                "| Digital | A guided onboarding experience shaped by Cost Differentiators | Core |",
                "",
                "#### Pain Relievers",
                "| Type | Pain Reliever | Pain Addressed | Relevance |",
                "|------|--------------|----------------|-----------|",
                "| Functional | Streamline the first-run setup into fewer guided steps | The current setup flow is too complex and slows time-to-value | Substantial |",
                "",
                "#### Gain Creators",
                "| Type | Gain Creator | Gain Addressed | Relevance |",
                "|------|-------------|----------------|-----------|",
                "| Functional | Deliver a faster activation path with fewer handoffs | A faster activation path aligned to Cost Differentiators | Substantial |",
                "",
                "### Ad-Lib Prototype",
                "> **OUR** guided onboarding experience **HELP** operational buyers **WHO WANT TO** complete onboarding quickly **BY** reducing setup friction **AND** improving early confidence",
                "> **OUR** activation support model using Cost Differentiators **HELP** operational buyers **WHO WANT TO** complete onboarding quickly **BY** reducing setup friction **AND** creating a faster path to first value",
            ]
        ),
    }


@when("the Step 6 design canvas node runs", target_fixture="step6_result")
def step6_result(workflow_state: BMIWorkflowState) -> BMIWorkflowState:
    return run_step(workflow_state)


@then('the workflow current step is "design_fit"')
def assert_current_step(step6_result: BMIWorkflowState) -> None:
    assert step6_result["current_step"] == "design_fit"


@then("the value proposition canvas is preserved in the workflow state")
def assert_value_proposition_preserved(
    workflow_state: BMIWorkflowState, step6_result: BMIWorkflowState
) -> None:
    assert step6_result["value_proposition_canvas"] == workflow_state["value_proposition_canvas"]


@then("the workflow state contains a business model canvas")
def assert_business_model_canvas(step6_result: BMIWorkflowState) -> None:
    assert isinstance(step6_result.get("business_model_canvas"), str)
    assert step6_result["business_model_canvas"]


@then("the workflow state contains a fit assessment")
def assert_fit_assessment(step6_result: BMIWorkflowState) -> None:
    assert isinstance(step6_result.get("fit_assessment"), str)
    assert step6_result["fit_assessment"]


@then("the business model canvas uses the CXIF business model headings")
def assert_bmc_headings(step6_result: BMIWorkflowState) -> None:
    business_model_canvas = step6_result["business_model_canvas"]
    assert "## Business Model Canvas" in business_model_canvas
    assert "### Desirability" in business_model_canvas
    assert "### Feasibility" in business_model_canvas
    assert "### Viability" in business_model_canvas


@then("the fit assessment uses the CXIF fit assessment headings")
def assert_fit_headings(step6_result: BMIWorkflowState) -> None:
    fit_assessment = step6_result["fit_assessment"]
    assert "## Fit Assessment" in fit_assessment
    assert "### Problem-Solution Fit" in fit_assessment
    assert "### Product-Market Fit Status" in fit_assessment
    assert "### Business Model Fit Status" in fit_assessment


@then("the business model canvas includes the approved pattern context")
def assert_pattern_context(step6_result: BMIWorkflowState) -> None:
    assert "Cost Differentiators" in step6_result["business_model_canvas"]


@then("the fit assessment includes problem-solution fit rows")
def assert_problem_solution_rows(step6_result: BMIWorkflowState) -> None:
    fit_assessment = step6_result["fit_assessment"]
    assert "| Customer Need (Job/Pain/Gain) | Importance to Customer | Mapped Value Proposition Element | Fit? |" in fit_assessment
    assert "| Complete onboarding quickly" in fit_assessment


@then("the fit assessment includes product-market and business-model status tables")
def assert_status_tables(step6_result: BMIWorkflowState) -> None:
    fit_assessment = step6_result["fit_assessment"]
    assert "| Criterion | Status | Evidence |" in fit_assessment
    assert "| Dimension | Status | Evidence |" in fit_assessment