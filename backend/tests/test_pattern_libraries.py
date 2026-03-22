from backend.app.patterns.loader import PatternLibraryLoader


def test_list_pattern_libraries_returns_packaged_json_assets():
    loader = PatternLibraryLoader()
    assert loader.list_libraries() == [
        "experiment-library.json",
        "precoil-emt-pattern-library.json",
        "soc-radar-pattern-library.json",
        "strategyzer-pattern-library.json",
    ]


def test_load_strategyzer_library_reads_metadata():
    loader = PatternLibraryLoader()
    library = loader.load_library("strategyzer-pattern-library.json")

    assert library.name == "strategyzer-pattern-library"
    assert library.data["metadata"]["title"] == "Strategyzer Pattern Library for Step 2"


def test_load_experiment_library_exposes_card_count():
    loader = PatternLibraryLoader()
    library = loader.load_library("experiment-library.json")

    assert library.data["metadata"]["card_count"] == 44
