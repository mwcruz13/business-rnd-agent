from pytest_bdd import given, parsers, scenarios, then, when

from backend.app.nodes.step7_risk import run_step
from backend.app.state import BMIWorkflowState


scenarios("features/step7-risk.feature")


@given("a workflow state with completed Step 6 design outputs", target_fixture="workflow_state")
def workflow_state() -> BMIWorkflowState:
    return {
        "session_id": "session-007",
        "current_step": "design_fit",
        "input_type": "text",
        "llm_backend": "azure",
        "pattern_direction": "shift",
        "selected_patterns": ["Cost Differentiators"],
        "business_model_canvas": "\n".join(
            [
                "## Business Model Canvas",
                "",
                "### Desirability",
                "| Building Block | Description |",
                "|---------------|-------------|",
                "| Customer Segments | Operational buyers and adoption stakeholders seeking faster activation through Cost Differentiators. |",
                "| Value Proposition | A lower-friction onboarding path that reduces setup complexity and accelerates time-to-value. Pattern context: Cost Differentiators. |",
                "| Channels | Direct sales handoff, guided digital onboarding, and in-product activation support. |",
                "| Customer Relationships | Self-service guidance with targeted human support for exceptions. |",
                "",
                "### Feasibility",
                "| Building Block | Description |",
                "|---------------|-------------|",
                "| Key Partnerships | Product, onboarding operations, and support teams aligned around a simplified activation path. |",
                "| Key Activities | Design guided setup flows, monitor activation progress, and intervene on edge cases. |",
                "| Key Resources | Onboarding playbooks, product telemetry, and customer-success expertise. |",
                "",
                "### Viability",
                "| Building Block | Description |",
                "|---------------|-------------|",
                "| Revenue Streams | Existing product revenue protected by faster activation and stronger adoption expansion. |",
                "| Cost Structure | Investment in productized onboarding flows, targeted support, and telemetry instrumentation. |",
            ]
        ),
        "fit_assessment": "\n".join(
            [
                "## Fit Assessment",
                "",
                "### Problem-Solution Fit",
                "| Customer Need (Job/Pain/Gain) | Importance to Customer | Mapped Value Proposition Element | Fit? |",
                "|------------------------------|----------------------|--------------------------------|------|",
                "| Complete onboarding quickly | High | Guided onboarding experience and streamlined setup steps | Strong |",
                "",
                "### Product-Market Fit Status",
                "| Criterion | Status | Evidence |",
                "|-----------|--------|----------|",
                "| Customers care about these jobs, pains, gains | Assumed | Prior workflow outputs point to onboarding friction and demand for faster activation. |",
                "| Value proposition creates real value for customers | Assumed | Prior workflow outputs point to onboarding friction and demand for faster activation. |",
                "| Market interest demonstrated | Unknown | No external validation has been run yet. |",
                "",
                "### Business Model Fit Status",
                "| Dimension | Status | Evidence |",
                "|-----------|--------|----------|",
                "| Desirable — creates value for customers and business | Assumed | Reduced onboarding friction is consistently supported. |",
                "| Feasible — the business model should work | Assumed | The model relies on productized onboarding and targeted support. |",
                "| Viable — will generate more revenue than costs | Unknown | Revenue preservation and cost reduction are not yet measured. |",
            ]
        ),
    }


@when("the Step 7 risk mapper node runs", target_fixture="step7_result")
def step7_result(workflow_state: BMIWorkflowState) -> BMIWorkflowState:
    return run_step(workflow_state)


@then('the workflow current step is "risk_map"')
def assert_current_step(step7_result: BMIWorkflowState) -> None:
    assert step7_result["current_step"] == "risk_map"


@then("the business model canvas is preserved in the workflow state")
def assert_bmc_preserved(workflow_state: BMIWorkflowState, step7_result: BMIWorkflowState) -> None:
    assert step7_result["business_model_canvas"] == workflow_state["business_model_canvas"]


@then("the workflow state contains assumptions")
def assert_assumptions(step7_result: BMIWorkflowState) -> None:
    assert isinstance(step7_result.get("assumptions"), str)
    assert step7_result["assumptions"]


@then("the assumptions use the Precoil EMT headings")
def assert_precoil_headings(step7_result: BMIWorkflowState) -> None:
    assumptions = step7_result["assumptions"]
    assert "## Desirability" in assumptions
    assert "## Viability" in assumptions
    assert "## Feasibility" in assumptions


@then("the assumptions include 9 formatted assumptions")
def assert_assumption_count(step7_result: BMIWorkflowState) -> None:
    assumptions = step7_result["assumptions"]
    formatted_rows = assumptions.count("| Desirable | I believe")
    formatted_rows += assumptions.count("| Viable | I believe")
    formatted_rows += assumptions.count("| Feasible | I believe")
    assert formatted_rows == 9


@then("the assumptions include all DVF categories")
def assert_dvf_categories(step7_result: BMIWorkflowState) -> None:
    assumptions = step7_result["assumptions"]
    assert "| Desirable |" in assumptions
    assert "| Viable |" in assumptions
    assert "| Feasible |" in assumptions


