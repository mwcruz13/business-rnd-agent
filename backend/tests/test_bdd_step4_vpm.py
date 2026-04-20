from pytest_bdd import given, parsers, scenarios, then, when

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


@then(parsers.parse('every success measure driver type is one of "{valid_types}"'))
def assert_valid_driver_types(step4_result: BMIWorkflowState, valid_types: str) -> None:
    import re
    allowed = {t.strip() for t in valid_types.split(",")}
    vdt = step4_result["value_driver_tree"]
    # Parse the success measures table under "### Key Deliverables and Success Measures"
    section = vdt.split("### Key Deliverables and Success Measures")[1] if "### Key Deliverables and Success Measures" in vdt else vdt
    rows = re.findall(r"^\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|$", section, re.MULTILINE)
    data_rows = [r for r in rows if "---" not in r[0] and "Key Deliverable" not in r[0]]
    assert len(data_rows) >= 2, f"Expected at least 2 success measure rows, found {len(data_rows)}"
    for row in data_rows:
        driver_type = row[4].strip() if len(row) > 4 else row[-1].strip()
        assert driver_type in allowed, f"Invalid driver type '{driver_type}'. Allowed: {allowed}"


@then(parsers.parse('every friction point friction type is one of "{valid_types}"'))
def assert_valid_friction_types(step4_result: BMIWorkflowState, valid_types: str) -> None:
    import re
    allowed = {t.strip() for t in valid_types.split(",")}
    insights = step4_result["actionable_insights"]
    # Parse the friction points table under "### Customer Journey Friction Points"
    section = insights.split("### Customer Journey Friction Points")[1] if "### Customer Journey Friction Points" in insights else insights
    # Stop at next section
    if "###" in section[1:]:
        section = section[:section.index("###", 1)]
    rows = re.findall(r"^\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|$", section, re.MULTILINE)
    data_rows = [r for r in rows if "---" not in r[0] and "Journey Phase" not in r[0] and "Phase" not in r[0]]
    assert len(data_rows) >= 1, f"Expected at least 1 friction point row, found {len(data_rows)}"
    for row in data_rows:
        friction_type = row[3].strip()
        assert friction_type in allowed, f"Invalid friction type '{friction_type}'. Allowed: {allowed}"


@then("the value driver tree includes at least 3 success measures")
def assert_success_measure_count(step4_result: BMIWorkflowState) -> None:
    import re
    vdt = step4_result["value_driver_tree"]
    section = vdt.split("### Key Deliverables and Success Measures")[1] if "### Key Deliverables and Success Measures" in vdt else ""
    rows = re.findall(r"^\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|$", section, re.MULTILINE)
    data_rows = [r for r in rows if "---" not in r[0] and "Key Deliverable" not in r[0]]
    assert len(data_rows) >= 3, f"Expected at least 3 success measures, found {len(data_rows)}"


@then("every success measure has a non-empty baseline and target")
def assert_baseline_and_target(step4_result: BMIWorkflowState) -> None:
    import re
    vdt = step4_result["value_driver_tree"]
    section = vdt.split("### Key Deliverables and Success Measures")[1] if "### Key Deliverables and Success Measures" in vdt else ""
    rows = re.findall(r"^\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|$", section, re.MULTILINE)
    data_rows = [r for r in rows if "---" not in r[0] and "Key Deliverable" not in r[0]]
    for row in data_rows:
        baseline = row[2].strip()
        target = row[3].strip()
        assert baseline and baseline != "-", f"Empty baseline in success measure: {row[0].strip()}"
        assert target and target != "-", f"Empty target in success measure: {row[0].strip()}"


@then("the actionable insights include at least 1 problem statement")
def assert_problem_statement_count(step4_result: BMIWorkflowState) -> None:
    insights = step4_result["actionable_insights"]
    assert "### Problem Statements" in insights
    section = insights.split("### Problem Statements")[1].split("###")[0] if "###" in insights.split("### Problem Statements")[1][1:] else insights.split("### Problem Statements")[1]
    data_rows = [r for r in section.strip().splitlines() if r.startswith("|") and "---" not in r and "Problem Statement" not in r and "#" not in r]
    assert len(data_rows) >= 1, f"Expected at least 1 problem statement, found {len(data_rows)}"


@then("the actionable insights include at least 1 friction point")
def assert_friction_point_count(step4_result: BMIWorkflowState) -> None:
    insights = step4_result["actionable_insights"]
    assert "### Customer Journey Friction Points" in insights
    section = insights.split("### Customer Journey Friction Points")[1]
    if "###" in section[1:]:
        section = section[:section.index("###", 1)]
    data_rows = [r for r in section.strip().splitlines() if r.startswith("|") and "---" not in r and "Journey Phase" not in r and "Phase" not in r]
    assert len(data_rows) >= 1, f"Expected at least 1 friction point, found {len(data_rows)}"