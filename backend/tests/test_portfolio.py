"""Tests for the portfolio computation service and API endpoints."""

import os
import pytest
from unittest.mock import MagicMock
from datetime import datetime, timezone

from backend.app.services.portfolio_service import (
    compute_risk_score,
    compute_return_score,
    build_portfolio_entry,
    _quadrant_label,
)


# ---------------------------------------------------------------------------
# compute_risk_score
# ---------------------------------------------------------------------------

class TestComputeRiskScore:
    def test_none_state_returns_50(self):
        assert compute_risk_score(None) == 50.0

    def test_empty_state_returns_fallback(self):
        score = compute_risk_score({})
        # No step7 data, no current_step → defaults to step1a fallback
        assert 50 <= score <= 100

    def test_with_dvf_assumptions_test_first(self):
        """All 'Test first' + 'None' evidence → high risk."""
        state = {
            "step7_structured": {
                "categories": [
                    {
                        "category": "Desirability",
                        "assumptions": [
                            {"suggested_quadrant": "Test first", "voc_evidence_strength": "None"},
                            {"suggested_quadrant": "Test first", "voc_evidence_strength": "None"},
                        ],
                    }
                ]
            }
        }
        score = compute_risk_score(state)
        assert score > 60, f"Expected high risk, got {score}"

    def test_with_dvf_assumptions_safe_zone(self):
        """All 'Safe zone' + 'Medium' evidence → low risk."""
        state = {
            "step7_structured": {
                "categories": [
                    {
                        "category": "Feasibility",
                        "assumptions": [
                            {"suggested_quadrant": "Safe zone", "voc_evidence_strength": "Medium"},
                            {"suggested_quadrant": "Safe zone", "voc_evidence_strength": "Medium"},
                        ],
                    }
                ]
            }
        }
        score = compute_risk_score(state)
        assert score < 30, f"Expected low risk, got {score}"

    def test_invent_adds_risk_bonus(self):
        state_base = {
            "step7_structured": {
                "categories": [
                    {
                        "category": "Viability",
                        "assumptions": [
                            {"suggested_quadrant": "Monitor", "voc_evidence_strength": "Weak"},
                        ],
                    }
                ]
            }
        }
        score_shift = compute_risk_score({**state_base, "pattern_direction": "shift"})
        score_invent = compute_risk_score({**state_base, "pattern_direction": "invent"})
        assert score_invent > score_shift, "Invent should have higher risk than shift"

    def test_fallback_early_step_higher_risk(self):
        early = compute_risk_score({"current_step": "step1a_signal_scan"})
        late = compute_risk_score({"current_step": "step8_pdsa"})
        assert early > late, "Earlier steps should have higher estimated risk"


# ---------------------------------------------------------------------------
# compute_return_score
# ---------------------------------------------------------------------------

class TestComputeReturnScore:
    def test_none_state_returns_50(self):
        assert compute_return_score(None) == 50.0

    def test_empty_state_returns_50(self):
        assert compute_return_score({}) == 50.0

    def test_all_high_rankings(self):
        state = {
            "vp_rankings": [
                {
                    "coverage_score": "High",
                    "differentiation_score": "High",
                    "evidence_score": "High",
                }
            ]
        }
        score = compute_return_score(state)
        assert score == 100.0

    def test_all_low_rankings(self):
        state = {
            "vp_rankings": [
                {
                    "coverage_score": "Low",
                    "differentiation_score": "Low",
                    "evidence_score": "Low",
                }
            ]
        }
        score = compute_return_score(state)
        assert round(score, 1) == round((3 / 9) * 100, 1)

    def test_picks_best_vp(self):
        """Should use the best-scoring VP, not average."""
        state = {
            "vp_rankings": [
                {"coverage_score": "Low", "differentiation_score": "Low", "evidence_score": "Low"},
                {"coverage_score": "High", "differentiation_score": "High", "evidence_score": "High"},
            ]
        }
        score = compute_return_score(state)
        assert score == 100.0


# ---------------------------------------------------------------------------
# _quadrant_label
# ---------------------------------------------------------------------------

class TestQuadrantLabel:
    def test_explore(self):
        # High risk (>50) + low return → Explore (bottom-left on reversed axis)
        assert _quadrant_label(70, 30) == "explore"

    def test_exploit(self):
        # Low risk (≤50) + high return → Exploit (top-right on reversed axis)
        assert _quadrant_label(30, 70) == "exploit"

    def test_explore_high_return(self):
        # High risk + high return → Explore with promising ROI
        assert _quadrant_label(60, 60) == "explore-high-return"

    def test_exploit_low_return(self):
        # Low risk + low return → validated but low ROI
        assert _quadrant_label(30, 30) == "exploit-low-return"


# ---------------------------------------------------------------------------
# build_portfolio_entry
# ---------------------------------------------------------------------------

class TestBuildPortfolioEntry:
    def _make_run(self, **overrides):
        run = MagicMock()
        run.session_id = overrides.get("session_id", "test-session-1")
        run.session_name = overrides.get("session_name", "Test Initiative")
        run.status = overrides.get("status", "paused")
        run.current_step = overrides.get("current_step", "step3_profile")
        run.created_at = overrides.get("created_at", datetime(2026, 1, 1, tzinfo=timezone.utc))
        run.updated_at = overrides.get("updated_at", datetime(2026, 1, 15, tzinfo=timezone.utc))
        run.state_json = overrides.get("state_json", {})
        run.portfolio_json = overrides.get("portfolio_json", None)
        return run

    def test_basic_entry(self):
        run = self._make_run()
        entry = build_portfolio_entry(run)
        assert entry["session_id"] == "test-session-1"
        assert entry["initiative_name"] == "Test Initiative"
        assert entry["status"] == "paused"
        assert "risk_score" in entry
        assert "return_score" in entry
        assert "quadrant" in entry

    def test_portfolio_json_overrides(self):
        run = self._make_run(
            portfolio_json={
                "initiative_name": "Custom Name",
                "expected_revenue": "$500M",
                "testing_cost": "$10K",
                "risk_score_override": 80.0,
                "return_score_override": 90.0,
                "notes": "High priority",
            }
        )
        entry = build_portfolio_entry(run)
        assert entry["initiative_name"] == "Custom Name"
        assert entry["expected_revenue"] == "$500M"
        assert entry["testing_cost"] == "$10K"
        assert entry["risk_score"] == 80.0
        assert entry["return_score"] == 90.0
        assert entry["notes"] == "High priority"

    def test_days_running(self):
        run = self._make_run(
            created_at=datetime(2026, 4, 1, tzinfo=timezone.utc)
        )
        entry = build_portfolio_entry(run)
        assert entry["days_running"] >= 0

    def test_counts_assumptions(self):
        state = {
            "step7_structured": {
                "categories": [
                    {"category": "D", "assumptions": [{"suggested_quadrant": "Monitor"}]},
                    {"category": "V", "assumptions": [{"suggested_quadrant": "Test first"}, {"suggested_quadrant": "Safe zone"}]},
                ]
            }
        }
        run = self._make_run(state_json=state)
        entry = build_portfolio_entry(run)
        assert entry["assumption_count"] == 3

    def test_counts_experiments(self):
        state = {"experiment_cards": [{"name": "A"}, {"name": "B"}]}
        run = self._make_run(state_json=state)
        entry = build_portfolio_entry(run)
        assert entry["experiment_count"] == 2
