from pytest_bdd import given, scenarios, then, when

from backend.app.nodes.step5_define import run_step
from backend.app.state import BMIWorkflowState


scenarios("features/step5-define.feature")


@given("a workflow state with completed Step 4 outputs", target_fixture="workflow_state")
def workflow_state() -> BMIWorkflowState:
    return {
        "session_id": "session-005",
        "current_step": "measure_define",
        "input_type": "text",
        "llm_backend": "azure",
        "pattern_direction": "shift",
        "selected_patterns": ["Cost Differentiators"],
        "customer_profile": "\n".join(
            [
                "## Customer Empathy Profile",
                "",
                "### Customer Segment",
                "Operational buyers navigating onboarding and early activation. Opportunity framing is informed by Cost Differentiators.",
                "",
                "### Customer Jobs",
                "| Type | Job | Importance |",
                "|------|-----|------------|",
                "| Functional | Complete onboarding quickly without expert intervention | High |",
                "| Social | Demonstrate to peers that adoption is under control | Medium |",
                "| Emotional | Feel confident that the solution will work without rework | High |",
                "",
                "### Customer Pains",
                "| Type | Pain | Severity |",
                "|------|------|----------|",
                "| Functional | The current setup flow is too complex and slows time-to-value | Severe |",
                "| Social | Delays make the buying team look unprepared in front of stakeholders | Moderate |",
                "| Emotional | Customers feel uncertainty when progress depends on specialist support | Severe |",
                "",
                "### Customer Gains",
                "| Type | Gain | Relevance |",
                "|------|------|-----------|",
                "| Functional | A faster activation path aligned to Cost Differentiators | Essential |",
                "| Social | Visible proof that the new model reduces friction for the wider team | Desired |",
                "| Emotional | Confidence that onboarding can be completed without escalation | Essential |",
            ]
        ),
        "value_driver_tree": "\n".join(
            [
                "## Value Driver Tree",
                "",
                "### Customer Business Outcome",
                "Reduce onboarding time-to-value while increasing buyer confidence during activation. The direction is being explored through Cost Differentiators.",
            ]
        ),
        "actionable_insights": "\n".join(
            [
                "## Context Analysis",
                "",
                "### Actionable Insights",
                "**Operational buyers** DOES **accelerate onboarding without specialist dependency** BECAUSE **they need fast time-to-value and visible progress** BUT **today's setup path is complex and creates delays**",
                "",
                "### Problem Statements",
                "| # | Problem Statement | Jobs Affected | Pains Addressed | Priority |",
                "|---|------------------|--------------|-----------------|----------|",
                "| 1 | Customers cannot realize value quickly because onboarding still assumes more process complexity than they need. | Accelerate onboarding | Setup friction and delay | High |",
            ]
        ),
    }


@when("the Step 5 define model node runs", target_fixture="step5_result")
def step5_result(workflow_state: BMIWorkflowState) -> BMIWorkflowState:
    return run_step(workflow_state)


@then('the workflow current step is "value_proposition"')
def assert_current_step(step5_result: BMIWorkflowState) -> None:
    assert step5_result["current_step"] == "value_proposition"


@then("the actionable insights are preserved in the workflow state")
def assert_actionable_insights_preserved(
    workflow_state: BMIWorkflowState, step5_result: BMIWorkflowState
) -> None:
    assert step5_result["actionable_insights"] == workflow_state["actionable_insights"]


@then("the workflow state contains a value proposition canvas")
def assert_value_proposition_canvas(step5_result: BMIWorkflowState) -> None:
    assert isinstance(step5_result.get("value_proposition_canvas"), str)
    assert step5_result["value_proposition_canvas"]


@then("the value proposition canvas uses the CXIF value map headings")
def assert_value_map_headings(step5_result: BMIWorkflowState) -> None:
    value_proposition_canvas = step5_result["value_proposition_canvas"]
    assert "## Value Proposition Canvas" in value_proposition_canvas
    assert "### Value Map" in value_proposition_canvas
    assert "#### Products & Services" in value_proposition_canvas
    assert "#### Pain Relievers" in value_proposition_canvas
    assert "#### Gain Creators" in value_proposition_canvas


@then("the value proposition canvas includes the approved pattern context")
def assert_pattern_context(step5_result: BMIWorkflowState) -> None:
    assert "Cost Differentiators" in step5_result["value_proposition_canvas"]


@then("the value proposition canvas maps pain relievers to customer pains")
def assert_pain_mapping(step5_result: BMIWorkflowState) -> None:
    value_proposition_canvas = step5_result["value_proposition_canvas"]
    section = value_proposition_canvas.split("#### Pain Relievers")[1].split("####")[0]
    data_rows = [r for r in section.strip().splitlines() if r.startswith("|") and "---" not in r and "Type" not in r]
    assert len(data_rows) >= 1, "Pain Relievers section must have at least 1 data row"


@then("the value proposition canvas maps gain creators to customer gains")
def assert_gain_mapping(step5_result: BMIWorkflowState) -> None:
    value_proposition_canvas = step5_result["value_proposition_canvas"]
    section = value_proposition_canvas.split("#### Gain Creators")[1].split("###")[0]
    data_rows = [r for r in section.strip().splitlines() if r.startswith("|") and "---" not in r and "Type" not in r]
    assert len(data_rows) >= 1, "Gain Creators section must have at least 1 data row"


@then("the value proposition canvas includes at least 2 ad-lib prototypes")
def assert_ad_lib_count(step5_result: BMIWorkflowState) -> None:
    value_proposition_canvas = step5_result["value_proposition_canvas"]
    assert value_proposition_canvas.count("**OUR**") >= 2