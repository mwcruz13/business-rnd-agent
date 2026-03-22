from pytest_bdd import given, scenarios, then, when

from backend.app.nodes.step8_pdsa import run_step
from backend.app.state import BMIWorkflowState


scenarios("features/step8-pdsa.feature")


TOP_ASSUMPTIONS = {
    "Desirability": "I believe operational buyers will choose a simpler onboarding path when it clearly reduces setup effort.",
    "Viability": "I believe the business can protect expansion revenue by accelerating activation through Cost Differentiators.",
    "Feasibility": "I believe the team can operationalize a guided onboarding flow without breaking existing delivery commitments.",
}


@given("a workflow state with completed Step 7 risk outputs", target_fixture="workflow_state")
def workflow_state() -> BMIWorkflowState:
    return {
        "session_id": "session-008",
        "current_step": "risk_map",
        "input_type": "text",
        "llm_backend": "azure",
        "pattern_direction": "shift",
        "selected_patterns": ["Cost Differentiators"],
        "business_model_canvas": "## Business Model Canvas\n\nPattern context: Cost Differentiators.",
        "fit_assessment": "## Fit Assessment\n\nThe model remains assumption-heavy and needs testing.",
        "assumptions": "\n".join(
            [
                "## Desirability",
                "| Category | Assumption | Rationale |",
                "|----------|------------|-----------|",
                f"| Desirable | {TOP_ASSUMPTIONS['Desirability']} | If buyers do not value lower-friction activation, the value proposition loses its core appeal. |",
                "| Desirable | I believe customers care more about faster time-to-value than about preserving the current high-touch onboarding model. | If time-to-value is not a priority, the proposed direction solves the wrong problem. |",
                "| Desirable | I believe visible onboarding progress increases customer confidence during activation. | If progress visibility does not matter, part of the proposed experience is unnecessary. |",
                "",
                "## Viability",
                "| Category | Assumption | Rationale |",
                "|----------|------------|-----------|",
                f"| Viable | {TOP_ASSUMPTIONS['Viability']} | If faster activation does not improve revenue retention or expansion, the model may not justify the investment. |",
                "| Viable | I believe reduced onboarding effort will lower support costs enough to improve business model sustainability. | If support costs remain unchanged, the economics of the new model weaken. |",
                "| Viable | I believe customers will continue to adopt the offer without requiring a more expensive service layer. | If adoption requires costly human intervention, margins may erode. |",
                "",
                "## Feasibility",
                "| Category | Assumption | Rationale |",
                "|----------|------------|-----------|",
                f"| Feasible | {TOP_ASSUMPTIONS['Feasibility']} | If the team cannot deliver the new flow reliably, the design will stall in execution. |",
                "| Feasible | I believe product telemetry and onboarding playbooks are sufficient to support the new activation path. | If these resources are inadequate, the model will be difficult to run consistently. |",
                "| Feasible | I believe support teams can handle exceptions while most customers self-serve successfully. | If exception volume stays high, the operating model will not scale. |",
                "",
                "## Importance × Evidence Map",
                "| Assumption | Category | Quadrant |",
                "|------------|----------|----------|",
                f"| {TOP_ASSUMPTIONS['Desirability']} | Desirability | Test first |",
                "| I believe customers care more about faster time-to-value than about preserving the current high-touch onboarding model. | Desirability | Monitor |",
                "| I believe visible onboarding progress increases customer confidence during activation. | Desirability | Safe zone |",
                f"| {TOP_ASSUMPTIONS['Viability']} | Viability | Test first |",
                "| I believe reduced onboarding effort will lower support costs enough to improve business model sustainability. | Viability | Monitor |",
                "| I believe customers will continue to adopt the offer without requiring a more expensive service layer. | Viability | Deprioritize |",
                f"| {TOP_ASSUMPTIONS['Feasibility']} | Feasibility | Test first |",
                "| I believe product telemetry and onboarding playbooks are sufficient to support the new activation path. | Feasibility | Monitor |",
                "| I believe support teams can handle exceptions while most customers self-serve successfully. | Feasibility | Safe zone |",
            ]
        ),
    }


@when("the Step 8 PDSA experiment designer node runs", target_fixture="step8_result")
def step8_result(workflow_state: BMIWorkflowState) -> BMIWorkflowState:
    return run_step(workflow_state)


