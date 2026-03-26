from uuid import uuid4
from typing import Any, cast

from pytest_bdd import given, scenarios, then, when

from backend.app.workflow import run_workflow_from_voc_data


scenarios("features/workflow-orchestrator.feature")


@given("a VoC input describing onboarding friction", target_fixture="workflow_context")
def workflow_context() -> dict[str, object]:
    return {
        "voc_data": "Customers report onboarding friction, too many manual steps, and delays before they reach value.",
        "result": None,
    }


@when("the consultant runs the workflow through the LangGraph orchestrator")
def run_orchestrated_workflow(workflow_context: dict[str, object]) -> None:
    workflow_context["result"] = run_workflow_from_voc_data(
        str(workflow_context["voc_data"]),
        session_id=f"bdd-workflow-orchestrator-{uuid4()}",
        llm_backend="azure",
        pause_at_checkpoints=False,
    )


@then('the workflow run status is "completed"')
def assert_completed_status(workflow_context: dict[str, object]) -> None:
    result = cast(dict[str, Any], workflow_context["result"])
    assert result.get("run_status") == "completed"


@then('the workflow current step is "pdsa_plan"')
def assert_final_step(workflow_context: dict[str, object]) -> None:
    result = cast(dict[str, Any], workflow_context["result"])
    assert result.get("current_step") == "pdsa_plan"


@then("the workflow state contains Step 8 experiment artifacts")
def assert_step8_artifacts(workflow_context: dict[str, object]) -> None:
    result = cast(dict[str, Any], workflow_context["result"])
    assert result.get("experiment_selections")
    assert result.get("experiment_plans")
    assert result.get("experiment_worksheets")
