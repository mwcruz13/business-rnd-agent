from pytest_bdd import given, parsers, scenarios, then, when
import pytest
import re

from backend.app.nodes.step8_pdsa import run_step, update_experiment_card_evidence
from backend.app.patterns.loader import PatternLibraryLoader
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
                "| Assumption | Category | VoC Evidence | Quadrant |",
                "|------------|----------|--------------|----------|",
                f"| {TOP_ASSUMPTIONS['Desirability']} | Desirability | Weak | Test first |",
                "| I believe customers care more about faster time-to-value than about preserving the current high-touch onboarding model. | Desirability | None | Monitor |",
                "| I believe visible onboarding progress increases customer confidence during activation. | Desirability | None | Safe zone |",
                f"| {TOP_ASSUMPTIONS['Viability']} | Viability | None | Test first |",
                "| I believe reduced onboarding effort will lower support costs enough to improve business model sustainability. | Viability | None | Monitor |",
                "| I believe customers will continue to adopt the offer without requiring a more expensive service layer. | Viability | None | Deprioritize |",
                f"| {TOP_ASSUMPTIONS['Feasibility']} | Feasibility | Weak | Test first |",
                "| I believe product telemetry and onboarding playbooks are sufficient to support the new activation path. | Feasibility | None | Monitor |",
                "| I believe support teams can handle exceptions while most customers self-serve successfully. | Feasibility | None | Safe zone |",
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
    library = PatternLibraryLoader().load_library("experiment-library.json").data
    canonical_names = {e["name"] for e in library["experiments"]}
    selections = step8_result["experiment_selections"]
    card_mentions = re.findall(r"\| \d+ \| (.+?) \| (?:Weak|Medium|Strong) \|", selections)
    assert len(card_mentions) >= 3, f"Expected at least 3 card recommendations, found {len(card_mentions)}"
    for name in card_mentions:
        assert name.strip() in canonical_names, f"Non-canonical card: {name.strip()}"


@then("the first recommended experiments are weak evidence cards")
def assert_weak_first(step8_result: BMIWorkflowState) -> None:
    selections = step8_result["experiment_selections"]
    first_cards = re.findall(r"\| 1 \| .+? \| (Weak|Medium|Strong) \|", selections)
    assert len(first_cards) == 3, f"Expected 3 first-priority cards, found {len(first_cards)}"
    for strength in first_cards:
        assert strength == "Weak", f"First experiment should be Weak, got {strength}"


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


@then("the workflow state contains structured experiment cards")
def assert_experiment_cards_present(step8_result: BMIWorkflowState) -> None:
    cards = step8_result.get("experiment_cards")
    assert isinstance(cards, list)
    assert len(cards) == 3  # one per top assumption (D, V, F)


@then("each experiment card has a unique id and correct structure")
def assert_card_structure(step8_result: BMIWorkflowState) -> None:
    cards = step8_result["experiment_cards"]
    ids = set()
    required_fields = {
        "id", "assumption", "category", "evidence_strength", "card_name",
        "what_it_tests", "best_used_when", "primary_metric", "secondary_metrics",
        "success_looks_like", "failure_looks_like", "ambiguous_looks_like",
        "sequencing", "evidence_path", "status", "evidence",
    }
    for card in cards:
        assert card["id"] not in ids, f"Duplicate card id: {card['id']}"
        ids.add(card["id"])
        missing = required_fields - set(card.keys())
        assert not missing, f"Card {card['id']} missing fields: {missing}"


@then("each experiment card matches a top assumption")
def assert_cards_match_assumptions(step8_result: BMIWorkflowState) -> None:
    cards = step8_result["experiment_cards"]
    card_assumptions = {c["assumption"] for c in cards}
    for assumption_text in TOP_ASSUMPTIONS.values():
        assert assumption_text in card_assumptions


@then("each experiment card starts with planned status and empty evidence")
def assert_cards_initial_state(step8_result: BMIWorkflowState) -> None:
    for card in step8_result["experiment_cards"]:
        assert card["status"] == "planned"
        assert card["owner"] is None
        evidence = card["evidence"]
        for key in ("what_customers_said", "what_customers_did", "what_surprised_us",
                     "confidence_change", "decision", "next_experiment", "notes"):
            assert evidence[key] is None, f"evidence.{key} should be None"


