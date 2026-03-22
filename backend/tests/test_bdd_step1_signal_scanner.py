from pytest_bdd import given, parsers, scenarios, then, when

from backend.app.nodes.step1_signal import run_step
from backend.app.state import BMIWorkflowState


scenarios("features/step1-signal-scanner.feature")


@given(parsers.parse('a workflow state with VoC data "{voc_data}"'), target_fixture="workflow_state")
def workflow_state(voc_data: str) -> BMIWorkflowState:
    return {
        "session_id": "session-001",
        "current_step": "ingest",
        "input_type": "text",
        "llm_backend": "azure",
        "voc_data": voc_data,
    }


@when("the Step 1 signal scanner node runs", target_fixture="step1_result")
def step1_result(workflow_state: BMIWorkflowState) -> BMIWorkflowState:
    return run_step(workflow_state)


@then(parsers.parse('the workflow current step is "{expected_step}"'))
def assert_current_step(step1_result: BMIWorkflowState, expected_step: str) -> None:
    assert step1_result["current_step"] == expected_step


@then("the original VoC data is preserved in the workflow state")
def assert_voc_data_preserved(workflow_state: BMIWorkflowState, step1_result: BMIWorkflowState) -> None:
    assert step1_result["voc_data"] == workflow_state["voc_data"]


@then("the workflow state contains a signals list")
def assert_signals_list(step1_result: BMIWorkflowState) -> None:
    assert isinstance(step1_result.get("signals"), list)


@then("the workflow state contains an interpreted signals list")
def assert_interpreted_signals_list(step1_result: BMIWorkflowState) -> None:
    assert isinstance(step1_result.get("interpreted_signals"), list)


@then("the workflow state contains a priority matrix list")
def assert_priority_matrix_list(step1_result: BMIWorkflowState) -> None:
    assert isinstance(step1_result.get("priority_matrix"), list)


@then(parsers.parse('the first detected signal uses the zone "{expected_zone}"'))
def assert_first_signal_zone(step1_result: BMIWorkflowState, expected_zone: str) -> None:
    signals = step1_result.get("signals") or []
    assert signals
    assert signals[0]["zone"] == expected_zone


@then(parsers.parse('the first interpreted signal uses the classification "{expected_classification}"'))
def assert_first_interpreted_signal_classification(
    step1_result: BMIWorkflowState, expected_classification: str
) -> None:
    interpreted_signals = step1_result.get("interpreted_signals") or []
    assert interpreted_signals
    assert interpreted_signals[0]["classification"] == expected_classification


@then("the interpreted signal only uses SOC Radar filter names")
def assert_interpreted_signal_uses_soc_filters(step1_result: BMIWorkflowState) -> None:
    interpreted_signals = step1_result.get("interpreted_signals") or []
    assert interpreted_signals
    filters = interpreted_signals[0].get("filters")
    assert filters == ["Performance Overshoot", "Business Model Conflict"]


@then(parsers.parse("the first priority matrix entry has a score of {expected_score:d}"))
def assert_priority_score(step1_result: BMIWorkflowState, expected_score: int) -> None:
    priority_matrix = step1_result.get("priority_matrix") or []
    assert priority_matrix
    assert priority_matrix[0]["score"] == expected_score


@then(parsers.parse('the first priority matrix entry uses the tier "{expected_tier}"'))
def assert_priority_tier(step1_result: BMIWorkflowState, expected_tier: str) -> None:
    priority_matrix = step1_result.get("priority_matrix") or []
    assert priority_matrix
    assert priority_matrix[0]["tier"] == expected_tier