from pytest_bdd import given, parsers, scenarios, then, when

from backend.app.nodes.step3_profile import run_step
from backend.app.state import BMIWorkflowState


scenarios("features/step3-customer-profile.feature")


@given("a workflow state with a consultant-approved pattern direction", target_fixture="workflow_state")
def workflow_state() -> BMIWorkflowState:
    return {
        "session_id": "session-003",
        "current_step": "pattern_select",
        "input_type": "text",
        "llm_backend": "azure",
        "voc_data": "Customers avoid onboarding because it is too complex",
        "interpreted_signals": [
            {
                "signal": "Customers delay onboarding due to workflow complexity",
                "zone": "Overserved Customers",
                "classification": "Disruptive - Low-End",
            }
        ],
        "agent_recommendation": "Shift toward a simpler low-friction model using Cost Differentiators.",
        "pattern_direction": "shift",
        "selected_patterns": ["Cost Differentiators"],
    }


@when("the Step 3 customer profile node runs", target_fixture="step3_result")
def step3_result(workflow_state: BMIWorkflowState) -> BMIWorkflowState:
    return run_step(workflow_state)


@then('the workflow current step is "empathize"')
def assert_current_step(step3_result: BMIWorkflowState) -> None:
    assert step3_result["current_step"] == "empathize"


@then("the selected patterns are preserved in the workflow state")
def assert_selected_patterns_preserved(
    workflow_state: BMIWorkflowState, step3_result: BMIWorkflowState
) -> None:
    assert step3_result["selected_patterns"] == workflow_state["selected_patterns"]


@then("the workflow state contains a customer profile")
def assert_customer_profile(step3_result: BMIWorkflowState) -> None:
    assert isinstance(step3_result.get("customer_profile"), str)
    assert step3_result["customer_profile"]


@then("the customer profile uses the CXIF empathy headings")
def assert_cxif_headings(step3_result: BMIWorkflowState) -> None:
    customer_profile = step3_result["customer_profile"]
    assert "## Customer Empathy Profile" in customer_profile
    assert "### Customer Jobs" in customer_profile
    assert "### Customer Pains" in customer_profile
    assert "### Customer Gains" in customer_profile


@then("the customer profile includes the selected pattern context")
def assert_selected_pattern_context(
    workflow_state: BMIWorkflowState, step3_result: BMIWorkflowState
) -> None:
    customer_profile = step3_result["customer_profile"]
    assert workflow_state["selected_patterns"][0] in customer_profile


@then(parsers.parse("the customer profile includes at least {minimum:d} customer jobs"))
def assert_minimum_jobs(step3_result: BMIWorkflowState, minimum: int) -> None:
    customer_profile = step3_result["customer_profile"]
    assert customer_profile.count("| Functional |") >= 1
    assert customer_profile.count("| Social |") >= 1
    assert customer_profile.count("| Emotional |") >= 1
    assert minimum <= 3


@then(parsers.parse("the customer profile includes at least {minimum:d} customer pains"))
def assert_minimum_pains(step3_result: BMIWorkflowState, minimum: int) -> None:
    customer_profile = step3_result["customer_profile"]
    assert customer_profile.count("| Functional |") >= 2
    assert customer_profile.count("| Social |") >= 2
    assert customer_profile.count("| Emotional |") >= 2
    assert minimum <= 3


@then(parsers.parse("the customer profile includes at least {minimum:d} customer gains"))
def assert_minimum_gains(step3_result: BMIWorkflowState, minimum: int) -> None:
    customer_profile = step3_result["customer_profile"]
    assert customer_profile.count("| Functional |") >= 3
    assert customer_profile.count("| Social |") >= 3
    assert customer_profile.count("| Emotional |") >= 3
    assert minimum <= 3