@then("experiment card evidence can be updated with valid Zone B fields")
def assert_evidence_update(step8_result: BMIWorkflowState) -> None:
    card = step8_result["experiment_cards"][0]
    updated = update_experiment_card_evidence(card, {
        "status": "running",
        "owner": "Jane Doe",
        "evidence": {
            "what_customers_said": "They confirmed the pain is real.",
            "confidence_change": "increased",
        },
    })
    assert updated["status"] == "running"
    assert updated["owner"] == "Jane Doe"
    assert updated["evidence"]["what_customers_said"] == "They confirmed the pain is real."
    assert updated["evidence"]["confidence_change"] == "increased"
    # Original evidence fields remain None
    assert updated["evidence"]["what_customers_did"] is None


@then("experiment card rejects updates to Zone A fields")
def assert_zone_a_rejected(step8_result: BMIWorkflowState) -> None:
    card = step8_result["experiment_cards"][0]
    with pytest.raises(ValueError, match="Cannot update Zone A fields"):
        update_experiment_card_evidence(card, {"assumption": "Hacked"})
    with pytest.raises(ValueError, match="Cannot update Zone A fields"):
        update_experiment_card_evidence(card, {"card_name": "Fake Card"})
    with pytest.raises(ValueError, match="Invalid status"):
        update_experiment_card_evidence(card, {"status": "bogus"})


# ---------------------------------------------------------------------------
# Structured step7 data for Phase 1-4 scenarios
# ---------------------------------------------------------------------------

STEP7_STRUCTURED = {
    "categories": [
        {
            "category": "Desirability",
            "assumptions": [
                {"assumption": TOP_ASSUMPTIONS["Desirability"], "rationale": "If buyers do not value lower-friction activation, the value proposition loses its core appeal.", "suggested_quadrant": "Test first"},
                {"assumption": "I believe customers care more about faster time-to-value than about preserving the current high-touch onboarding model.", "rationale": "If time-to-value is not a priority, the proposed direction solves the wrong problem.", "suggested_quadrant": "Monitor"},
                {"assumption": "I believe visible onboarding progress increases customer confidence during activation.", "rationale": "If progress visibility does not matter, part of the proposed experience is unnecessary.", "suggested_quadrant": "Safe zone"},
            ],
        },
        {
            "category": "Viability",
            "assumptions": [
                {"assumption": TOP_ASSUMPTIONS["Viability"], "rationale": "If faster activation does not improve revenue retention or expansion, the model may not justify the investment.", "suggested_quadrant": "Test first"},
                {"assumption": "I believe reduced onboarding effort will lower support costs enough to improve business model sustainability.", "rationale": "If support costs remain unchanged, the economics of the new model weaken.", "suggested_quadrant": "Monitor"},
                {"assumption": "I believe customers will continue to adopt the offer without requiring a more expensive service layer.", "rationale": "If adoption requires costly human intervention, margins may erode.", "suggested_quadrant": "Deprioritize"},
            ],
        },
        {
            "category": "Feasibility",
            "assumptions": [
                {"assumption": TOP_ASSUMPTIONS["Feasibility"], "rationale": "If the team cannot deliver the new flow reliably, the design will stall in execution.", "suggested_quadrant": "Test first"},
                {"assumption": "I believe product telemetry and onboarding playbooks are sufficient to support the new activation path.", "rationale": "If these resources are inadequate, the model will be difficult to run consistently.", "suggested_quadrant": "Monitor"},
                {"assumption": "I believe support teams can handle exceptions while most customers self-serve successfully.", "rationale": "If exception volume stays high, the operating model will not scale.", "suggested_quadrant": "Safe zone"},
            ],
        },
    ],
    "dvf_tensions": [
        {"tension": "Faster activation vs delivery capacity", "assumption_a": TOP_ASSUMPTIONS["Desirability"], "assumption_b": TOP_ASSUMPTIONS["Feasibility"], "categories_in_conflict": "Desirability vs Feasibility"},
    ],
}


@given("a workflow state with completed Step 7 risk outputs including structured data", target_fixture="workflow_state")
def workflow_state_with_structured() -> BMIWorkflowState:
    base = workflow_state()
    base["step7_structured"] = dict(STEP7_STRUCTURED)
    return base


