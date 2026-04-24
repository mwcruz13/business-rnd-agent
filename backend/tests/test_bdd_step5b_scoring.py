from pytest_bdd import given, scenarios, then, when

from backend.app.nodes.step5b_scoring import run_step
from backend.app.state import BMIWorkflowState


scenarios("features/step5b-scoring.feature")


@given("a workflow state with completed Step 5a VP alternatives", target_fixture="workflow_state")
def workflow_state() -> BMIWorkflowState:
    """State that simulates Step 5a having completed with 3 VP alternatives."""
    return {
        "session_id": "session-005b",
        "current_step": "vp_ideation",
        "input_type": "text",
        "llm_backend": "azure",
        "pattern_direction": "shift",
        "selected_patterns": ["Cost Differentiators"],
        "customer_profile": "\n".join(
            [
                "## Customer Empathy Profile",
                "",
                "### Customer Pains",
                "| Type | Pain | Severity |",
                "|------|------|----------|",
                "| Functional | The current setup flow is too complex and slows time-to-value | Severe |",
                "| Emotional | Customers feel uncertainty when progress depends on specialist support | Severe |",
                "",
                "### Customer Gains",
                "| Type | Gain | Relevance |",
                "|------|------|-----------|",
                "| Functional | A faster activation path aligned to Cost Differentiators | Essential |",
                "| Emotional | Confidence that onboarding can be completed without escalation | Essential |",
            ]
        ),
        "vp_alternatives": [
            {
                "name": "Resource-Light Self-Serve Onboarding",
                "pattern_flavor_applied": "Resource Dodgers",
                "strategic_rationale": "Eliminate specialist dependency using technology-driven self-serve.",
                "target_segment": "Operational buyers seeking fast time-to-value",
                "primary_job_focus": "Complete onboarding quickly without expert intervention",
                "context_scenario": "New customer activation during high-volume deployment periods",
                "products_services": [
                    {"type": "Digital", "product_service": "Self-serve onboarding portal", "relevance": "Core"},
                ],
                "pain_relievers": [
                    {"type": "Functional", "pain_reliever": "Automated guided setup eliminates manual complexity", "pain_addressed": "Setup flow is too complex", "relevance": "Substantial"},
                ],
                "gain_creators": [
                    {"type": "Functional", "gain_creator": "Instant activation path reduces onboarding from weeks to hours", "gain_addressed": "Faster activation path", "relevance": "Substantial"},
                ],
                "ad_lib_prototype": {"statement": "OUR self-serve portal HELPS operational buyers WHO WANT TO complete onboarding quickly BY eliminating manual setup complexity AND enabling instant activation"},
                "pattern_coherence_note": "Resource Dodgers eliminates costly specialist resources from the delivery model.",
            },
            {
                "name": "Technology-Driven Cost Reduction",
                "pattern_flavor_applied": "Technologists",
                "strategic_rationale": "Use automation to replace manual labor and reduce delivery costs.",
                "target_segment": "IT teams managing multi-site deployments",
                "primary_job_focus": "Demonstrate to peers that adoption is under control",
                "context_scenario": "Organizations with distributed infrastructure needing standardized deployment",
                "products_services": [
                    {"type": "Digital", "product_service": "Automated deployment orchestration platform", "relevance": "Core"},
                ],
                "pain_relievers": [
                    {"type": "Social", "pain_reliever": "Dashboard visibility proves deployment progress to stakeholders", "pain_addressed": "Delays make the buying team look unprepared", "relevance": "Substantial"},
                ],
                "gain_creators": [
                    {"type": "Social", "gain_creator": "Real-time deployment tracking provides visible proof of progress", "gain_addressed": "Visible proof that the new model reduces friction", "relevance": "Substantial"},
                ],
                "ad_lib_prototype": {"statement": "OUR orchestration platform HELPS IT teams WHO WANT TO demonstrate deployment control BY providing real-time progress visibility AND reducing manual coordination"},
                "pattern_coherence_note": "Technologists uses technology to replace labor-intensive activities.",
            },
            {
                "name": "Low-Cost Standardized Packages",
                "pattern_flavor_applied": "Low Cost",
                "strategic_rationale": "Combine simplified offerings with standardized delivery for disruptive pricing.",
                "target_segment": "Budget-conscious buyers with straightforward deployment needs",
                "primary_job_focus": "Feel confident that the solution will work without rework",
                "context_scenario": "SMB customers evaluating total cost of ownership",
                "products_services": [
                    {"type": "Intangible", "product_service": "Standardized deployment package with fixed scope", "relevance": "Core"},
                ],
                "pain_relievers": [
                    {"type": "Emotional", "pain_reliever": "Fixed-scope packages eliminate uncertainty about outcomes", "pain_addressed": "Customers feel uncertainty when progress depends on specialist support", "relevance": "Substantial"},
                ],
                "gain_creators": [
                    {"type": "Emotional", "gain_creator": "Guaranteed outcomes build confidence in onboarding success", "gain_addressed": "Confidence that onboarding can be completed without escalation", "relevance": "Substantial"},
                ],
                "ad_lib_prototype": {"statement": "OUR standardized packages HELP budget-conscious buyers WHO WANT TO onboard confidently BY guaranteeing fixed outcomes AND removing dependency on specialist support"},
                "pattern_coherence_note": "Low Cost combines standardized delivery with disruptive pricing.",
            },
        ],
        "value_proposition_canvas": "# Value Proposition Portfolio\n\n(combined markdown from step 5a)",
    }


