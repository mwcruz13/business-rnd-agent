from pytest_bdd import given, parsers, scenarios, then, when

from backend.app.nodes.step3_profile import run_step
from backend.app.nodes.step3_profile_llm import (
    CustomerEmpathyProfile,
    CustomerJob,
    CustomerPain,
    check_empathy_gate,
    format_gate_questions,
    EMPATHY_TRIGGER_QUESTIONS,
)
from backend.app.state import BMIWorkflowState


scenarios("features/step3-customer-profile.feature")


# ---------------------------------------------------------------------------
# Givens
# ---------------------------------------------------------------------------

@given("a workflow state with a consultant-approved pattern direction", target_fixture="workflow_state")
def workflow_state() -> BMIWorkflowState:
    return {
        "session_id": "session-003",
        "current_step": "pattern_select",
        "input_type": "text",
        "llm_backend": "azure",
        "voc_data": "Customers avoid onboarding because it is too complex",
        "interpreted_signals": [
            {
                "signal": "Customers delay onboarding due to workflow complexity",
                "zone": "Overserved Customers",
                "classification": "Disruptive - Low-End",
            }
        ],
        "agent_recommendation": "Shift toward a simpler low-friction model using Cost Differentiators.",
        "pattern_direction": "shift",
        "selected_patterns": ["Cost Differentiators"],
    }


@given("a customer empathy profile with an empty gains section", target_fixture="gate_profile")
def gate_profile_empty_gains() -> CustomerEmpathyProfile:
    """A profile where gains is empty — triggers the empathy gate."""
    return CustomerEmpathyProfile(
        customer_segment="Test segment",
        jobs=[CustomerJob(type="Functional", job="Complete onboarding", importance="High")],
        pains=[CustomerPain(type="Functional", pain="Complex workflow", severity="Severe")],
        gains=[],
    )


@given("a workflow state with supplemental VoC from the consultant", target_fixture="workflow_state")
def workflow_state_with_supplemental_voc() -> BMIWorkflowState:
    return {
        "session_id": "session-003",
        "current_step": "pattern_select",
        "input_type": "text",
        "llm_backend": "azure",
        "voc_data": "Customers avoid onboarding because it is too complex",
        "interpreted_signals": [
            {
                "signal": "Customers delay onboarding due to workflow complexity",
                "zone": "Overserved Customers",
                "classification": "Disruptive - Low-End",
            }
        ],
        "agent_recommendation": "Shift toward a simpler low-friction model using Cost Differentiators.",
        "pattern_direction": "shift",
        "selected_patterns": ["Cost Differentiators"],
        "supplemental_voc": (
            "The customer's main functional gain is faster time-to-value through simplified setup. "
            "They desire recognition from leadership for adopting efficient tools (social gain). "
            "They feel relieved and confident when onboarding completes without escalations (emotional gain)."
        ),
    }


# ---------------------------------------------------------------------------
# Whens
# ---------------------------------------------------------------------------

@when("the Step 3 customer profile node runs", target_fixture="step3_result")
def step3_result(workflow_state: BMIWorkflowState) -> BMIWorkflowState:
    return run_step(workflow_state)


@when("the empathy gate evaluates the profile", target_fixture="gate_result")
def gate_result(gate_profile: CustomerEmpathyProfile) -> dict:
    """Run the deterministic gate check — no LLM needed."""
    gaps = check_empathy_gate(gate_profile)
    return {
        "gaps": gaps,
        "formatted": format_gate_questions(gaps) if gaps else "",
    }


# ---------------------------------------------------------------------------
# Thens
# ---------------------------------------------------------------------------

@then('the workflow current step is "empathize"')
def assert_current_step(step3_result: BMIWorkflowState) -> None:
    assert step3_result["current_step"] == "empathize"


@then("the selected patterns are preserved in the workflow state")
def assert_selected_patterns_preserved(
    workflow_state: BMIWorkflowState, step3_result: BMIWorkflowState
) -> None:
    assert step3_result["selected_patterns"] == workflow_state["selected_patterns"]


@then("the workflow state contains a customer profile")
def assert_customer_profile(step3_result: BMIWorkflowState) -> None:
    assert isinstance(step3_result.get("customer_profile"), str)
    assert step3_result["customer_profile"]


@then("the customer profile uses the CXIF empathy headings")
def assert_cxif_headings(step3_result: BMIWorkflowState) -> None:
    customer_profile = step3_result["customer_profile"]
    assert "## Customer Empathy Profile" in customer_profile
    assert "### Customer Jobs" in customer_profile
    assert "### Customer Pains" in customer_profile
    assert "### Customer Gains" in customer_profile


@then("the customer profile includes the selected pattern context")
def assert_selected_pattern_context(
    workflow_state: BMIWorkflowState, step3_result: BMIWorkflowState
) -> None:
    customer_profile = step3_result["customer_profile"]
    assert workflow_state["selected_patterns"][0] in customer_profile


@then(parsers.parse("the customer profile includes at least {minimum:d} customer jobs"))
def assert_minimum_jobs(step3_result: BMIWorkflowState, minimum: int) -> None:
    customer_profile = step3_result["customer_profile"]
    jobs_section = customer_profile.split("### Customer Jobs")[1].split("### Customer Pains")[0]
    row_count = sum(1 for line in jobs_section.strip().splitlines() if line.startswith("| ") and not line.startswith("| Type") and not line.startswith("|--"))
    assert row_count >= minimum, f"Expected at least {minimum} jobs, found {row_count}"


@then(parsers.parse("the customer profile includes at least {minimum:d} customer pains"))
def assert_minimum_pains(step3_result: BMIWorkflowState, minimum: int) -> None:
    customer_profile = step3_result["customer_profile"]
    pains_section = customer_profile.split("### Customer Pains")[1].split("### Customer Gains")[0]
    row_count = sum(1 for line in pains_section.strip().splitlines() if line.startswith("| ") and not line.startswith("| Type") and not line.startswith("|--"))
    assert row_count >= minimum, f"Expected at least {minimum} pains, found {row_count}"


@then(parsers.parse("the customer profile includes at least {minimum:d} customer gains"))
def assert_minimum_gains(step3_result: BMIWorkflowState, minimum: int) -> None:
    customer_profile = step3_result["customer_profile"]
    gains_section = customer_profile.split("### Customer Gains")[1]
    row_count = sum(1 for line in gains_section.strip().splitlines() if line.startswith("| ") and not line.startswith("| Type") and not line.startswith("|--"))
    assert row_count >= minimum, f"Expected at least {minimum} gains, found {row_count}"


# --- Gate scenario assertions ---

@then("the gate produces CXIF trigger questions for the gains section")
def assert_gate_trigger_questions(gate_result: dict) -> None:
    assert "gains" in gate_result["gaps"], "Gate should have flagged the empty gains section"
    assert gate_result["gaps"]["gains"] == EMPATHY_TRIGGER_QUESTIONS["gains"]
    assert "### Gains" in gate_result["formatted"]
    for type_name, question in EMPATHY_TRIGGER_QUESTIONS["gains"]:
        assert type_name in gate_result["formatted"]
        assert question in gate_result["formatted"]


@then("the workflow state does not contain empathy gap questions")
def assert_no_gap_questions(step3_result: BMIWorkflowState) -> None:
    assert not step3_result.get("empathy_gap_questions"), (
        "Retry path should not set empathy_gap_questions"
    )