@given("a workflow state with Step 7 markdown output but no structured data", target_fixture="workflow_state")
def workflow_state_markdown_only() -> BMIWorkflowState:
    base = workflow_state()
    # Ensure no structured data key exists
    base.pop("step7_structured", None)
    return base


@then("the experiment cards reference assumptions from the structured step 7 output")
def assert_cards_from_structured(step8_result: BMIWorkflowState) -> None:
    cards = step8_result["experiment_cards"]
    card_assumptions = {c["assumption"] for c in cards}
    # All test-first assumptions from structured data should be in cards
    for assumption_text in TOP_ASSUMPTIONS.values():
        assert assumption_text in card_assumptions, f"Missing assumption from structured data: {assumption_text}"


@then("the experiment card count matches the number of test-first assumptions in structured output")
def assert_card_count_matches_structured(step8_result: BMIWorkflowState) -> None:
    # Count test-first assumptions in STEP7_STRUCTURED
    test_first_count = sum(
        1 for cat in STEP7_STRUCTURED["categories"]
        for a in cat["assumptions"]
        if a["suggested_quadrant"] == "Test first"
    )
    cards = step8_result["experiment_cards"]
    assert len(cards) == test_first_count, f"Expected {test_first_count} cards, got {len(cards)}"


# ── Phase 4-1: empty test-first assumptions ─────────────────────────────

@given("a workflow state with Step 7 output containing zero test-first assumptions", target_fixture="workflow_state")
def workflow_state_no_test_first() -> BMIWorkflowState:
    """All assumptions are Monitor/Deprioritize/Safe zone — none are Test first."""
    return {
        "session_id": "session-008-empty",
        "current_step": "risk_map",
        "input_type": "text",
        "llm_backend": "azure",
        "pattern_direction": "shift",
        "selected_patterns": ["Cost Differentiators"],
        "business_model_canvas": "## Business Model Canvas\n\nPattern context: Cost Differentiators.",
        "fit_assessment": "## Fit Assessment\n\nThe model remains assumption-heavy.",
        "assumptions": "\n".join(
            [
                "## Desirability",
                "| Category | Assumption | Rationale |",
                "|----------|------------|-----------|",
                "| Desirable | Assumption A | Rationale A |",
                "",
                "## Viability",
                "| Category | Assumption | Rationale |",
                "|----------|------------|-----------|",
                "| Viable | Assumption B | Rationale B |",
                "",
                "## Feasibility",
                "| Category | Assumption | Rationale |",
                "|----------|------------|-----------|",
                "| Feasible | Assumption C | Rationale C |",
                "",
                "## Importance × Evidence Map",
                "| Assumption | Category | Quadrant |",
                "|------------|----------|----------|",
                "| Assumption A | Desirability | Monitor |",
                "| Assumption B | Viability | Deprioritize |",
                "| Assumption C | Feasibility | Safe zone |",
            ]
        ),
        "step7_structured": {
            "categories": [
                {
                    "category": "Desirability",
                    "assumptions": [
                        {"assumption": "Assumption A", "rationale": "Rationale A", "suggested_quadrant": "Monitor"},
                    ],
                },
                {
                    "category": "Viability",
                    "assumptions": [
                        {"assumption": "Assumption B", "rationale": "Rationale B", "suggested_quadrant": "Deprioritize"},
                    ],
                },
                {
                    "category": "Feasibility",
                    "assumptions": [
                        {"assumption": "Assumption C", "rationale": "Rationale C", "suggested_quadrant": "Safe zone"},
                    ],
                },
            ],
            "dvf_tensions": [],
        },
    }


@then("the workflow state contains empty experiment selections")
def assert_empty_selections(step8_result: BMIWorkflowState) -> None:
    selections = step8_result.get("experiment_selections", None)
    assert selections is not None, "experiment_selections key should exist"
    assert selections == "" or selections == [], f"Expected empty selections, got: {selections!r}"


@then("the workflow state contains empty experiment cards")
def assert_empty_cards(step8_result: BMIWorkflowState) -> None:
    cards = step8_result.get("experiment_cards", None)
    assert cards is not None, "experiment_cards key should exist"
    assert cards == [], f"Expected empty card list, got {len(cards)} cards"