"""Phase 4+5 validation tests — Step 1 Recommend phase, Step 8 experiment matrix, schema fixes."""
from backend.app.nodes.step1_signal_llm import (
    SignalScanResult, SignalRecommendation, InterpretedSignal, DetectedSignal, PriorityEntry,
)
from backend.app.nodes.step8_pdsa import EXPERIMENT_MATRIX, PATH_BY_CATEGORY


def test_signal_recommendation_schema():
    rec = SignalRecommendation(
        signal_id="test_signal",
        action_tier="Act",
        what_we_know="Evidence shows X is happening because Y.",
        what_we_dont_know=["How many customers are affected", "Whether it's seasonal"],
        experiment_candidate="We believe that early adopters will switch within 30 days",
    )
    schema = rec.model_json_schema()
    assert "We believe that" in schema["properties"]["experiment_candidate"]["description"]
    assert "Act" in rec.action_tier


def test_signal_scan_result_includes_recommendations_field():
    schema = SignalScanResult.model_json_schema()
    assert "recommendations" in schema["properties"]
    assert "SignalRecommendation" in str(schema)


def test_interpreted_signal_has_alternative_explanation_description():
    schema = InterpretedSignal.model_json_schema()
    desc = schema["properties"]["alternative_explanation"]["description"]
    assert "plausible reason" in desc.lower()
    assert "disruptive" in desc.lower()


def test_experiment_matrix_covers_all_dvf_categories():
    assert set(EXPERIMENT_MATRIX.keys()) == {"Desirability", "Feasibility", "Viability"}
    for category, levels in EXPERIMENT_MATRIX.items():
        assert set(levels.keys()) == {"Weak", "Medium", "Strong"}, f"{category} missing evidence levels"


def test_experiment_matrix_weak_tier_includes_path_first_cards():
    """The first card in each PATH_BY_CATEGORY must appear in the matrix Weak tier."""
    for category, path in PATH_BY_CATEGORY.items():
        first_card = path[0]
        assert first_card in EXPERIMENT_MATRIX[category]["Weak"], (
            f"{first_card} not in {category} Weak tier"
        )


def test_experiment_matrix_cards_are_valid_library_names():
    """All card names in the matrix must exist in the experiment library."""
    from backend.app.patterns.loader import PatternLibraryLoader
    library = PatternLibraryLoader().load_library("experiment-library.json").data
    valid_names = {exp["name"] for exp in library["experiments"]}
    for category, levels in EXPERIMENT_MATRIX.items():
        for level, cards in levels.items():
            for card_name in cards:
                assert card_name in valid_names, (
                    f"'{card_name}' in {category}/{level} not found in experiment library"
                )


def test_path_by_category_unchanged():
    """PATH_BY_CATEGORY must remain unchanged to preserve BDD test compatibility."""
    assert PATH_BY_CATEGORY == {
        "Desirability": ["Problem Interviews", "Landing Page", "Fake Door"],
        "Feasibility": ["Expert Interviews", "Throwaway Prototype", "Wizard of Oz"],
        "Viability": ["Competitor Analysis", "Mock Sale", "Pre-Order Test"],
    }
