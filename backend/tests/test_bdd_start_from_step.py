from uuid import uuid4

from pytest_bdd import given, parsers, scenarios, then, when

from backend.app.workflow import start_workflow_from_step


scenarios("features/start-from-step.feature")


STEP_3_UPSTREAM_STATE = {
    "voc_data": "Customer onboarding is slow",
    "signals": [{"signal": "onboarding friction", "source": "survey", "strength": "strong"}],
    "pattern_direction": "shift",
    "selected_patterns": ["Cost Differentiators"],
}


@given(parsers.parse('initial state with voc_data "{voc_data}"'), target_fixture="initial_state")
def initial_state_with_voc_data(voc_data: str) -> dict:
    return {"voc_data": voc_data}


@given("initial state with upstream fields for step 3", target_fixture="initial_state")
def initial_state_for_step_3() -> dict:
    return dict(STEP_3_UPSTREAM_STATE)


@when(
    parsers.parse("the workflow is started from step {step_number:d}"),
    target_fixture="start_result",
)
def start_from_step(initial_state: dict, step_number: int) -> dict:
    try:
        result = start_workflow_from_step(
            step_number,
            initial_state,
            session_id=f"bdd-start-from-step-{uuid4()}",
            llm_backend="azure",
            pause_at_checkpoints=True,
        )
        return {"state": dict(result), "error": None}
    except ValueError as exc:
        return {"state": None, "error": str(exc)}


@then(parsers.parse('the run status is "{expected}"'))
def assert_run_status(start_result: dict, expected: str) -> None:
    assert start_result["error"] is None, f"Unexpected error: {start_result['error']}"
    assert start_result["state"]["run_status"] == expected


@then(parsers.parse('the pending checkpoint is "{expected}"'))
def assert_pending_checkpoint(start_result: dict, expected: str) -> None:
    assert start_result["state"]["pending_checkpoint"] == expected


@then(parsers.parse('the start is rejected with a message containing "{fragment}"'))
def assert_start_rejected(start_result: dict, fragment: str) -> None:
    assert start_result["state"] is None
    assert fragment in start_result["error"]
