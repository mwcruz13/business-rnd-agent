from uuid import uuid4
from typing import Any, cast

from pytest_bdd import given, parsers, scenarios, then, when

from backend.app.workflow import get_run_state
from backend.app.workflow import resume_workflow
from backend.app.workflow import run_workflow_from_voc_data


scenarios("features/workflow-checkpoints.feature")


def _build_context() -> dict[str, object]:
    return {
        "session_id": f"bdd-workflow-checkpoints-{uuid4()}",
        "voc_data": "Customers report onboarding friction, too many manual steps, and delays before they reach value.",
        "result": None,
        "error": None,
    }


@given("a checkpointed workflow input describing onboarding friction", target_fixture="workflow_context")
def workflow_context() -> dict[str, object]:
    return _build_context()


@given("a checkpointed workflow already paused at the pattern checkpoint", target_fixture="workflow_context")
def paused_at_pattern_checkpoint() -> dict[str, object]:
    context = _build_context()
    context["result"] = run_workflow_from_voc_data(
        str(context["voc_data"]),
        session_id=str(context["session_id"]),
        llm_backend="azure",
        pause_at_checkpoints=True,
    )
    context["result"] = resume_workflow(str(context["session_id"]), decision="approve")
    return context


@when("the consultant starts the checkpointed workflow")
def start_checkpointed_workflow(workflow_context: dict[str, object]) -> None:
    workflow_context["error"] = None
    workflow_context["result"] = run_workflow_from_voc_data(
        str(workflow_context["voc_data"]),
        session_id=str(workflow_context["session_id"]),
        llm_backend="azure",
        pause_at_checkpoints=True,
    )


@when("the consultant approves the current checkpoint")
def approve_current_checkpoint(workflow_context: dict[str, object]) -> None:
    workflow_context["error"] = None
    workflow_context["result"] = resume_workflow(str(workflow_context["session_id"]), decision="approve")


@when("the consultant retries the current checkpoint")
def retry_current_checkpoint(workflow_context: dict[str, object]) -> None:
    workflow_context["error"] = None
    workflow_context["result"] = resume_workflow(str(workflow_context["session_id"]), decision="retry")


@when(
    parsers.parse(
        'the consultant edits the current checkpoint with direction "{direction}" pattern "{pattern}" rationale "{rationale}"'
    )
)
def edit_current_checkpoint(
    workflow_context: dict[str, object],
    direction: str,
    pattern: str,
    rationale: str,
) -> None:
    workflow_context["error"] = None
    workflow_context["result"] = resume_workflow(
        str(workflow_context["session_id"]),
        decision="edit",
        edit_state={
            "pattern_direction": direction,
            "selected_patterns": [pattern],
            "pattern_rationale": rationale,
        },
    )


@when("the consultant edits the current checkpoint without pattern direction")
def edit_without_direction(workflow_context: dict[str, object]) -> None:
    workflow_context["result"] = None
    try:
        resume_workflow(
            str(workflow_context["session_id"]),
            decision="edit",
            edit_state={"pattern_direction": ""},
        )
    except ValueError as error:
        workflow_context["error"] = str(error)
    else:
        workflow_context["error"] = None


@then(parsers.parse('the workflow run status is "{expected_status}"'))
def assert_run_status(
    workflow_context: dict[str, object], expected_status: str
) -> None:
    result = cast(dict[str, Any], workflow_context["result"])
    assert result.get("run_status") == expected_status


@then(parsers.parse('the pending checkpoint is "{expected_checkpoint}"'))
def assert_pending_checkpoint(
    workflow_context: dict[str, object], expected_checkpoint: str
) -> None:
    result = cast(dict[str, Any], workflow_context["result"])
    assert result.get("pending_checkpoint") == expected_checkpoint


@then("no pending checkpoint remains")
def assert_no_pending_checkpoint(workflow_context: dict[str, object]) -> None:
    result = cast(dict[str, Any], workflow_context["result"])
    assert result.get("pending_checkpoint") is None


@then(parsers.parse('the workflow current step is "{expected_step}"'))
def assert_workflow_step(
    workflow_context: dict[str, object], expected_step: str
) -> None:
    result = cast(dict[str, Any], workflow_context["result"])
    assert result.get("current_step") == expected_step


@then(parsers.parse('checkpoint resume fails with message "{expected_message}"'))
def assert_resume_failure(
    workflow_context: dict[str, object], expected_message: str
) -> None:
    assert workflow_context["result"] is None
    assert workflow_context["error"] == expected_message


@then(parsers.parse('the final workflow artifacts include the selected pattern "{pattern}"'))
def assert_selected_pattern_propagation(
    workflow_context: dict[str, object], pattern: str
) -> None:
    result = cast(dict[str, Any], workflow_context["result"])
    for field_name in [
        "value_proposition_canvas",
        "business_model_canvas",
        "assumptions",
        "experiment_selections",
        "experiment_plans",
        "experiment_worksheets",
    ]:
        field_value = result.get(field_name)
        assert isinstance(field_value, str)
        assert pattern in field_value


@then(parsers.parse('the final workflow artifacts do not include the unselected pattern "{pattern}"'))
def assert_unselected_pattern_absence(
    workflow_context: dict[str, object], pattern: str
) -> None:
    result = cast(dict[str, Any], workflow_context["result"])
    for field_name in [
        "value_proposition_canvas",
        "business_model_canvas",
        "assumptions",
        "experiment_selections",
        "experiment_plans",
        "experiment_worksheets",
    ]:
        field_value = result.get(field_name)
        assert isinstance(field_value, str)
        assert pattern not in field_value


@then("the persisted workflow state matches the completed run")
def assert_persisted_state(workflow_context: dict[str, object]) -> None:
    result = cast(dict[str, Any], workflow_context["result"])
    persisted = get_run_state(str(workflow_context["session_id"]))
    assert persisted.get("run_status") == result.get("run_status")
    assert persisted.get("current_step") == result.get("current_step")