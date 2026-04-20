"""Quick validation of rendering changes for Phase 1+2.

Run: pytest backend/tests/test_rendering_validation.py -q
"""
from backend.app.nodes.step7_risk_llm import (
    Step7Output, DVFAssumption, DVFCategory, DVFTension, _render_assumptions,
)
from backend.app.nodes.step8_pdsa import _extract_top_assumptions


def _make_step7_output() -> Step7Output:
    return Step7Output(
        categories=[
            DVFCategory(category="Desirability", assumptions=[
                DVFAssumption(assumption="I believe customers want faster onboarding", rationale="Slow adoption kills revenue", suggested_quadrant="Test first"),
                DVFAssumption(assumption="I believe self-service reduces churn", rationale="High churn if support-dependent", suggested_quadrant="Monitor"),
                DVFAssumption(assumption="I believe UX quality matters more than features", rationale="Feature bloat confuses users", suggested_quadrant="Test first"),
            ]),
            DVFCategory(category="Viability", assumptions=[
                DVFAssumption(assumption="I believe subscription pricing works", rationale="Cash flow risk", suggested_quadrant="Test first"),
                DVFAssumption(assumption="I believe margins improve at scale", rationale="Unit economics fail", suggested_quadrant="Monitor"),
                DVFAssumption(assumption="I believe enterprise can afford premium tier", rationale="Pricing rejection", suggested_quadrant="Safe zone"),
            ]),
            DVFCategory(category="Feasibility", assumptions=[
                DVFAssumption(assumption="I believe our team can build this in 6 months", rationale="Delay kills market window", suggested_quadrant="Test first"),
                DVFAssumption(assumption="I believe existing infra can handle scale", rationale="Infra collapse at launch", suggested_quadrant="Monitor"),
                DVFAssumption(assumption="I believe API integrations are straightforward", rationale="Integration failures break workflow", suggested_quadrant="Deprioritize"),
            ]),
        ],
        dvf_tensions=[
            DVFTension(
                tension="Speed to market (Feasibility) may require cutting UX quality (Desirability)",
                assumption_a="I believe our team can build this in 6 months",
                assumption_b="I believe UX quality matters more than features",
                categories_in_conflict="Desirability vs Feasibility",
            ),
        ],
    )


def test_step7_rendering_has_suggested_quadrant_header():
    output = _make_step7_output()
    rendered = _render_assumptions(output, ["Cost Differentiators"])
    assert "## Importance × Evidence Map (Suggested — Review Required)" in rendered
    assert "| Assumption | Category | Suggested Quadrant |" in rendered


def test_step7_rendering_has_structured_tensions():
    output = _make_step7_output()
    rendered = _render_assumptions(output, ["Cost Differentiators"])
    assert "## DVF Tensions" in rendered
    assert "| Tension | Assumptions in Conflict | Categories |" in rendered
    assert "Desirability vs Feasibility" in rendered


def test_step7_rendering_has_review_required_notice():
    output = _make_step7_output()
    rendered = _render_assumptions(output, ["Cost Differentiators"])
    assert "The following quadrant placements are the LLM's best assessment" in rendered
    assert "should review and adjust" in rendered


def test_step8_parser_reads_new_step7_format():
    """Step 8 parser must extract 'Test first' assumptions from new Step 7 output."""
    output = _make_step7_output()
    rendered = _render_assumptions(output, ["Cost Differentiators"])
    top = _extract_top_assumptions(rendered)
    assert len(top) == 4  # 2 Desirability + 1 Viability + 1 Feasibility
    categories = {a.category for a in top}
    assert categories == {"Desirability", "Viability", "Feasibility"}
    for a in top:
        assert a.quadrant == "Test first"
        assert a.assumption.startswith("I believe")


def test_step6_schema_uses_validated_terminology():
    from backend.app.nodes.step6_design_llm import FitStatusRow, BusinessModelFitRow
    fit_schema = FitStatusRow.model_json_schema()
    assert "Validated" in fit_schema["properties"]["status"]["description"]
    assert "Demonstrated" not in fit_schema["properties"]["status"]["description"]
    bm_schema = BusinessModelFitRow.model_json_schema()
    assert "Validated" in bm_schema["properties"]["status"]["description"]


def test_step5_schema_has_supplier_descriptions():
    from backend.app.nodes.step5_define_llm import PainReliever, GainCreator, ProductService
    pr_schema = PainReliever.model_json_schema()
    assert "supplier" in pr_schema["properties"]["pain_reliever"]["description"].lower()
    gc_schema = GainCreator.model_json_schema()
    assert "supplier" in gc_schema["properties"]["gain_creator"]["description"].lower()
    ps_schema = ProductService.model_json_schema()
    assert "supplier" in ps_schema["properties"]["product_service"]["description"].lower()
