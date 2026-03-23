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

    checkpoint_1_5 = client.post(f"/runs/{session_id}/resume", json={"decision": "approve"})
    assert checkpoint_1_5.status_code == 200
    assert checkpoint_1_5.json()["pending_checkpoint"] == "checkpoint_1_5"

    checkpoint_2 = client.post(
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
    assert checkpoint_2.status_code == 200
    assert checkpoint_2.json()["pending_checkpoint"] == "checkpoint_2"

    completed = client.post(f"/runs/{session_id}/resume", json={"decision": "approve"})
    assert completed.status_code == 200
    assert completed.json()["run_status"] == "completed"
    assert completed.json()["current_step"] == "pdsa_plan"

    fetched = client.get(f"/runs/{session_id}")
    assert fetched.status_code == 200
    assert fetched.json()["run_status"] == "completed"


def test_resume_requires_consultant_pattern_selection_for_checkpoint_1_5() -> None:
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

    invalid_resume = client.post(f"/runs/{session_id}/resume", json={"decision": "approve"})
    assert invalid_resume.status_code == 422
    assert "checkpoint_1_5" in invalid_resume.json()["detail"]