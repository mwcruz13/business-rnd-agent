from pytest_bdd import given, scenarios, then, when

from backend.app.nodes.step4_vpm import run_step
from backend.app.state import BMIWorkflowState


scenarios("features/step4-vpm.feature")


@given("a workflow state with a completed Step 3 empathy profile", target_fixture="workflow_state")
def workflow_state() -> BMIWorkflowState:
    return {
        "session_id": "session-004",
        "current_step": "empathize",
        "input_type": "text",
        "llm_backend": "azure",
        "voc_data": "Customers delay onboarding because the current process is too complex",
        "interpreted_signals": [
            {
                "signal": "Customers delay onboarding because the workflow is more complex than they value",
                "zone": "Overserved Customers",
                "classification": "Disruptive — Low-End",
            }
        ],
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
    }


@when("the Step 4 VPM synthesizer node runs", target_fixture="step4_result")
def step4_result(workflow_state: BMIWorkflowState) -> BMIWorkflowState:
    return run_step(workflow_state)


@then('the workflow current step is "measure_define"')
def assert_current_step(step4_result: BMIWorkflowState) -> None:
    assert step4_result["current_step"] == "measure_define"


@then("the customer profile is preserved in the workflow state")
def assert_customer_profile_preserved(
    workflow_state: BMIWorkflowState, step4_result: BMIWorkflowState
) -> None:
    assert step4_result["customer_profile"] == workflow_state["customer_profile"]


@then("the workflow state contains a value driver tree")
def assert_value_driver_tree(step4_result: BMIWorkflowState) -> None:
    assert isinstance(step4_result.get("value_driver_tree"), str)
    assert step4_result["value_driver_tree"]


@then("the workflow state contains actionable insights")
def assert_actionable_insights(step4_result: BMIWorkflowState) -> None:
    assert isinstance(step4_result.get("actionable_insights"), str)
    assert step4_result["actionable_insights"]


@then("the value driver tree uses the CXIF measure headings")
def assert_measure_headings(step4_result: BMIWorkflowState) -> None:
    value_driver_tree = step4_result["value_driver_tree"]
    assert "## Value Driver Tree" in value_driver_tree
    assert "### Customer Business Outcome" in value_driver_tree
    assert "### Key Deliverables and Success Measures" in value_driver_tree


@then("the actionable insights use the CXIF define headings")
def assert_define_headings(step4_result: BMIWorkflowState) -> None:
    actionable_insights = step4_result["actionable_insights"]
    assert "## Context Analysis" in actionable_insights
    assert "### Value Chain Assessment" in actionable_insights
    assert "### Customer Journey Friction Points" in actionable_insights
    assert "### Actionable Insights" in actionable_insights
    assert "### Problem Statements" in actionable_insights


@then("the value driver tree includes the approved pattern context")
def assert_pattern_context(step4_result: BMIWorkflowState) -> None:
    assert "Cost Differentiators" in step4_result["value_driver_tree"]


@then("the actionable insights include a WHO-DOES-BECAUSE-BUT statement")
def assert_who_does_because_but(step4_result: BMIWorkflowState) -> None:
    actionable_insights = step4_result["actionable_insights"]
    assert " DOES " in actionable_insights
    assert " BECAUSE " in actionable_insights
    assert " BUT " in actionable_insights