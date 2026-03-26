from pytest_bdd import given, parsers, scenarios, then, when

from backend.app.nodes.step2_pattern_llm import run_step2_llm
from backend.app.patterns.pattern_affinity import INVENT_PATTERNS, SHIFT_PATTERNS
from backend.app.state import BMIWorkflowState


scenarios("features/step2-pattern-matcher.feature")


@given("a workflow state with interpreted signals from Step 1", target_fixture="workflow_state")
def workflow_state() -> BMIWorkflowState:
    return {
        "session_id": "session-002",
        "current_step": "signal_scan",
        "input_type": "text",
        "llm_backend": "azure",
        "voc_data": "Customers avoid onboarding because it is too complex",
        "interpreted_signals": [
            {
                "signal": "Customers delay onboarding due to workflow complexity",
                "zone": "Overserved Customers",
                "classification": "Disruptive - Low-End",
                "filters": [],
            }
        ],
        "priority_matrix": [
            {
                "signal_id": None,
                "signal": "Customers delay onboarding due to workflow complexity",
                "impact": 3,
                "speed": 2,
                "score": 6,
                "tier": "Act",
            }
        ],
    }


@given("a workflow state with a new-market interpreted signal from Step 1", target_fixture="workflow_state")
def new_market_workflow_state() -> BMIWorkflowState:
    return {
        "session_id": "session-002b",
        "current_step": "signal_scan",
        "input_type": "text",
        "llm_backend": "azure",
        "voc_data": "Small teams can now launch analytics without needing an enterprise implementation project",
        "interpreted_signals": [
            {
                "signal": "Small teams launch analytics without enterprise implementation",
                "zone": "New-Market Foothold",
                "classification": "Disruptive — New-Market",
                "filters": [],
            }
        ],
        "priority_matrix": [
            {
                "signal_id": None,
                "signal": "Small teams launch analytics without enterprise implementation",
                "impact": 3,
                "speed": 3,
                "score": 9,
                "tier": "Act",
            }
        ],
    }


@when("the Step 2 pattern matcher node runs", target_fixture="step2_result")
def step2_result(workflow_state: BMIWorkflowState) -> BMIWorkflowState:
    return run_step2_llm(workflow_state)


@then('the workflow current step is "pattern_select"')
def assert_current_step(step2_result: BMIWorkflowState) -> None:
    assert step2_result["current_step"] == "pattern_select"


@then("the interpreted signals are preserved in the workflow state")
def assert_interpreted_signals_preserved(
    workflow_state: BMIWorkflowState, step2_result: BMIWorkflowState
) -> None:
    assert step2_result["interpreted_signals"] == workflow_state["interpreted_signals"]


@then("the workflow state contains an agent recommendation")
def assert_agent_recommendation(step2_result: BMIWorkflowState) -> None:
    assert isinstance(step2_result.get("agent_recommendation"), str)
    assert step2_result["agent_recommendation"]


@then("the agent recommendation says to explore SHIFT first")
def assert_shift_direction(step2_result: BMIWorkflowState) -> None:
    assert "SHIFT" in step2_result["agent_recommendation"]


@then("the agent recommendation says to explore INVENT first")
def assert_invent_direction(step2_result: BMIWorkflowState) -> None:
    assert "INVENT" in step2_result["agent_recommendation"]


@then(parsers.parse('Step 2 pre-fills pattern direction as "{direction}"'))
def assert_pattern_direction_prefilled(step2_result: BMIWorkflowState, direction: str) -> None:
    assert step2_result["pattern_direction"] == direction


@then("Step 2 selects patterns from the SHIFT library")
def assert_selected_shift_patterns(step2_result: BMIWorkflowState) -> None:
    patterns = step2_result.get("selected_patterns", [])
    assert len(patterns) > 0
    for p in patterns:
        assert p in SHIFT_PATTERNS, f"{p} is not a SHIFT pattern"


@then("Step 2 selects patterns from the INVENT library")
def assert_selected_invent_patterns(step2_result: BMIWorkflowState) -> None:
    patterns = step2_result.get("selected_patterns", [])
    assert len(patterns) > 0
    for p in patterns:
        assert p in INVENT_PATTERNS, f"{p} is not an INVENT pattern"


@then(parsers.parse('the selected patterns include "{pattern}"'))
def assert_selected_patterns_include(step2_result: BMIWorkflowState, pattern: str) -> None:
    patterns = step2_result.get("selected_patterns", [])
    assert pattern in patterns, f"Expected {pattern} in {patterns}"


@then("the selected patterns are verified library entries")
def assert_patterns_are_verified(step2_result: BMIWorkflowState) -> None:
    patterns = step2_result.get("selected_patterns", [])
    all_known = set(INVENT_PATTERNS) | set(SHIFT_PATTERNS)
    for p in patterns:
        assert p in all_known, f"{p} is not a known pattern"
