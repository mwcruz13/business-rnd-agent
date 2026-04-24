from pytest_bdd import given, scenarios, then, when

from backend.app.nodes.step5a_ideation import run_step
from backend.app.state import BMIWorkflowState


scenarios("features/step5a-ideation.feature")


@given("a workflow state with completed Step 4 outputs and pattern context", target_fixture="workflow_state")
def workflow_state() -> BMIWorkflowState:
    return {
        "session_id": "session-005a",
        "current_step": "measure_define",
        "input_type": "text",
        "llm_backend": "azure",
        "pattern_direction": "shift",
        "selected_patterns": ["Cost Differentiators"],
        "num_vp_alternatives": 3,
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


@when("the Step 5a ideation node runs", target_fixture="step5a_result")
def step5a_result(workflow_state: BMIWorkflowState) -> BMIWorkflowState:
    return run_step(workflow_state)


# --- Scenario: Step 5a generates the configured number of VP alternatives ---

@then('the workflow current step is "vp_ideation"')
def assert_current_step(step5a_result: BMIWorkflowState) -> None:
    assert step5a_result["current_step"] == "vp_ideation"


@then("the workflow state contains vp_alternatives")
def assert_vp_alternatives_exist(step5a_result: BMIWorkflowState) -> None:
    alts = step5a_result.get("vp_alternatives")
    assert isinstance(alts, list)
    assert len(alts) > 0


@then("the number of VP alternatives matches the configured count")
def assert_vp_count(workflow_state: BMIWorkflowState, step5a_result: BMIWorkflowState) -> None:
    expected = workflow_state.get("num_vp_alternatives", 3)
    actual = len(step5a_result.get("vp_alternatives", []))
    assert actual == expected, f"Expected {expected} alternatives, got {actual}"


# --- Scenario: Each VP alternative is pattern-coherent ---

@then("each VP alternative declares a pattern flavor applied")
def assert_pattern_flavor(step5a_result: BMIWorkflowState) -> None:
    for i, alt in enumerate(step5a_result["vp_alternatives"]):
        assert alt.get("pattern_flavor_applied"), f"Alternative {i} missing pattern_flavor_applied"


@then("each VP alternative includes a pattern coherence note")
def assert_coherence_note(step5a_result: BMIWorkflowState) -> None:
    for i, alt in enumerate(step5a_result["vp_alternatives"]):
        assert alt.get("pattern_coherence_note"), f"Alternative {i} missing pattern_coherence_note"


@then("each VP alternative references the selected patterns")
def assert_pattern_reference(workflow_state: BMIWorkflowState, step5a_result: BMIWorkflowState) -> None:
    selected = workflow_state.get("selected_patterns", [])
    vpc = step5a_result.get("value_proposition_canvas", "")
    for pattern_name in selected:
        assert pattern_name in vpc, f"Pattern '{pattern_name}' not found in value_proposition_canvas"


# --- Scenario: VP alternatives have complete Value Map structure ---

@then("each VP alternative includes at least 1 product or service")
def assert_products(step5a_result: BMIWorkflowState) -> None:
    for i, alt in enumerate(step5a_result["vp_alternatives"]):
        assert len(alt.get("products_services", [])) >= 1, f"Alternative {i} has no products/services"


@then("each VP alternative includes at least 1 pain reliever")
def assert_pain_relievers(step5a_result: BMIWorkflowState) -> None:
    for i, alt in enumerate(step5a_result["vp_alternatives"]):
        assert len(alt.get("pain_relievers", [])) >= 1, f"Alternative {i} has no pain relievers"


@then("each VP alternative includes at least 1 gain creator")
def assert_gain_creators(step5a_result: BMIWorkflowState) -> None:
    for i, alt in enumerate(step5a_result["vp_alternatives"]):
        assert len(alt.get("gain_creators", [])) >= 1, f"Alternative {i} has no gain creators"


@then("each VP alternative includes an ad-lib prototype")
def assert_ad_lib(step5a_result: BMIWorkflowState) -> None:
    for i, alt in enumerate(step5a_result["vp_alternatives"]):
        ad_lib = alt.get("ad_lib_prototype", {})
        assert ad_lib.get("statement"), f"Alternative {i} missing ad-lib prototype"


# --- Scenario: VP alternatives are diverse across ideation axes ---

@then("the VP alternatives have distinct names")
def assert_distinct_names(step5a_result: BMIWorkflowState) -> None:
    names = [alt["name"] for alt in step5a_result["vp_alternatives"]]
    assert len(names) == len(set(names)), f"Duplicate VP names: {names}"


@then("the VP alternatives target different primary job focuses")
def assert_different_jobs(step5a_result: BMIWorkflowState) -> None:
    jobs = [alt.get("primary_job_focus", "") for alt in step5a_result["vp_alternatives"]]
    # At least 2 distinct job focuses (allow some overlap for 3 alternatives)
    assert len(set(jobs)) >= 2, f"VP alternatives lack job diversity: {jobs}"


@then("the ideation output includes a diversity check")
def assert_diversity_check(step5a_result: BMIWorkflowState) -> None:
    vpc = step5a_result.get("value_proposition_canvas", "")
    assert "Diversity Check" in vpc, "Missing diversity check in output"


# --- Scenario: backward compatibility ---

@then("the workflow state contains a value proposition canvas")
def assert_vpc_exists(step5a_result: BMIWorkflowState) -> None:
    assert isinstance(step5a_result.get("value_proposition_canvas"), str)
    assert step5a_result["value_proposition_canvas"]


@then("the value proposition canvas includes headings for each VP alternative")
def assert_vpc_headings(step5a_result: BMIWorkflowState) -> None:
    vpc = step5a_result["value_proposition_canvas"]
    for alt in step5a_result["vp_alternatives"]:
        assert alt["name"] in vpc, f"VP alternative '{alt['name']}' not in combined canvas"
