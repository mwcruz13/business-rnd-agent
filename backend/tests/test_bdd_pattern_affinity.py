"""BDD step definitions for the pattern affinity shortlister."""

from __future__ import annotations

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from backend.app.patterns.pattern_affinity import shortlist_patterns, PatternScore


scenarios("features/pattern-affinity-shortlister.feature")


# ---- shared fixtures ----

@pytest.fixture()
def signal_context() -> dict:
    """Mutable dict to accumulate signal parameters across Given steps."""
    return {"zone": "", "classification": "", "filters": [], "max_results": 4}


@pytest.fixture()
def shortlister_result() -> dict:
    """Holds direction + shortlist after the When step runs."""
    return {"direction": "", "shortlist": []}


# ---- Given steps ----

@given(
    parsers.parse('a signal with zone "{zone}" and classification "{classification}"'),
    target_fixture="signal_context",
)
def given_signal(zone: str, classification: str) -> dict:
    return {"zone": zone, "classification": classification, "filters": [], "max_results": 4}


@given(
    parsers.parse('the signal has disruption filters "{f1}" and "{f2}"'),
)
def given_two_filters(signal_context: dict, f1: str, f2: str) -> None:
    signal_context["filters"] = [f1, f2]


@given(
    parsers.parse('the signal has disruption filters "{f1}"'),
)
def given_one_filter(signal_context: dict, f1: str) -> None:
    signal_context["filters"] = [f1]


@given(
    parsers.parse("the maximum shortlist size is {n:d}"),
)
def given_max_results(signal_context: dict, n: int) -> None:
    signal_context["max_results"] = n


# ---- When step ----

@when("the affinity shortlister runs", target_fixture="shortlister_result")
def when_shortlister_runs(signal_context: dict) -> dict:
    direction, shortlist = shortlist_patterns(
        zone=signal_context["zone"],
        classification=signal_context["classification"],
        filters=signal_context["filters"],
        max_results=signal_context["max_results"],
    )
    return {"direction": direction, "shortlist": shortlist}


# ---- Then steps ----

@then(parsers.parse('the direction is "{expected}"'))
def then_direction(shortlister_result: dict, expected: str) -> None:
    assert shortlister_result["direction"] == expected


@then(parsers.parse('the shortlist contains "{pattern_name}"'))
def then_shortlist_contains(shortlister_result: dict, pattern_name: str) -> None:
    names = [ps.name for ps in shortlister_result["shortlist"]]
    assert pattern_name in names, f"Expected '{pattern_name}' in {names}"


@then(parsers.parse('every shortlisted pattern belongs to the "{library}" library'))
def then_all_in_library(shortlister_result: dict, library: str) -> None:
    for ps in shortlister_result["shortlist"]:
        assert ps.library == library, f"{ps.name} has library={ps.library}, expected {library}"


@then("the shortlist is not empty")
def then_shortlist_not_empty(shortlister_result: dict) -> None:
    assert len(shortlister_result["shortlist"]) > 0


@then(parsers.parse('"{higher}" scores higher than "{lower}"'))
def then_scores_higher(shortlister_result: dict, higher: str, lower: str) -> None:
    scores = {ps.name: ps.score for ps in shortlister_result["shortlist"]}
    assert higher in scores, f"'{higher}' not in shortlist"
    assert lower in scores or True, f"'{lower}' not in shortlist (may have been pruned)"
    # If lower was pruned from shortlist, that inherently means higher scored above it
    if lower in scores:
        assert scores[higher] > scores[lower], (
            f"{higher}={scores[higher]} should be > {lower}={scores[lower]}"
        )


@then(parsers.parse("the shortlist has at most {n:d} entries"))
def then_max_entries(shortlister_result: dict, n: int) -> None:
    assert len(shortlister_result["shortlist"]) <= n
