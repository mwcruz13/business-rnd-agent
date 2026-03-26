from pytest_bdd import given, parsers, scenarios, then, when

from backend.app.graph import WORKFLOW_STEP_ORDER, determine_next_step
from backend.app.state import BMIWorkflowState


scenarios("features/orchestrator-routing.feature")


def _minimal_state(**overrides) -> BMIWorkflowState:
    base: BMIWorkflowState = {
        "session_id": "routing-test",
        "current_step": "ingest",
        "input_type": "text",
        "llm_backend": "azure",
        "voc_data": "test data",
    }
    base.update(overrides)
    return base


@given("a workflow state with no completed steps", target_fixture="routing_state")
def state_no_completed() -> BMIWorkflowState:
    return _minimal_state(completed_steps=[])


@given(
    parsers.parse('a workflow state with completed steps "{steps}"'),
    target_fixture="routing_state",
)
def state_with_completed(steps: str) -> BMIWorkflowState:
    return _minimal_state(completed_steps=steps.split(","))


@given("a workflow state with all 8 steps completed", target_fixture="routing_state")
def state_all_completed() -> BMIWorkflowState:
    return _minimal_state(completed_steps=list(WORKFLOW_STEP_ORDER))


@when("the orchestrator decides the next step", target_fixture="orchestrator_result")
def run_orchestrator(routing_state: BMIWorkflowState) -> BMIWorkflowState:
    next_step = determine_next_step(routing_state)
    return {**routing_state, "next_step": next_step}


@then(parsers.parse('the next step is "{expected}"'))
def assert_next_step(orchestrator_result: BMIWorkflowState, expected: str) -> None:
    assert orchestrator_result["next_step"] == expected
