from uuid import uuid4

from pytest_bdd import given, parsers, scenarios, then, when

from backend.app.workflow import start_workflow_from_step


scenarios("features/start-from-step.feature")


STEP_2_UPSTREAM_STATE = {
    "voc_data": "Customer onboarding is slow",
    "signals": [{"signal": "onboarding friction", "source": "survey", "strength": "strong"}],
}

STEP_3_UPSTREAM_STATE = {
    **STEP_2_UPSTREAM_STATE,
    "pattern_direction": "shift",
    "selected_patterns": ["Cost Differentiators"],
}

STEP_4_UPSTREAM_STATE = {
    **STEP_3_UPSTREAM_STATE,
    "customer_profile": "Enterprise IT buyers experiencing slow onboarding cycles.",
}

STEP_5_UPSTREAM_STATE = {
    **STEP_4_UPSTREAM_STATE,
    "value_driver_tree": "## Value Driver Tree\n| Driver | Type | Baseline | Target |\n|---|---|---|---|\n| Onboarding speed | Time | 30 days | 7 days |",
    "actionable_insights": "## Actionable Insights\n- Reduce manual steps in onboarding workflow.",
}

STEP_6_UPSTREAM_STATE = {
    **STEP_5_UPSTREAM_STATE,
    "value_proposition_canvas": "## Value Proposition Canvas\nProducts: Automated onboarding portal.",
    "fit_assessment": "## Fit Assessment\nProblem-solution fit: strong alignment.",
}

STEP_7_UPSTREAM_STATE = {
    **STEP_6_UPSTREAM_STATE,
    "business_model_canvas": "## Business Model Canvas\nKey Partners: Cloud providers.",
}

STEP_8_UPSTREAM_STATE = {
    **STEP_7_UPSTREAM_STATE,
    "assumptions": "## Importance × Evidence Map\n| Assumption | Quadrant |\n|---|---|\n| Customers want self-serve | Test first |",
}

STEP_9_UPSTREAM_STATE = {
    **STEP_8_UPSTREAM_STATE,
    "experiment_cards": [{"card_name": "Single Feature MVP", "assumption": "Customers want self-serve"}],
}


@given(parsers.parse('initial state with voc_data "{voc_data}"'), target_fixture="initial_state")
def initial_state_with_voc_data(voc_data: str) -> dict:
    return {"voc_data": voc_data}


@given("initial state with upstream fields for step 2", target_fixture="initial_state")
def initial_state_for_step_2() -> dict:
    return dict(STEP_2_UPSTREAM_STATE)


@given("initial state with upstream fields for step 3", target_fixture="initial_state")
def initial_state_for_step_3() -> dict:
    return dict(STEP_3_UPSTREAM_STATE)


@given("initial state with upstream fields for step 4", target_fixture="initial_state")
def initial_state_for_step_4() -> dict:
    return dict(STEP_4_UPSTREAM_STATE)


@given("initial state with upstream fields for step 5", target_fixture="initial_state")
def initial_state_for_step_5() -> dict:
    return dict(STEP_5_UPSTREAM_STATE)


@given("initial state with upstream fields for step 6", target_fixture="initial_state")
def initial_state_for_step_6() -> dict:
    return dict(STEP_6_UPSTREAM_STATE)


@given("initial state with upstream fields for step 7", target_fixture="initial_state")
def initial_state_for_step_7() -> dict:
    return dict(STEP_7_UPSTREAM_STATE)


@given("initial state with upstream fields for step 8", target_fixture="initial_state")
def initial_state_for_step_8() -> dict:
    return dict(STEP_8_UPSTREAM_STATE)


@given("initial state with upstream fields for step 9", target_fixture="initial_state")
def initial_state_for_step_9() -> dict:
    return dict(STEP_9_UPSTREAM_STATE)


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
