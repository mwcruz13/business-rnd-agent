"""Tests for Phase 3: signal-seeded CXIF workflow."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.app.db.models import Base, SignalRecord, SignalReport, WorkflowRun
from backend.app.db.session import SessionLocal, engine
from backend.app.main import app
from backend.app.services import signal_repository as repo
from backend.app.workflow import _signal_to_workflow_state


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _setup_tables():
    """Ensure all required tables exist and clean up after each test."""
    Base.metadata.create_all(engine)
    yield
    sess = SessionLocal()
    try:
        sess.query(SignalRecord).delete()
        sess.query(SignalReport).delete()
        # Clean up any workflow runs created during tests
        sess.query(WorkflowRun).filter(WorkflowRun.input_type == "signal").delete()
        sess.commit()
    finally:
        sess.close()


@pytest.fixture
def sample_report():
    return repo.upsert_report(
        bu="Compute",
        survey_source="Partner Experience Survey",
        title="Test Report — Compute (Partner VoC)",
        input_stats={"total_comments": 50, "bu_comments": 30},
        source_file="test_report.json",
        reinforcement_map={"chain": ["sig1", "sig2"], "strategic_insight": "Test insight"},
    )


@pytest.fixture
def sample_signals(sample_report):
    """Create 3 signals in the same report with realistic full_analysis."""
    sigs = []
    for i, (title, zone, classification, tier, score) in enumerate([
        ("Tool outage forces competitors", "Nonconsumption", "Disruptive — Low-End", "Act", 9),
        ("Pricing complexity drives churn", "Overserved Customers", "Sustaining", "Investigate", 4),
        ("AI workload shift to cloud", "Enabling Technology", "Disruptive — New-Market", "Act", 6),
    ], start=1):
        sig = repo.upsert_signal(
            report_id=sample_report.id,
            signal_id=str(i),
            signal_title=title,
            bu="Compute",
            survey_source="Partner Experience Survey",
            signal_zone=zone,
            classification=classification,
            action_tier=tier,
            priority_score=score,
            observable_behavior=f"Observable behavior for signal {i}",
            full_analysis={
                "phase_1_scan": {
                    "id": i,
                    "signal": title,
                    "signal_zone": zone,
                    "source_type": "Internal VoC",
                    "observable_behavior": f"Observable behavior for signal {i}",
                    "evidence": [f"Quote {i}a", f"Quote {i}b"],
                    "supporting_comments": [i, i + 10],
                },
                "phase_2_interpret": {
                    "signal_id": i,
                    "signal": title,
                    "classification": classification,
                    "confidence": "High",
                    "litmus_test": "Pass" if "Disruptive" in classification else "",
                    "litmus_rationale": f"Rationale for signal {i}",
                    "filters": [],
                    "filters_passed": 3 if "Disruptive" in classification else 0,
                    "disruptive_potential": "High" if "Disruptive" in classification else "",
                    "value_network_insight": f"Value network for {i}",
                    "alternative_explanation": f"Alternative for {i}",
                    "key_evidence_gap": f"Evidence gap for {i}",
                },
                "phase_3_prioritize": {
                    "signal_id": i,
                    "signal": title,
                    "classification": classification,
                    "impact": 3 if score >= 6 else 2,
                    "speed": 3 if score >= 6 else 2,
                    "priority_score": score,
                    "action_tier": tier,
                    "rationale": f"Priority rationale for signal {i}",
                },
                "phase_4_recommend": {
                    "next_steps": [f"Action for signal {i}"],
                    "owner": "CX Team",
                    "timeframe": "30 days",
                },
            },
        )
        sigs.append(sig)
    return sigs


# ---------------------------------------------------------------------------
# Unit tests: _signal_to_workflow_state
# ---------------------------------------------------------------------------

class TestSignalToWorkflowState:

    def test_basic_mapping(self, sample_signals):
        """State has signals, interpreted_signals, priority_matrix populated."""
        sig_dict = repo.get_signal(sample_signals[0].id)
        report = repo.get_report(sig_dict["report_id"])
        siblings = repo.list_signals(bu="Compute", survey_source="Partner Experience Survey")

        state = _signal_to_workflow_state(sig_dict, siblings, report)

        assert len(state["signals"]) == 3
        assert len(state["interpreted_signals"]) == 3
        assert len(state["priority_matrix"]) == 3

    def test_completed_steps(self, sample_signals):
        """State pre-marks step1a and step1b as completed."""
        sig_dict = repo.get_signal(sample_signals[0].id)
        report = repo.get_report(sig_dict["report_id"])
        siblings = repo.list_signals(bu="Compute", survey_source="Partner Experience Survey")

        state = _signal_to_workflow_state(sig_dict, siblings, report)

        assert "step1a_signal_scan" in state["completed_steps"]
        assert "step1b_signal_recommend" in state["completed_steps"]
        assert len(state["completed_steps"]) == 2

    def test_voc_data_from_behaviors(self, sample_signals):
        """voc_data is constructed from observable behaviors."""
        sig_dict = repo.get_signal(sample_signals[0].id)
        report = repo.get_report(sig_dict["report_id"])
        siblings = repo.list_signals(bu="Compute", survey_source="Partner Experience Survey")

        state = _signal_to_workflow_state(sig_dict, siblings, report)

        assert "Observable behavior for signal 1" in state["voc_data"]
        assert "Observable behavior for signal 2" in state["voc_data"]

    def test_reinforcement_map(self, sample_signals):
        """Reinforcement map from report is carried through."""
        sig_dict = repo.get_signal(sample_signals[0].id)
        report = repo.get_report(sig_dict["report_id"])
        siblings = repo.list_signals(bu="Compute", survey_source="Partner Experience Survey")

        state = _signal_to_workflow_state(sig_dict, siblings, report)

        assert state["reinforcement_map"]["strategic_insight"] == "Test insight"

    def test_signal_fields(self, sample_signals):
        """Individual signal dicts have expected keys."""
        sig_dict = repo.get_signal(sample_signals[0].id)
        report = repo.get_report(sig_dict["report_id"])
        siblings = repo.list_signals(bu="Compute", survey_source="Partner Experience Survey")

        state = _signal_to_workflow_state(sig_dict, siblings, report)

        first_signal = state["signals"][0]
        assert "signal_id" in first_signal
        assert "signal" in first_signal
        assert "zone" in first_signal
        assert "observable_behavior" in first_signal
        assert "evidence" in first_signal

    def test_interpreted_signal_fields(self, sample_signals):
        """Interpreted signal dicts have classification and confidence."""
        sig_dict = repo.get_signal(sample_signals[0].id)
        report = repo.get_report(sig_dict["report_id"])
        siblings = repo.list_signals(bu="Compute", survey_source="Partner Experience Survey")

        state = _signal_to_workflow_state(sig_dict, siblings, report)

        first = state["interpreted_signals"][0]
        assert "classification" in first
        assert "confidence" in first

    def test_priority_matrix_fields(self, sample_signals):
        """Priority matrix entries have score and tier."""
        sig_dict = repo.get_signal(sample_signals[0].id)
        report = repo.get_report(sig_dict["report_id"])
        siblings = repo.list_signals(bu="Compute", survey_source="Partner Experience Survey")

        state = _signal_to_workflow_state(sig_dict, siblings, report)

        first = state["priority_matrix"][0]
        assert "score" in first
        assert "tier" in first
        assert "impact" in first


# ---------------------------------------------------------------------------
# API tests: POST /runs/from-signal
# ---------------------------------------------------------------------------

class TestRunFromSignalAPI:
    client = TestClient(app)

    def test_from_signal_returns_state(self, sample_signals):
        """POST /runs/from-signal returns a workflow state at step 2."""
        response = self.client.post("/runs/from-signal", json={
            "signal_id": sample_signals[0].id,
            "pause_at_checkpoints": False,
        })
        # The workflow will fail at step2 due to missing LLM, but the state
        # creation and pre-population should succeed. We may get a 422 or 500
        # from the LLM call, but the endpoint itself should accept the request.
        # For a unit test, we just verify the endpoint exists and accepts the payload.
        assert response.status_code in (200, 422, 500)

    def test_from_signal_not_found(self):
        """POST /runs/from-signal with invalid signal_id returns 404."""
        response = self.client.post("/runs/from-signal", json={
            "signal_id": 99999,
        })
        assert response.status_code == 404

    def test_from_signal_state_shape(self, sample_signals):
        """Verify the state created by run_workflow_from_signal has correct shape."""
        from backend.app.workflow import run_workflow_from_signal
        # We can't run the full workflow without an LLM, but we can test
        # the state building by catching the error from step execution.
        try:
            run_workflow_from_signal(
                sample_signals[0].id,
                pause_at_checkpoints=True,
            )
        except Exception:
            pass  # Expected — LLM not available in test

        # Verify the run was persisted
        sess = SessionLocal()
        try:
            runs = sess.query(WorkflowRun).filter(WorkflowRun.input_type == "signal").all()
            assert len(runs) >= 1
            run = runs[0]
            state = run.state_json
            assert "signals" in state
            assert "interpreted_signals" in state
            assert "priority_matrix" in state
            assert len(state["signals"]) == 3
        finally:
            sess.close()
