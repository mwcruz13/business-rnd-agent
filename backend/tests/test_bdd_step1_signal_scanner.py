from pathlib import Path

from pytest_bdd import given, parsers, scenarios, then, when

from backend.app.nodes.step1_signal import run_step
from backend.app.state import BMIWorkflowState


scenarios("features/step1-signal-scanner.feature")


FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"


@given(parsers.parse('a workflow state with VoC data "{voc_data}"'), target_fixture="workflow_state")
def workflow_state(voc_data: str) -> BMIWorkflowState:
    return {
        "session_id": "session-001",
        "current_step": "ingest",
        "input_type": "text",
        "llm_backend": "azure",
        "voc_data": voc_data,
    }


@given("a workflow state with the firmware assessment VoC sample", target_fixture="workflow_state")
def firmware_assessment_workflow_state() -> BMIWorkflowState:
    return {
        "session_id": "session-001b",
        "current_step": "ingest",
        "input_type": "text",
        "llm_backend": "azure",
        "voc_data": (FIXTURE_DIR / "firmware_assessment_sample.txt").read_text(encoding="utf-8"),
    }


@when("the Step 1 signal scanner node runs", target_fixture="step1_result")
def step1_result(workflow_state: BMIWorkflowState) -> BMIWorkflowState:
    return run_step(workflow_state)


@then(parsers.parse('the workflow current step is "{expected_step}"'))
def assert_current_step(step1_result: BMIWorkflowState, expected_step: str) -> None:
    assert step1_result["current_step"] == expected_step


@then("the original VoC data is preserved in the workflow state")
def assert_voc_data_preserved(workflow_state: BMIWorkflowState, step1_result: BMIWorkflowState) -> None:
    assert step1_result["voc_data"] == workflow_state["voc_data"]


@then("the workflow state contains a signals list")
def assert_signals_list(step1_result: BMIWorkflowState) -> None:
    assert isinstance(step1_result.get("signals"), list)


@then("the workflow state contains an interpreted signals list")
def assert_interpreted_signals_list(step1_result: BMIWorkflowState) -> None:
    assert isinstance(step1_result.get("interpreted_signals"), list)


@then("the workflow state contains a priority matrix list")
def assert_priority_matrix_list(step1_result: BMIWorkflowState) -> None:
    assert isinstance(step1_result.get("priority_matrix"), list)


@then("the workflow state contains an agent recommendation")
def assert_agent_recommendation(step1_result: BMIWorkflowState) -> None:
    assert isinstance(step1_result.get("agent_recommendation"), str)
    assert step1_result["agent_recommendation"]


@then(parsers.parse('the first detected signal uses the zone "{expected_zone}"'))
def assert_first_signal_zone(step1_result: BMIWorkflowState, expected_zone: str) -> None:
    signals = step1_result.get("signals") or []
    assert signals
    assert signals[0]["zone"] == expected_zone


@then(parsers.parse('the first interpreted signal uses the classification "{expected_classification}"'))
def assert_first_interpreted_signal_classification(
    step1_result: BMIWorkflowState, expected_classification: str
) -> None:
    interpreted_signals = step1_result.get("interpreted_signals") or []
    assert interpreted_signals
    assert interpreted_signals[0]["classification"] == expected_classification


@then("every interpreted signal only uses SOC Radar filter names")
def assert_interpreted_signal_uses_soc_filters(step1_result: BMIWorkflowState) -> None:
    interpreted_signals = step1_result.get("interpreted_signals") or []
    assert interpreted_signals
    valid_filters = {
        "Asymmetric Motivation",
        "Asymmetric Skills",
        "Trajectory",
        "Performance Overshoot",
        "Barrier Removal",
        "Business Model Conflict",
    }
    for signal in interpreted_signals:
        filters = signal.get("filters") or []
        assert all(filter_name in valid_filters for filter_name in filters)


@then(parsers.parse("the workflow state contains at least {minimum_count:d} detected signals"))
def assert_detected_signal_count(step1_result: BMIWorkflowState, minimum_count: int) -> None:
    signals = step1_result.get("signals") or []
    assert len(signals) >= minimum_count


@then(parsers.parse('the detected signals include "{expected_signal}"'))
def assert_detected_signal_present(step1_result: BMIWorkflowState, expected_signal: str) -> None:
    signals = step1_result.get("signals") or []
    assert any(signal.get("signal") == expected_signal for signal in signals)


@then(parsers.parse("the first priority matrix entry has a score of {expected_score:d}"))
def assert_priority_score(step1_result: BMIWorkflowState, expected_score: int) -> None:
    priority_matrix = step1_result.get("priority_matrix") or []
    assert priority_matrix
    assert priority_matrix[0]["score"] == expected_score


@then(parsers.parse('the first priority matrix entry uses the tier "{expected_tier}"'))
def assert_priority_tier(step1_result: BMIWorkflowState, expected_tier: str) -> None:
    priority_matrix = step1_result.get("priority_matrix") or []
    assert priority_matrix
    assert priority_matrix[0]["tier"] == expected_tier


@then("the workflow state contains coverage gaps")
def assert_coverage_gaps(step1_result: BMIWorkflowState) -> None:
    coverage_gaps = step1_result.get("coverage_gaps") or []
    assert isinstance(coverage_gaps, list)
    assert coverage_gaps


def test_competitor_self_serve_evidence_avoids_generic_slogans() -> None:
    state: BMIWorkflowState = {
        "session_id": "session-001c",
        "current_step": "ingest",
        "input_type": "text",
        "llm_backend": "azure",
        "voc_data": (FIXTURE_DIR / "firmware_assessment_sample.txt").read_text(encoding="utf-8"),
    }

    result = run_step(state)
    competitor_signal = next(
        signal for signal in result["signals"] if signal["signal_id"] == "competitor_self_serve"
    )

    evidence = competitor_signal.get("evidence") or []
    assert evidence
    assert "Meet or beat our competitors" not in evidence