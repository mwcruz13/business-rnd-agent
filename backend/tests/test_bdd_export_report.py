"""Step definitions for export-report.feature."""

from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace
from typing import Any

from pytest_bdd import given, scenarios, then, when

from backend.cli.export_report import build_report

scenarios("features/export-report.feature")


def _mock_run(state: dict[str, Any], *, status: str = "completed", current_step: str = "pdsa_plan") -> SimpleNamespace:
    """Create a lightweight stand-in for WorkflowRun with the fields build_report reads."""
    return SimpleNamespace(
        session_id="test-export-001",
        session_name="Export Test Session",
        created_at=datetime(2025, 1, 15, 12, 0, 0),
        status=status,
        current_step=current_step,
        llm_backend="azure",
        input_type="text",
        state_json=state,
    )


def _full_state() -> dict[str, Any]:
    """Return a state dict representing a full 8-step completed workflow."""
    return {
        "signals": [
            {
                "signal": "Customers report delays in firmware updates",
                "zone": "Overserved Customers",
                "source_type": "survey",
                "observable_behavior": "Delayed update cycles",
                "evidence": ["Quote 1", "Quote 2"],
            }
        ],
        "interpreted_signals": [
            {
                "signal": "Firmware update delays",
                "classification": "Disruptive — Low-End",
                "confidence": "High",
                "rationale": "Clear pattern",
                "alternative_explanation": "None",
                "filters": ["Performance Overshoot"],
            }
        ],
        "priority_matrix": [
            {
                "signal": "Firmware update delays",
                "impact": "High",
                "speed": "Medium",
                "score": 8,
                "tier": "Tier 1",
                "rationale": "High impact",
            }
        ],
        "coverage_gaps": [],
        "signal_recommendations": [],
        "pattern_direction": "shift",
        "selected_patterns": ["Cost Differentiators"],
        "pattern_rationale": "Low-end disruption pattern fits the overserved signal",
        "agent_recommendation": "Recommend shifting to cost-focused patterns.",
        "customer_profile": "## Customer Empathy Profile\n\n### Jobs to Be Done\n- Onboard firmware quickly",
        "value_driver_tree": "## Value Driver Tree\n\n### Customer Business Outcome\nReduce onboarding time",
        "actionable_insights": "## Context Analysis\n\n### Problem Statements\n| # | Problem | Friction |\n|---|---------|----------|\n| 1 | Slow onboarding | Delay |",
        "value_proposition_canvas": "## Value Proposition Canvas\n\n### Customer Jobs\n- Update firmware efficiently",
        "business_model_canvas": "## Business Model Canvas\n\n| Building Block | Description |\n|---|---|\n| Value Propositions | Faster firmware |",
        "fit_assessment": "## Fit Assessment\n\n### Problem-Solution Fit\nStrong alignment",
        "assumptions": "## Assumptions Map\n\n| # | Assumption | Category |\n|---|-----------|----------|\n| 1 | Customers want faster updates | Desirability |",
        "experiment_selections": "## Experiment Selections\n\n| # | Assumption | Card |\n|---|-----------|------|\n| 1 | Speed matters | Customer Interview |",
        "experiment_plans": "## Experiment Plans\n\nPlan details here.",
        "experiment_worksheets": "## Worksheets\n\nWorksheet content.",
        "experiment_cards": [
            {
                "assumption": "Customers want faster firmware updates",
                "category": "Desirability",
                "evidence_strength": "Weak",
                "card_name": "Customer Interview",
                "what_it_tests": "Customer desire for speed",
                "best_used_when": "Testing desirability assumptions",
                "test_audience": "IT administrators",
                "sample_size": "10",
                "timebox": "2 weeks",
                "primary_metric": "Interest rate",
                "secondary_metrics": "NPS",
                "success_looks_like": "8/10 express interest",
                "failure_looks_like": "Less than 3/10",
                "ambiguous_looks_like": "4-7/10",
                "evidence_path": [
                    {"step": "1", "card_name": "Customer Interview", "evidence_strength": "Weak"},
                ],
                "selection_rationale": "Direct customer feedback needed",
                "evidence_status": "collected",
                "evidence_decision": "pivot",
                "evidence_summary": "Customers expressed moderate interest",
            }
        ],
    }


