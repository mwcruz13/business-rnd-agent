from uuid import uuid4

from fastapi.testclient import TestClient

from backend.app.main import app


def test_run_endpoint_executes_the_graph_end_to_end() -> None:
    client = TestClient(app)
    session_id = f"api-run-test-{uuid4()}"

    response = client.post(
        "/runs",
        json={
            "input_text": "Customers report onboarding friction, too many manual steps, and delays before they reach value.",
            "session_id": session_id,
            "llm_backend": "azure",
            "pause_at_checkpoints": False,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["session_id"] == session_id
    assert payload["current_step"] == "pdsa_plan"
    assert payload["experiment_selections"]
    assert payload["experiment_plans"]
    assert payload["experiment_worksheets"]


def test_run_endpoint_requires_exactly_one_input_source() -> None:
    client = TestClient(app)

    response = client.post(
        "/runs",
        json={
            "input_text": "inline text",
            "input_path": "/tmp/source.txt",
        },
    )

    assert response.status_code == 422
    assert "Provide exactly one of input_text or input_path" in response.json()["detail"]


def test_run_endpoint_accepts_raw_csv_text() -> None:
    client = TestClient(app)
    session_id = f"api-csv-text-test-{uuid4()}"

    response = client.post(
        "/runs",
        json={
            "input_text": "Reference,Overall Comments\nACME-1,Slow onboarding with too many manual steps\nACME-2,We need faster time-to-value\n",
            "input_format": "csv",
            "session_id": session_id,
            "pause_at_checkpoints": False,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["session_id"] == session_id
    assert payload["input_type"] == "csv"
    assert payload["current_step"] == "pdsa_plan"


def test_run_endpoint_pauses_and_resume_endpoint_advances_workflow() -> None:
    client = TestClient(app)
    session_id = f"api-resume-test-{uuid4()}"

    start_response = client.post(
        "/runs",
        json={
            "input_text": "Customers report onboarding friction, too many manual steps, and delays before they reach value.",
            "session_id": session_id,
            "llm_backend": "azure",
            "pause_at_checkpoints": True,
        },
    )
    assert start_response.status_code == 200
    start_payload = start_response.json()
    assert start_payload["run_status"] == "paused"
    assert start_payload["pending_checkpoint"] == "checkpoint_1"

    # Approve checkpoint_1 → paused at checkpoint_1_5
    checkpoint_1_5 = client.post(f"/runs/{session_id}/resume", json={"decision": "approve"})
    assert checkpoint_1_5.status_code == 200
    assert checkpoint_1_5.json()["pending_checkpoint"] == "checkpoint_1_5"

    # Edit checkpoint_1_5 → paused at checkpoint_3
    checkpoint_3 = client.post(
        f"/runs/{session_id}/resume",
        json={
            "decision": "edit",
            "edit_state": {
                "pattern_direction": "shift",
                "selected_patterns": ["Cost Differentiators"],
                "pattern_rationale": "Consultant selected the incumbent-transformation path.",
            },
        },
    )
    assert checkpoint_3.status_code == 200
    assert checkpoint_3.json()["pending_checkpoint"] == "checkpoint_3"

    # Approve checkpoint_3 → paused at checkpoint_4
    checkpoint_4 = client.post(f"/runs/{session_id}/resume", json={"decision": "approve"})
    assert checkpoint_4.status_code == 200
    assert checkpoint_4.json()["pending_checkpoint"] == "checkpoint_4"

    # Approve checkpoint_4 → paused at checkpoint_5
    checkpoint_5 = client.post(f"/runs/{session_id}/resume", json={"decision": "approve"})
    assert checkpoint_5.status_code == 200
    assert checkpoint_5.json()["pending_checkpoint"] == "checkpoint_5"

    # Approve checkpoint_5 → paused at checkpoint_6
    checkpoint_6 = client.post(f"/runs/{session_id}/resume", json={"decision": "approve"})
    assert checkpoint_6.status_code == 200
    assert checkpoint_6.json()["pending_checkpoint"] == "checkpoint_6"

    # Approve checkpoint_6 → paused at checkpoint_2
    checkpoint_2 = client.post(f"/runs/{session_id}/resume", json={"decision": "approve"})
    assert checkpoint_2.status_code == 200
    assert checkpoint_2.json()["pending_checkpoint"] == "checkpoint_2"

    # Approve checkpoint_2 → paused at checkpoint_8
    checkpoint_8 = client.post(f"/runs/{session_id}/resume", json={"decision": "approve"})
    assert checkpoint_8.status_code == 200
    assert checkpoint_8.json()["pending_checkpoint"] == "checkpoint_8"

    # Approve checkpoint_8 → completed
    completed = client.post(f"/runs/{session_id}/resume", json={"decision": "approve"})
    assert completed.status_code == 200
    assert completed.json()["run_status"] == "completed"
    assert completed.json()["current_step"] == "pdsa_plan"

    fetched = client.get(f"/runs/{session_id}")
    assert fetched.status_code == 200
    assert fetched.json()["run_status"] == "completed"


def test_resume_rejects_checkpoint_1_5_edit_without_pattern_direction() -> None:
    client = TestClient(app)
    session_id = f"api-invalid-resume-test-{uuid4()}"

    client.post(
        "/runs",
        json={
            "input_text": "Customers report onboarding friction, too many manual steps, and delays before they reach value.",
            "session_id": session_id,
            "pause_at_checkpoints": True,
        },
    )
    client.post(f"/runs/{session_id}/resume", json={"decision": "approve"})

    invalid_resume = client.post(
        f"/runs/{session_id}/resume",
        json={"decision": "edit", "edit_state": {"pattern_direction": ""}},
    )
    assert invalid_resume.status_code == 422
    assert "pattern_direction" in invalid_resume.json()["detail"]


def test_start_from_step_endpoint_begins_at_step_1() -> None:
    client = TestClient(app)
    session_id = f"api-start-step1-{uuid4()}"

    response = client.post(
        "/runs/start-from-step",
        json={
            "step_number": 1,
            "initial_state": {"voc_data": "Onboarding is slow and painful"},
            "session_id": session_id,
            "llm_backend": "azure",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["run_status"] == "paused"
    assert payload["pending_checkpoint"] == "checkpoint_1"


def test_start_from_step_rejects_missing_upstream_state() -> None:
    client = TestClient(app)

    response = client.post(
        "/runs/start-from-step",
        json={
            "step_number": 3,
            "initial_state": {"voc_data": "Some data but no signals"},
        },
    )
    assert response.status_code == 422
    assert "missing required upstream state" in response.json()["detail"]


def test_start_from_step_rejects_invalid_step_number() -> None:
    client = TestClient(app)

    response = client.post(
        "/runs/start-from-step",
        json={
            "step_number": 0,
            "initial_state": {"voc_data": "anything"},
        },
    )
    assert response.status_code == 422
    assert "step_number must be between" in response.json()["detail"]


def test_get_step_output_returns_persisted_output() -> None:
    client = TestClient(app)
    session_id = f"api-step-output-{uuid4()}"

    # Start a run to populate step outputs
    client.post(
        "/runs",
        json={
            "input_text": "Onboarding takes too long",
            "session_id": session_id,
            "llm_backend": "azure",
            "pause_at_checkpoints": True,
        },
    )

    response = client.get(f"/runs/{session_id}/step/1")
    assert response.status_code == 200
    payload = response.json()
    assert payload["step_number"] == 1
    assert payload["step_name"] == "step1_signal"


def test_get_step_output_returns_404_for_missing_step() -> None:
    client = TestClient(app)

    response = client.get("/runs/nonexistent-session/step/1")
    assert response.status_code == 404