from pathlib import Path

from pytest_bdd import given, parsers, scenarios, then, when

from backend.app.config import get_settings
from backend.app.llm.factory import get_chat_model
from backend.app.llm.judge import JudgeVerdict, evaluate_step1_quality
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
        # Filters may be a list of strings (legacy) or list of dicts (new schema)
        filter_names = [
            f["filter_name"] if isinstance(f, dict) else f
            for f in filters
        ]
        invalid = [f for f in filter_names if f not in valid_filters]
        assert not invalid, (
            f"Invalid filter(s) {invalid} for signal '{signal.get('signal_id')}'. "
            f"Valid filters: {valid_filters}"
        )


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


@then("every signal zone is a valid SOC Radar zone")
def assert_valid_signal_zones(step1_result: BMIWorkflowState) -> None:
    valid_zones = {
        "Nonconsumption",
        "Overserved Customers",
        "Low-End Foothold",
        "New-Market Foothold",
        "Business Model Anomaly",
        "Enabling Technology",
        "Regulatory / Policy Shift",
        # Accept abbreviated forms the LLM may produce
        "Enabling Tech",
        "Overserved",
        "Regulatory Shift",
    }
    signals = step1_result.get("signals") or []
    assert signals
    for signal in signals:
        assert signal["zone"] in valid_zones, (
            f"Invalid zone '{signal['zone']}' for signal '{signal.get('signal_id')}'"
        )


@then("every interpreted signal uses a valid classification")
def assert_valid_classifications(step1_result: BMIWorkflowState) -> None:
    valid_classifications = {
        "Sustaining",
        "Disruptive — New-Market",
        "Disruptive — Low-End",
        # Accept variants the LLM may produce
        "Disruptive - New-Market",
        "Disruptive - Low-End",
    }
    interpreted = step1_result.get("interpreted_signals") or []
    assert interpreted
    for signal in interpreted:
        assert signal["classification"] in valid_classifications, (
            f"Invalid classification '{signal['classification']}' "
            f"for signal '{signal.get('signal_id')}'"
        )


@then("every priority score equals impact times speed")
def assert_priority_score_calculation(step1_result: BMIWorkflowState) -> None:
    priority_matrix = step1_result.get("priority_matrix") or []
    assert priority_matrix
    for entry in priority_matrix:
        expected = entry["impact"] * entry["speed"]
        assert entry["score"] == expected, (
            f"Score {entry['score']} != impact({entry['impact']}) * speed({entry['speed']}) "
            f"for signal '{entry.get('signal_id')}'"
        )


@then("every priority tier matches its score range")
def assert_priority_tier_matches_score(step1_result: BMIWorkflowState) -> None:
    priority_matrix = step1_result.get("priority_matrix") or []
    assert priority_matrix
    for entry in priority_matrix:
        score = entry["score"]
        tier = entry["tier"]
        if score >= 7:
            assert tier == "Act", f"Score {score} should be Act, got {tier}"
        elif score >= 4:
            assert tier == "Investigate", f"Score {score} should be Investigate, got {tier}"
        else:
            assert tier == "Monitor", f"Score {score} should be Monitor, got {tier}"


@then("the workflow state contains coverage gaps")
def assert_coverage_gaps(step1_result: BMIWorkflowState) -> None:
    coverage_gaps = step1_result.get("coverage_gaps") or []
    assert isinstance(coverage_gaps, list)
    assert coverage_gaps


# ---------------------------------------------------------------------------
# LLM-as-Judge step definitions
# ---------------------------------------------------------------------------

@when(
    "the LLM judge evaluates the signal scan against the SOC Radar SKILL",
    target_fixture="judge_verdict",
)
def judge_verdict(workflow_state: BMIWorkflowState, step1_result: BMIWorkflowState) -> JudgeVerdict:
    settings = get_settings()
    settings.llm_backend = workflow_state.get("llm_backend", settings.llm_backend)
    llm = get_chat_model(settings)
    voc_text = str(workflow_state.get("voc_data", ""))
    step1_output = {
        "signals": step1_result.get("signals", []),
        "interpreted_signals": step1_result.get("interpreted_signals", []),
        "priority_matrix": step1_result.get("priority_matrix", []),
        "coverage_gaps": step1_result.get("coverage_gaps", []),
        "agent_recommendation": step1_result.get("agent_recommendation", ""),
    }
    return evaluate_step1_quality(voc_text, step1_output, llm)


@then(parsers.parse("the judge completeness score is at least {threshold:d}"))
def assert_judge_completeness(judge_verdict: JudgeVerdict, threshold: int) -> None:
    assert judge_verdict.completeness.score >= threshold, (
        f"Completeness {judge_verdict.completeness.score} < {threshold}: "
        f"{judge_verdict.completeness.rationale}"
    )


@then(parsers.parse("the judge relevance score is at least {threshold:d}"))
def assert_judge_relevance(judge_verdict: JudgeVerdict, threshold: int) -> None:
    assert judge_verdict.relevance.score >= threshold, (
        f"Relevance {judge_verdict.relevance.score} < {threshold}: "
        f"{judge_verdict.relevance.rationale}"
    )


@then(parsers.parse("the judge groundedness score is at least {threshold:d}"))
def assert_judge_groundedness(judge_verdict: JudgeVerdict, threshold: int) -> None:
    assert judge_verdict.groundedness.score >= threshold, (
        f"Groundedness {judge_verdict.groundedness.score} < {threshold}: "
        f"{judge_verdict.groundedness.rationale}"
    )


@then(parsers.parse("the judge SKILL compliance score is at least {threshold:d}"))
def assert_judge_skill_compliance(judge_verdict: JudgeVerdict, threshold: int) -> None:
    assert judge_verdict.skill_compliance.score >= threshold, (
        f"SKILL compliance {judge_verdict.skill_compliance.score} < {threshold}: "
        f"{judge_verdict.skill_compliance.rationale}"
    )