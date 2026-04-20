"""BDD step definitions for LLM error handling scenarios."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from backend.app.nodes.step1_signal_llm import (
    DetectedSignal,
    InterpretedSignal,
    PriorityEntry,
    SignalRecommendation,
    SignalScanResult,
    run_step1_llm,
)
from backend.app.state import BMIWorkflowState

scenarios("features/llm-error-handling.feature")


# ── Shared fixtures ──────────────────────────────────────────────────────

def _minimal_scan_result() -> SignalScanResult:
    """A minimal valid SignalScanResult for mock responses."""
    return SignalScanResult(
        signals=[
            DetectedSignal(
                signal_id="sig_onboarding",
                signal="Customers need faster onboarding",
                zone="Overserved Customers",
                observable_behavior="Customers complain about slow onboarding",
                evidence=["Customers need faster onboarding"],
            ),
        ],
        interpreted_signals=[
            InterpretedSignal(
                signal_id="sig_onboarding",
                signal="Customers need faster onboarding",
                zone="Overserved Customers",
                classification="Sustaining",
                confidence="Medium",
                rationale="Onboarding friction is common.",
                alternative_explanation="May be a temporary spike.",
                key_evidence_gap="Volume data missing.",
            ),
        ],
        priority_matrix=[
            PriorityEntry(
                signal_id="sig_onboarding",
                signal="Customers need faster onboarding",
                impact=2,
                speed=2,
                score=4,
                tier="Investigate",
                rationale="Moderate priority.",
            ),
        ],
        recommendations=[
            SignalRecommendation(
                signal_id="sig_onboarding",
                action_tier="Investigate",
                what_we_know="Onboarding is slow.",
                what_we_dont_know=["How many customers are affected"],
                experiment_candidate="We believe that faster onboarding improves retention.",
            ),
        ],
        agent_recommendation="Investigate onboarding friction.",
    )


@given(parsers.parse('a workflow state with VoC data "{voc_data}"'), target_fixture="workflow_state")
def workflow_state(voc_data: str) -> BMIWorkflowState:
    return {
        "session_id": "session-llm-err",
        "current_step": "ingest",
        "input_type": "text",
        "llm_backend": "azure",
        "voc_data": voc_data,
    }


# ── LLM mock configurations ─────────────────────────────────────────────

@given("the LLM is configured to fail on the first call then succeed", target_fixture="llm_mock")
def llm_fail_then_succeed() -> MagicMock:
    """Create a mock LLM whose structured invoke fails once then succeeds."""
    mock_llm = MagicMock()
    structured_mock = MagicMock()
    structured_mock.invoke = MagicMock(
        side_effect=[RuntimeError("Transient LLM failure"), _minimal_scan_result()]
    )
    mock_llm.with_structured_output.return_value = structured_mock
    return mock_llm


@given("the LLM is configured to always fail", target_fixture="llm_mock")
def llm_always_fail() -> MagicMock:
    """Create a mock LLM that always raises on invoke."""
    mock_llm = MagicMock()
    structured_mock = MagicMock()
    structured_mock.invoke = MagicMock(side_effect=RuntimeError("Permanent LLM failure"))
    mock_llm.with_structured_output.return_value = structured_mock
    return mock_llm


# ── When steps ───────────────────────────────────────────────────────────

@when("the Step 1 signal scanner node runs", target_fixture="step1_result")
def step1_runs(workflow_state: BMIWorkflowState, llm_mock: MagicMock) -> BMIWorkflowState:
    return run_step1_llm(workflow_state, llm_mock)


@when("the Step 1 signal scanner node runs expecting failure", target_fixture="step1_error")
def step1_runs_expecting_failure(workflow_state: BMIWorkflowState, llm_mock: MagicMock) -> Exception:
    with pytest.raises(Exception) as exc_info:
        run_step1_llm(workflow_state, llm_mock)
    return exc_info.value


# ── Then steps ───────────────────────────────────────────────────────────

@then("the workflow state contains a signals list")
def assert_signals_list(step1_result: BMIWorkflowState) -> None:
    assert isinstance(step1_result.get("signals"), list)
    assert len(step1_result["signals"]) > 0


@then(parsers.parse("the LLM was called exactly {count:d} times"))
def assert_llm_call_count(llm_mock: MagicMock, count: int) -> None:
    structured_mock = llm_mock.with_structured_output.return_value
    assert structured_mock.invoke.call_count == count


@then("the error message indicates an LLM failure")
def assert_error_indicates_llm_failure(step1_error: Exception) -> None:
    msg = str(step1_error).lower()
    assert "llm" in msg or "failure" in msg or "failed" in msg, f"Expected LLM failure message, got: {step1_error}"


@then("the error message names the step that failed")
def assert_error_names_step(step1_error: Exception) -> None:
    msg = str(step1_error).lower()
    assert "step" in msg or "signal" in msg or "step1" in msg or "step 1" in msg, (
        f"Expected step name in error, got: {step1_error}"
    )