@then("the assumptions include a DVF tension check")
def assert_dvf_tensions(step7_result: BMIWorkflowState) -> None:
    assert "## DVF Tensions" in step7_result["assumptions"]


@then("the assumptions include an importance evidence matrix")
def assert_importance_evidence_matrix(step7_result: BMIWorkflowState) -> None:
    assumptions = step7_result["assumptions"]
    assert "## Importance × Evidence Map" in assumptions
    assert "| Assumption |" in assumptions and "| Category |" in assumptions
    import re
    assert re.search(r"\|\s*(?:Suggested\s+)?Quadrant\s*\|", assumptions), (
        "Expected a 'Quadrant' or 'Suggested Quadrant' column in the importance-evidence matrix"
    )


@then("the assumptions identify at least one test-first risk")
def assert_test_first(step7_result: BMIWorkflowState) -> None:
    assert "Test first" in step7_result["assumptions"]


@then(parsers.parse('every assumption quadrant is one of "{valid_quadrants}"'))
def assert_valid_quadrants(step7_result: BMIWorkflowState, valid_quadrants: str) -> None:
    import re
    allowed = {q.strip() for q in valid_quadrants.split(",")}
    assumptions = step7_result["assumptions"]
    # Parse the Importance × Evidence Map table rows
    matrix_section = assumptions.split("## Importance × Evidence Map")[1] if "## Importance × Evidence Map" in assumptions else ""
    rows = re.findall(r"^\|([^|]+)\|([^|]+)\|([^|]+)\|$", matrix_section, re.MULTILINE)
    # Skip the header and separator rows
    data_rows = [row for row in rows if "---" not in row[0] and "Assumption" not in row[0].strip()]
    assert len(data_rows) == 9, f"Expected 9 assumption rows, found {len(data_rows)}"
    for assumption_text, category, quadrant in data_rows:
        q = quadrant.strip()
        assert q in allowed, f"Invalid quadrant '{q}' for assumption '{assumption_text.strip()}'. Allowed: {allowed}"


@then("the workflow state contains structured step 7 output")
def assert_structured_output_exists(step7_result: BMIWorkflowState) -> None:
    structured = step7_result.get("step7_structured")
    assert isinstance(structured, dict), "step7_structured should be a dict"
    assert "categories" in structured
    assert "dvf_tensions" in structured


@then("the structured output has 3 DVF categories with 3 assumptions each")
def assert_structured_categories(step7_result: BMIWorkflowState) -> None:
    structured = step7_result["step7_structured"]
    categories = structured["categories"]
    assert len(categories) == 3, f"Expected 3 categories, got {len(categories)}"
    for cat in categories:
        assert len(cat["assumptions"]) == 3, f"Expected 3 assumptions in {cat['category']}, got {len(cat['assumptions'])}"


@then("every structured assumption has a suggested quadrant")
def assert_structured_quadrants(step7_result: BMIWorkflowState) -> None:
    valid_quadrants = {"Test first", "Monitor", "Deprioritize", "Safe zone"}
    for cat in step7_result["step7_structured"]["categories"]:
        for a in cat["assumptions"]:
            assert a.get("suggested_quadrant") in valid_quadrants, (
                f"Invalid quadrant '{a.get('suggested_quadrant')}' in structured output"
            )


@then("the assumptions include at least 1 DVF tension")
def assert_dvf_tension_count(step7_result: BMIWorkflowState) -> None:
    structured = step7_result.get("step7_structured")
    if structured:
        tensions = structured.get("dvf_tensions", [])
        assert len(tensions) >= 1, f"Expected at least 1 DVF tension in structured output, found {len(tensions)}"
    else:
        assert "## DVF Tensions" in step7_result["assumptions"]
        section = step7_result["assumptions"].split("## DVF Tensions")[1].split("##")[0]
        data_rows = [r for r in section.strip().splitlines() if r.startswith("|") and "---" not in r and "Tension" not in r]
        assert len(data_rows) >= 1, f"Expected at least 1 DVF tension row, found {len(data_rows)}"


@then("each DVF tension references two assumptions from different categories")
def assert_dvf_tension_cross_category(step7_result: BMIWorkflowState) -> None:
    structured = step7_result.get("step7_structured")
    assert structured, "step7_structured required for cross-category validation"
    dvf_categories = {"Desirability", "Viability", "Feasibility"}
    for tension in structured["dvf_tensions"]:
        conflict = tension.get("categories_in_conflict", "")
        # Should contain "vs" separating two different categories
        cats_mentioned = [c.strip() for c in conflict.replace("vs", ",").replace("×", ",").split(",")]
        cats_found = {c for c in cats_mentioned if c in dvf_categories}
        assert len(cats_found) >= 2, (
            f"DVF tension '{tension.get('tension')}' should reference 2 different DVF categories, "
            f"found: {cats_found} in '{conflict}'"
        )