@when("the Step 5b scoring node runs", target_fixture="step5b_result")
def step5b_result(workflow_state: BMIWorkflowState) -> BMIWorkflowState:
    return run_step(workflow_state)


# --- Scenario: Step 5b scores all VP alternatives ---

@then('the workflow current step is "vp_scoring"')
def assert_current_step(step5b_result: BMIWorkflowState) -> None:
    assert step5b_result["current_step"] == "vp_scoring"


@then("the workflow state contains vp_rankings")
def assert_rankings_exist(step5b_result: BMIWorkflowState) -> None:
    rankings = step5b_result.get("vp_rankings")
    assert isinstance(rankings, list)
    assert len(rankings) > 0


@then("the number of rankings matches the number of VP alternatives")
def assert_ranking_count(workflow_state: BMIWorkflowState, step5b_result: BMIWorkflowState) -> None:
    expected = len(workflow_state.get("vp_alternatives", []))
    actual = len(step5b_result.get("vp_rankings", []))
    assert actual == expected, f"Expected {expected} rankings, got {actual}"


# --- Scenario: Each ranking includes all five scoring criteria ---

@then("each ranking includes a coverage score")
def assert_coverage(step5b_result: BMIWorkflowState) -> None:
    for i, r in enumerate(step5b_result["vp_rankings"]):
        assert r.get("coverage_score"), f"Ranking {i} missing coverage_score"


@then("each ranking includes an evidence score")
def assert_evidence(step5b_result: BMIWorkflowState) -> None:
    for i, r in enumerate(step5b_result["vp_rankings"]):
        assert r.get("evidence_score"), f"Ranking {i} missing evidence_score"


@then("each ranking includes a pattern fit score")
def assert_pattern_fit(step5b_result: BMIWorkflowState) -> None:
    for i, r in enumerate(step5b_result["vp_rankings"]):
        assert r.get("pattern_fit_score"), f"Ranking {i} missing pattern_fit_score"


@then("each ranking includes a differentiation score")
def assert_differentiation(step5b_result: BMIWorkflowState) -> None:
    for i, r in enumerate(step5b_result["vp_rankings"]):
        assert r.get("differentiation_score"), f"Ranking {i} missing differentiation_score"


@then("each ranking includes a testability score")
def assert_testability(step5b_result: BMIWorkflowState) -> None:
    for i, r in enumerate(step5b_result["vp_rankings"]):
        assert r.get("testability_score"), f"Ranking {i} missing testability_score"


@then("each ranking includes an overall recommendation")
def assert_recommendation(step5b_result: BMIWorkflowState) -> None:
    for i, r in enumerate(step5b_result["vp_rankings"]):
        assert r.get("overall_recommendation"), f"Ranking {i} missing overall_recommendation"


# --- Scenario: Step 5b provides LLM recommendations ---

@then("the workflow state contains vp_recommended indices")
def assert_recommended_exists(step5b_result: BMIWorkflowState) -> None:
    recommended = step5b_result.get("vp_recommended")
    assert isinstance(recommended, list)
    assert len(recommended) >= 1


@then("the vp_recommended indices are valid alternative indices")
def assert_valid_indices(workflow_state: BMIWorkflowState, step5b_result: BMIWorkflowState) -> None:
    num_alts = len(workflow_state.get("vp_alternatives", []))
    for idx in step5b_result.get("vp_recommended", []):
        assert 0 <= idx < num_alts, f"Recommended index {idx} out of range [0, {num_alts})"


@then("the vp_rankings include a comparative summary")
def assert_comparative_summary(step5b_result: BMIWorkflowState) -> None:
    summary = step5b_result.get("vp_scoring_summary", "")
    assert "Comparative Summary" in summary, "Missing comparative summary in scoring output"
