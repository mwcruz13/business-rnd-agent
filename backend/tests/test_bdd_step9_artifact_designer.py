from __future__ import annotations

from pytest_bdd import given, scenarios, then, when

from backend.app.nodes.step9_artifact_designer import run_step
from backend.app.state import BMIWorkflowState


scenarios("features/step9-artifact-designer.feature")


@given(
    "a workflow state with experiment cards ready for artifact design",
    target_fixture="workflow_state",
)
def workflow_state() -> BMIWorkflowState:
    return {
        "session_id": "session-9",
        "current_step": "pdsa_plan",
        "experiment_cards": [
            {
                "id": "exp-001",
                "assumption": "I believe onboarding stakeholders need proof complexity is reduced before adoption.",
                "card_name": "Problem Interviews",
                "asset_needed": "Interview Guide v1 + Screener",
                "asset_spec": "10-question interview script, participant screener form, and evidence capture template.",
                "asset_acceptance_criteria": "Guide covers trigger, impact, alternatives, urgency, and decision moments with no leading prompts.",
            },
            {
                "id": "exp-002",
                "assumption": "I believe delivery teams can run guided onboarding without manual recovery.",
                "card_name": "Throwaway Prototype",
                "asset_needed": "Workflow Throwaway Prototype",
                "asset_spec": "Clickable prototype of critical onboarding path with 3-5 tasks and failure-state branches.",
                "asset_acceptance_criteria": "Prototype allows observation of completion, drop-off points, and manual recovery events.",
            },
        ],
    }


@when("the Step 9 artifact designer node runs", target_fixture="step9_result")
def step9_result(workflow_state: BMIWorkflowState) -> BMIWorkflowState:
    return run_step(workflow_state)


@then('the workflow current step is "pdsa_plan"')
def assert_current_step(step9_result: BMIWorkflowState) -> None:
    assert step9_result["current_step"] == "pdsa_plan"


@then("the workflow state contains artifact designs")
def assert_artifact_designs(step9_result: BMIWorkflowState) -> None:
    designs = step9_result.get("artifact_designs")
    assert isinstance(designs, list)
    assert designs


@then("each artifact design includes a concrete artifact name")
def assert_concrete_artifact_name(step9_result: BMIWorkflowState) -> None:
    for design in step9_result["artifact_designs"]:
        assert isinstance(design["artifact_name"], str)
        assert design["artifact_name"].strip()


@then("each artifact design includes a deliverable checklist")
def assert_checklist(step9_result: BMIWorkflowState) -> None:
    for design in step9_result["artifact_designs"]:
        checklist = design.get("deliverable_checklist")
        assert isinstance(checklist, list)
        assert len(checklist) >= 3