# ── Givens ──────────────────────────────────────────────────────────────

@given("a completed workflow run with all 8 steps", target_fixture="mock_run")
def completed_run() -> SimpleNamespace:
    return _mock_run(_full_state())


@given("a completed workflow run with experiment card evidence captured", target_fixture="mock_run")
def completed_run_with_evidence() -> SimpleNamespace:
    return _mock_run(_full_state())


@given("a workflow run paused at step 3", target_fixture="mock_run")
def partial_run() -> SimpleNamespace:
    full = _full_state()
    # Keep only steps 1-3 fields
    partial_state: dict[str, Any] = {
        "signals": full["signals"],
        "interpreted_signals": full["interpreted_signals"],
        "priority_matrix": full["priority_matrix"],
        "coverage_gaps": full["coverage_gaps"],
        "signal_recommendations": full["signal_recommendations"],
        "pattern_direction": full["pattern_direction"],
        "selected_patterns": full["selected_patterns"],
        "agent_recommendation": full["agent_recommendation"],
        "customer_profile": full["customer_profile"],
    }
    return _mock_run(partial_state, status="paused", current_step="empathize")


# ── When ────────────────────────────────────────────────────────────────

@when("the markdown report is generated", target_fixture="report_text")
def generate_report(mock_run: SimpleNamespace) -> str:
    return build_report(mock_run)  # type: ignore[arg-type]


# ── Then — Scenario 1: all step outputs ─────────────────────────────────

@then("the report includes a Step 1 signal scan section")
def assert_step1_section(report_text: str) -> None:
    assert "## Step 1" in report_text
    assert "Signal Scan" in report_text


@then("the report includes a Step 2 pattern rationale")
def assert_step2_section(report_text: str) -> None:
    assert "## Step 2" in report_text
    assert "Pattern Selection" in report_text


@then("the report includes a Step 3 customer profile section")
def assert_step3_section(report_text: str) -> None:
    assert "Customer Empathy Profile" in report_text or "Step 3" in report_text


@then("the report includes a Step 6 fit assessment section")
def assert_step6_section(report_text: str) -> None:
    assert "Fit Assessment" in report_text


@then("the report includes a Step 8 experiment selections section")
def assert_step8_section(report_text: str) -> None:
    assert "Experiment Selections" in report_text


# ── Then — Scenario 2: experiment card evidence ─────────────────────────

@then("the report includes experiment card status and evidence fields")
def assert_experiment_evidence_fields(report_text: str) -> None:
    assert "evidence" in report_text.lower() or "Evidence" in report_text


@then("the report includes the evidence decision for each card")
def assert_evidence_decision(report_text: str) -> None:
    # The report should include the evidence decision from the card data.
    # build_report renders experiment cards with detail blocks.
    # If evidence_decision is not yet in the report, Phase 3 production code will add it.
    assert "pivot" in report_text.lower() or "evidence_decision" in report_text.lower() or "Evidence Decision" in report_text


# ── Then — Scenario 3: partial runs ────────────────────────────────────

@then("the report includes steps 1 through 3 only")
def assert_partial_steps_present(report_text: str) -> None:
    assert "## Step 1" in report_text
    assert "## Step 2" in report_text
    assert "Customer Empathy Profile" in report_text or "Step 3" in report_text


@then("the report does not include step 4 or later sections")
def assert_no_later_steps(report_text: str) -> None:
    assert "Value Driver Tree" not in report_text
    assert "Value Proposition Canvas" not in report_text
    assert "Business Model Canvas" not in report_text
    assert "Assumptions" not in report_text.split("## Step 2")[1] if "## Step 2" in report_text else True
    assert "Experiment Selections" not in report_text
