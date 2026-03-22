from pytest_bdd import given, scenarios, then, when

from backend.app.nodes.step2_pattern import run_step
from backend.app.state import BMIWorkflowState


scenarios("features/step2-pattern-matcher.feature")


@given("a workflow state with interpreted signals from Step 1", target_fixture="workflow_state")
def workflow_state() -> BMIWorkflowState:
    return {
        "session_id": "session-002",
        "current_step": "signal_scan",
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
        "priority_matrix": [
            {
                "signal": "Customers delay onboarding due to workflow complexity",
                "impact": 3,
                "speed": 2,
                "tier": "Act",
            }
        ],
    }


@given("a workflow state with a new-market interpreted signal from Step 1", target_fixture="workflow_state")
def new_market_workflow_state() -> BMIWorkflowState:
    return {
        "session_id": "session-002b",
        "current_step": "signal_scan",
        "input_type": "text",
        "llm_backend": "azure",
        "voc_data": "Small teams can now launch analytics without needing an enterprise implementation project",
        "interpreted_signals": [
            {
                "signal": "Small teams launch analytics without enterprise implementation",
                "zone": "New-Market Foothold",
                "classification": "Disruptive — New-Market",
            }
        ],
        "priority_matrix": [
            {
                "signal": "Small teams launch analytics without enterprise implementation",
                "impact": 3,
                "speed": 3,
                "score": 9,
                "tier": "Act",
            }
        ],
    }


@when("the Step 2 pattern matcher node runs", target_fixture="step2_result")
def step2_result(workflow_state: BMIWorkflowState) -> BMIWorkflowState:
    return run_step(workflow_state)


@then('the workflow current step is "pattern_select"')
def assert_current_step(step2_result: BMIWorkflowState) -> None:
    assert step2_result["current_step"] == "pattern_select"


@then("the interpreted signals are preserved in the workflow state")
def assert_interpreted_signals_preserved(
    workflow_state: BMIWorkflowState, step2_result: BMIWorkflowState
) -> None:
    assert step2_result["interpreted_signals"] == workflow_state["interpreted_signals"]


@then("the workflow state contains an agent recommendation")
def assert_agent_recommendation(step2_result: BMIWorkflowState) -> None:
    assert isinstance(step2_result.get("agent_recommendation"), str)
    assert step2_result["agent_recommendation"]


@then("the agent recommendation says to explore SHIFT first")
def assert_shift_direction(step2_result: BMIWorkflowState) -> None:
    assert "SHIFT" in step2_result["agent_recommendation"]


@then("the agent recommendation says to explore INVENT first")
def assert_invent_direction(step2_result: BMIWorkflowState) -> None:
    assert "INVENT" in step2_result["agent_recommendation"]


@then('the agent recommendation includes "pending_library_source"')
def assert_pending_shift_placeholder(step2_result: BMIWorkflowState) -> None:
    assert "pending_library_source" in step2_result["agent_recommendation"]


@then('the agent recommendation references the verified INVENT pattern "Market Explorers"')
def assert_invent_pattern_reference(step2_result: BMIWorkflowState) -> None:
    assert "Market Explorers" in step2_result["agent_recommendation"]


@then("Step 2 does not set the consultant checkpoint fields")
def assert_checkpoint_fields_unset(step2_result: BMIWorkflowState) -> None:
    assert "pattern_direction" not in step2_result
    assert "selected_patterns" not in step2_result
    assert "pattern_rationale" not in step2_result
