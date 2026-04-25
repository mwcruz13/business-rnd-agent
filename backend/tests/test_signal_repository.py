"""Tests for the signal repository service and API endpoints."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.db.models import Base, SignalRecord, SignalReport
from backend.app.db.session import SessionLocal, engine
from backend.app.main import app


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _setup_signal_tables():
    """Ensure signal tables exist before each test and clean up after."""
    Base.metadata.create_all(engine, tables=[
        SignalReport.__table__,
        SignalRecord.__table__,
    ])
    yield
    sess = SessionLocal()
    try:
        sess.query(SignalRecord).delete()
        sess.query(SignalReport).delete()
        sess.commit()
    finally:
        sess.close()


@pytest.fixture()
def sample_report() -> dict:
    from backend.app.services.signal_repository import upsert_report
    report = upsert_report(
        bu="Compute",
        survey_source="Transactional Service Experience Survey",
        title="SOC Radar — Compute",
        input_stats={"total_candidates": 100, "selected_comments": 10},
        source_file="test/soc_voc_compute_analyst.json",
        report_date="2026-04-25",
    )
    return {"id": report.id, "bu": report.bu, "source_file": report.source_file}


@pytest.fixture()
def sample_signals(sample_report) -> list[int]:
    from backend.app.services.signal_repository import upsert_signal
    ids = []
    for i in range(1, 4):
        rec = upsert_signal(
            report_id=sample_report["id"],
            signal_id=i,
            signal_title=f"Test signal {i}",
            bu="Compute",
            survey_source="Transactional Service Experience Survey",
            signal_zone="Overserved Customers" if i < 3 else "Low-End Foothold",
            full_analysis={"phase_1_scan": {"id": i, "signal": f"Test signal {i}"}},
            classification="Sustaining" if i < 3 else "Disruptive",
            action_tier="Act" if i == 1 else "Investigate",
            priority_score=10 - i,
        )
        ids.append(rec.id)
    return ids


# ---------------------------------------------------------------------------
# Service-level tests
# ---------------------------------------------------------------------------


class TestSignalRepositoryService:
    def test_upsert_report_creates_new(self, sample_report):
        assert sample_report["id"] is not None
        assert sample_report["bu"] == "Compute"

    def test_upsert_report_updates_existing(self, sample_report):
        from backend.app.services.signal_repository import upsert_report
        updated = upsert_report(
            bu="Compute-Updated",
            survey_source="Updated Survey",
            title="Updated Title",
            input_stats={"updated": True},
            source_file="test/soc_voc_compute_analyst.json",
        )
        assert updated.id == sample_report["id"]
        assert updated.bu == "Compute-Updated"

    def test_get_report(self, sample_report):
        from backend.app.services.signal_repository import get_report
        result = get_report(sample_report["id"])
        assert result["bu"] == "Compute"
        assert result["report_date"] == "2026-04-25"

    def test_get_report_not_found(self):
        from backend.app.services.signal_repository import get_report
        with pytest.raises(ValueError, match="not found"):
            get_report(999999)

    def test_list_reports(self, sample_report):
        from backend.app.services.signal_repository import list_reports
        reports = list_reports()
        assert len(reports) >= 1
        assert any(r["id"] == sample_report["id"] for r in reports)

    def test_upsert_signal_creates_new(self, sample_signals):
        assert len(sample_signals) == 3

    def test_upsert_signal_updates_existing(self, sample_report):
        from backend.app.services.signal_repository import upsert_signal
        rec1 = upsert_signal(
            report_id=sample_report["id"],
            signal_id=100,
            signal_title="Original",
            bu="Compute",
            survey_source="Transactional Service Experience Survey",
            signal_zone="Overserved Customers",
            full_analysis={"version": 1},
        )
        rec2 = upsert_signal(
            report_id=sample_report["id"],
            signal_id=100,
            signal_title="Updated",
            bu="Compute",
            survey_source="Transactional Service Experience Survey",
            signal_zone="Low-End Foothold",
            full_analysis={"version": 2},
        )
        assert rec2.id == rec1.id
        assert rec2.signal_title == "Updated"

    def test_get_signal(self, sample_signals):
        from backend.app.services.signal_repository import get_signal
        result = get_signal(sample_signals[0])
        assert result["signal_title"] == "Test signal 1"

    def test_list_signals_filter_by_bu(self, sample_signals):
        from backend.app.services.signal_repository import list_signals
        results = list_signals(bu="Compute")
        assert len(results) == 3

    def test_list_signals_filter_by_classification(self, sample_signals):
        from backend.app.services.signal_repository import list_signals
        results = list_signals(classification="Disruptive")
        assert len(results) == 1
        assert results[0]["signal_title"] == "Test signal 3"

    def test_get_bu_summary(self, sample_signals):
        from backend.app.services.signal_repository import get_bu_summary
        summary = get_bu_summary()
        assert len(summary) >= 1
        compute_row = next(s for s in summary if s["bu"] == "Compute")
        assert compute_row["signal_count"] == 3


# ---------------------------------------------------------------------------
# API endpoint tests
# ---------------------------------------------------------------------------


class TestSignalAPI:
    def test_get_summary(self, sample_signals):
        client = TestClient(app)
        response = client.get("/signals/summary")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert any(row["bu"] == "Compute" for row in data)

    def test_list_signals(self, sample_signals):
        client = TestClient(app)
        response = client.get("/signals")
        assert response.status_code == 200
        assert len(response.json()) >= 3

    def test_list_signals_filter(self, sample_signals):
        client = TestClient(app)
        response = client.get("/signals", params={"bu": "Compute", "classification": "Disruptive"})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["classification"] == "Disruptive"

    def test_get_signal_by_id(self, sample_signals):
        client = TestClient(app)
        response = client.get(f"/signals/{sample_signals[0]}")
        assert response.status_code == 200
        assert response.json()["signal_title"] == "Test signal 1"

    def test_get_signal_not_found(self):
        client = TestClient(app)
        response = client.get("/signals/999999")
        assert response.status_code == 404

    def test_list_reports(self, sample_report):
        client = TestClient(app)
        response = client.get("/signals/reports")
        assert response.status_code == 200
        assert len(response.json()) >= 1

    def test_get_report_by_id(self, sample_report):
        client = TestClient(app)
        response = client.get(f"/signals/reports/{sample_report['id']}")
        assert response.status_code == 200
        assert response.json()["bu"] == "Compute"

    def test_get_report_not_found(self):
        client = TestClient(app)
        response = client.get("/signals/reports/999999")
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Ingestion script tests
# ---------------------------------------------------------------------------


class TestIngestionScript:
    def test_ingest_file(self, tmp_path):
        """Test ingesting a single analyst JSON file."""
        from backend.scripts.ingest_signals import ingest_file

        analyst_json = {
            "report": {
                "title": "Test Radar — Compute",
                "source": "Test Survey",
                "bu": "Compute",
                "date": "2026-04-25",
                "input_stats": {"total_candidates": 50, "selected_comments": 5},
            },
            "phase_1_scan": {
                "signals": [
                    {
                        "id": 1,
                        "signal": "Test signal alpha",
                        "signal_zone": "Overserved Customers",
                        "source_type": "Internal VoC",
                        "observable_behavior": "Customers report delays.",
                        "supporting_comments": [1, 2],
                    },
                    {
                        "id": 2,
                        "signal": "Test signal beta",
                        "signal_zone": "Low-End Foothold",
                        "source_type": "Internal VoC",
                        "observable_behavior": "Competitor gaining share.",
                        "supporting_comments": [3],
                    },
                ],
                "coverage_gaps": [],
            },
            "phase_2_interpret": {
                "assessments": [
                    {"signal_id": 1, "signal": "Test signal alpha", "classification": "Sustaining"},
                    {"signal_id": 2, "signal": "Test signal beta", "classification": "Disruptive"},
                ],
            },
            "phase_3_prioritize": {
                "priority_matrix": [
                    {"signal_id": 1, "signal": "Test signal alpha", "classification": "Sustaining", "priority_score": 8, "action_tier": "Act"},
                    {"signal_id": 2, "signal": "Test signal beta", "classification": "Disruptive", "priority_score": 9, "action_tier": "Investigate"},
                ],
            },
            "phase_4_recommend": {
                "act_signals": [
                    {"signal_id": 1, "signal": "Test signal alpha", "action_tier": "Act", "what_we_know": "x", "next_steps": "y"},
                ],
                "investigate_signals": [
                    {"signal_id": 2, "signal": "Test signal beta", "action_tier": "Investigate", "what_we_know": "a", "next_steps": "b"},
                ],
                "watching_briefs": [],
            },
        }

        filepath = tmp_path / "backend" / "scripts" / "data" / "soc_extracts_service" / "signal_results" / "soc_voc_compute_analyst.json"
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(json.dumps(analyst_json))

        count = ingest_file(filepath, "Test Survey")
        assert count == 2

        from backend.app.services.signal_repository import list_signals
        signals = list_signals(bu="Compute", survey_source="Test Survey")
        assert len(signals) == 2
        titles = {s["signal_title"] for s in signals}
        assert "Test signal alpha" in titles
        assert "Test signal beta" in titles

        # Verify phase data was captured
        alpha = next(s for s in signals if s["signal_title"] == "Test signal alpha")
        assert alpha["classification"] == "Sustaining"
        assert alpha["action_tier"] == "Act"
        assert alpha["priority_score"] == 8
        assert "phase_2_interpret" in alpha["full_analysis"]
        assert "phase_4_recommend" in alpha["full_analysis"]
