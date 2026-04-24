import csv
from uuid import uuid4

import pytest

from backend.app.workflow import get_run_state
from backend.app.workflow import resume_workflow
from backend.app.workflow import run_workflow_from_path, run_workflow_from_voc_data


def test_run_workflow_from_voc_data_reaches_step_8() -> None:
    result = run_workflow_from_voc_data(
        "Customers report onboarding friction, too many manual steps, and delays before they reach value.",
        session_id=f"workflow-service-test-{uuid4()}",
        llm_backend="azure",
        pause_at_checkpoints=False,
    )

    assert result["current_step"] == "pdsa_plan"
    assert result["experiment_selections"]
    assert result["experiment_plans"]
    assert result["experiment_worksheets"]


def test_run_workflow_from_csv_path_reaches_step_8(tmp_path) -> None:
    csv_path = tmp_path / "survey.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["Reference", "Overall Comments"])
        writer.writerow(["ACME-1", "Slow onboarding with too many manual steps"])
        writer.writerow(["ACME-2", "We need faster time-to-value"])

    result = run_workflow_from_path(
        csv_path,
        session_id=f"workflow-csv-test-{uuid4()}",
        llm_backend="azure",
        pause_at_checkpoints=False,
    )

    assert result["input_type"] == "csv"
    assert result["current_step"] == "pdsa_plan"


def test_run_workflow_rejects_empty_input() -> None:
    with pytest.raises(ValueError, match="cannot be empty"):
        run_workflow_from_voc_data("   ")


def test_checkpointed_workflow_pauses_and_resumes_to_completion() -> None:
    session_id = f"workflow-checkpoint-test-{uuid4()}"

    first_pause = run_workflow_from_voc_data(
        "Customers report onboarding friction, too many manual steps, and delays before they reach value.",
        session_id=session_id,
        llm_backend="azure",
        pause_at_checkpoints=True,
    )
    assert first_pause["run_status"] == "paused"
    assert first_pause["pending_checkpoint"] == "checkpoint_1a"
    assert first_pause["current_step"] == "signal_scan"

    second_pause = resume_workflow(session_id, decision="approve")
    assert second_pause["run_status"] == "paused"
    assert second_pause["pending_checkpoint"] == "checkpoint_1b"
    assert second_pause["current_step"] == "signal_recommend"

    third_pause = resume_workflow(session_id, decision="approve")
    assert third_pause["run_status"] == "paused"
    assert third_pause["pending_checkpoint"] == "checkpoint_2"
    assert third_pause["current_step"] == "pattern_select"

    fourth_pause = resume_workflow(
        session_id,
        decision="edit",
        edit_state={
            "pattern_direction": "shift",
            "selected_patterns": ["Cost Differentiators"],
            "pattern_rationale": "Consultant selected the incumbent-transformation path.",
        },
    )
    assert fourth_pause["run_status"] == "paused"
    assert fourth_pause["pending_checkpoint"] == "checkpoint_3"
    assert fourth_pause["current_step"] == "empathize"

    # Approve through remaining checkpoints (4, 5a, 5b, 6, 7, 8, 9)
    for expected_cp, expected_step in [
        ("checkpoint_4", "measure_define"),
        ("checkpoint_5a", "vp_ideation"),
        ("checkpoint_5b", "vp_scoring"),
        ("checkpoint_6", "design_fit"),
        ("checkpoint_7", "risk_map"),
        ("checkpoint_8", "pdsa_plan"),
        ("checkpoint_9", "pdsa_plan"),
    ]:
        state = resume_workflow(session_id, decision="approve")
        assert state["run_status"] == "paused"
        assert state["pending_checkpoint"] == expected_cp
        assert state["current_step"] == expected_step

    completed = resume_workflow(session_id, decision="approve")
    assert completed["run_status"] == "completed"
    assert completed.get("pending_checkpoint") is None
    assert completed["current_step"] == "pdsa_plan"
    assert completed["experiment_plans"]

    persisted = get_run_state(session_id)
    assert persisted["run_status"] == "completed"
    assert persisted["current_step"] == "pdsa_plan"


def test_invent_pattern_selection_propagates_without_shift_leakage() -> None:
    session_id = f"workflow-invent-pattern-test-{uuid4()}"

    run_workflow_from_voc_data(
        "Customers report onboarding friction, too many manual steps, and delays before they reach value.",
        session_id=session_id,
        llm_backend="azure",
        pause_at_checkpoints=True,
    )
    resume_workflow(session_id, decision="approve")
    resume_workflow(
        session_id,
        decision="edit",
        edit_state={
            "pattern_direction": "invent",
            "selected_patterns": ["Market Explorers"],
            "pattern_rationale": "Consultant selected the new-market exploration path.",
        },
    )
    # Approve through remaining checkpoints (3, 4, 5a, 5b, 6, 7, 8)
    for _ in range(6):
        resume_workflow(session_id, decision="approve")
    completed = resume_workflow(session_id, decision="approve")

    for field_name in [
        "value_proposition_canvas",
        "business_model_canvas",
        "assumptions",
        "experiment_selections",
        "experiment_plans",
        "experiment_worksheets",
    ]:
        field_value = completed[field_name]
        assert "Market Explorers" in field_value
        assert "Cost Differentiators" not in field_value