@then('the workflow current step is "pdsa_plan"')
def assert_current_step(step8_result: BMIWorkflowState) -> None:
    assert step8_result["current_step"] == "pdsa_plan"


@then("the assumptions are preserved in the workflow state")
def assert_assumptions_preserved(workflow_state: BMIWorkflowState, step8_result: BMIWorkflowState) -> None:
    assert step8_result["assumptions"] == workflow_state["assumptions"]


@then("the workflow state contains experiment selections")
def assert_experiment_selections(step8_result: BMIWorkflowState) -> None:
    assert isinstance(step8_result.get("experiment_selections"), str)
    assert step8_result["experiment_selections"]


@then("the workflow state contains experiment plans")
def assert_experiment_plans(step8_result: BMIWorkflowState) -> None:
    assert isinstance(step8_result.get("experiment_plans"), str)
    assert step8_result["experiment_plans"]


@then("the workflow state contains experiment worksheets")
def assert_experiment_worksheets(step8_result: BMIWorkflowState) -> None:
    assert isinstance(step8_result.get("experiment_worksheets"), str)
    assert step8_result["experiment_worksheets"]


@then("the experiment selections use the Testing Business Ideas selection headings")
def assert_selection_headings(step8_result: BMIWorkflowState) -> None:
    selections = step8_result["experiment_selections"]
    assert selections.count("## Experiment Selection") == 3
    assert selections.count("### Recommended Experiments") == 3
    assert "### Selection rationale" in selections


@then("the experiment selections recommend canonical cards for each top assumption")
def assert_canonical_cards(step8_result: BMIWorkflowState) -> None:
    selections = step8_result["experiment_selections"]
    for experiment_name in [
        "Problem Interviews",
        "Landing Page",
        "Fake Door",
        "Competitor Analysis",
        "Mock Sale",
        "Pre-Order Test",
        "Expert Interviews",
        "Throwaway Prototype",
        "Wizard of Oz",
    ]:
        assert experiment_name in selections


@then("the first recommended experiments are weak evidence cards")
def assert_weak_first(step8_result: BMIWorkflowState) -> None:
    selections = step8_result["experiment_selections"]
    assert "| 1 | Problem Interviews | Weak |" in selections
    assert "| 1 | Competitor Analysis | Weak |" in selections
    assert "| 1 | Expert Interviews | Weak |" in selections


@then("the experiment plans use the Precoil brief headings")
def assert_precoil_brief_headings(step8_result: BMIWorkflowState) -> None:
    plans = step8_result["experiment_plans"]
    assert plans.count("## Experiment Brief") == 3
    assert "### Assumption to Test" in plans
    assert "### What You're Trying to Learn" in plans
    assert "### Experiment Type" in plans
    assert "### How to Run It" in plans
    assert "### How to Measure It" in plans
    assert "### Estimated Effort" in plans
    assert "### Remaining Uncertainty" in plans


@then("the experiment plans include implementation plans and evidence sequences")
def assert_plan_sections(step8_result: BMIWorkflowState) -> None:
    plans = step8_result["experiment_plans"]
    assert plans.count("## Experiment Implementation Plan") == 3
    assert plans.count("## Evidence Sequence") == 3
    assert "### Implementation Steps" in plans
    assert "### Sequence" in plans


@then("the experiment worksheets use the Testing Business Ideas worksheet headings")
def assert_worksheet_headings(step8_result: BMIWorkflowState) -> None:
    worksheets = step8_result["experiment_worksheets"]
    assert worksheets.count("## Experiment Worksheet") == 3
    assert "### Experiment Overview" in worksheets
    assert "### Assumption To Test" in worksheets
    assert "### Learning Objective" in worksheets
    assert "### Success And Failure Criteria" in worksheets
    assert "### Evidence Captured" in worksheets
    assert "### Decision" in worksheets


@then("the experiment artifacts reproduce the exact top assumptions")
def assert_exact_assumptions(step8_result: BMIWorkflowState) -> None:
    for assumption in TOP_ASSUMPTIONS.values():
        assert assumption in step8_result["experiment_selections"]
        assert assumption in step8_result["experiment_plans"]
        assert assumption in step8_result["experiment_worksheets"]