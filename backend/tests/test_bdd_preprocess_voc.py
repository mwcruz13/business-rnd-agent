"""BDD step definitions for VoC input preprocessing."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from pytest_bdd import given, parsers, scenarios, then, when

from backend.app.nodes.preprocess_voc import (
    ObservationMetadata,
    PreprocessingResult,
    RawObservation,
    clean_text,
    detect_products,
    detect_segments,
    find_near_duplicates,
    lookup_bu,
    merge_duplicates,
    reindex_observations,
    render_preprocessed_voc,
    run_preprocessing,
)
from backend.app.nodes.step1a_signal_scan_llm import _build_messages
from backend.app.state import BMIWorkflowState

scenarios("features/preprocess-voc.feature")


# ============================================================================
# Fixtures — multi-source sample input
# ============================================================================

_MULTI_SOURCE_INPUT = """\
From HPE Policy Guidance we hear:

HPE set the quote validity window to 14 days. Quote terms for servers have been modified.

HPE is adding a surcharge to offset the increased costs of DRAM and NAND industry wide.

From the technology front we have:

CXL 3.0 goes beyond memory expansion by enabling fabric-scale, coherent memory pooling.

CXL 3.0 explicitly targets memory disaggregation and composable AI infrastructure.

From Customer Comments:

## 2.1 5-month delay in delivery of full BoQ
"Urgent: 5-Month Delay in Delivery of HPE Order — Immediate Action Required."

## 2.2 Gen12 parts coming piecemeal
"Parts unavailable in the system coming piecemeal, without clear communication."

## 5.1 Almost a year out — not all GPUs deployed
"We are almost year out, and not all GPUs are deployed by HPE engineers."

From the Industry discussions:

The AI Infrastructure Buildout is driving up hardware and cloud costs.

IDC expects 2026 DRAM supply growth below historical norms at 16% year-on-year.
"""


# ============================================================================
# Phase 1: Segment detection
# ============================================================================

@given("a raw VoC input with 4 distinct source headers", target_fixture="raw_input")
def raw_input_multi_source() -> str:
    return _MULTI_SOURCE_INPUT


@when("the rule-based segmentation runs", target_fixture="segments")
def run_segmentation(raw_input: str):
    return detect_segments(raw_input)


@then(parsers.parse("{count:d} segments are detected"))
def assert_segment_count(segments, count: int):
    assert len(segments) == count, f"Expected {count} segments, got {len(segments)}"


@then(parsers.parse('the segment source types include "{type1}" and "{type2}"'))
def assert_segment_types(segments, type1: str, type2: str):
    types = {s.source_type for s in segments}
    assert type1 in types, f"{type1} not in {types}"
    assert type2 in types, f"{type2} not in {types}"


# ============================================================================
# Re-indexing
# ============================================================================

@when("observations are re-indexed", target_fixture="observations")
def run_reindex(segments):
    return reindex_observations(segments)


@then("observation IDs are sequential starting from 1 with no gaps")
def assert_sequential_ids(observations):
    ids = [o.observation_id for o in observations]
    assert ids == list(range(1, len(ids) + 1)), f"Non-sequential IDs: {ids}"


# ============================================================================
# Text cleaning
# ============================================================================

@given(
    parsers.parse('text containing "{url}" and "{emoji}" and "{divider}"'),
    target_fixture="dirty_text",
)
def dirty_text(url: str, emoji: str, divider: str) -> str:
    return f"Some text [site.com] here ✅ and more\n---\nfinal line"


@when("the text cleaner runs", target_fixture="cleaned")
def run_cleaner(dirty_text: str) -> str:
    return clean_text(dirty_text)


@then(parsers.parse('the cleaned text does not contain "{fragment}"'))
def assert_fragment_absent(cleaned: str, fragment: str):
    assert fragment not in cleaned, f"Found '{fragment}' in cleaned text"


@then(parsers.parse('standalone "{divider}" dividers are removed'))
def assert_dividers_removed(cleaned: str, divider: str):
    import re
    assert not re.search(r"^-{3,}$", cleaned, re.MULTILINE), "Found standalone --- in cleaned text"


# ============================================================================
# Near-duplicate detection
# ============================================================================

@given("two observations with near-identical text", target_fixture="dup_observations")
def duplicate_observations() -> list[RawObservation]:
    return [
        RawObservation(
            observation_id=1,
            source_type="Customer VoC",
            text="5-month delay in delivery of full BoQ, customer threatening order cancellation immediately",
            original_excerpt="5-month delay in delivery of full BoQ, customer threatening order cancellation immediately",
        ),
        RawObservation(
            observation_id=2,
            source_type="Customer VoC",
            text="5-month delay in delivery of the full BoQ, customer threatening order cancellation",
            original_excerpt="5-month delay in delivery of the full BoQ, customer threatening order cancellation",
        ),
        RawObservation(
            observation_id=3,
            source_type="Customer VoC",
            text="CXL 3.0 enables fabric-scale memory pooling for AI workloads",
            original_excerpt="CXL 3.0 enables fabric-scale memory pooling for AI workloads",
        ),
    ]


@when("near-duplicate detection runs", target_fixture="duplicate_pairs")
def run_dedup(dup_observations):
    return find_near_duplicates(dup_observations)


@then(parsers.parse("{count:d} duplicate pair is found"))
def assert_duplicate_count(duplicate_pairs, count: int):
    assert len(duplicate_pairs) == count, f"Expected {count} pairs, got {len(duplicate_pairs)}"


@then(parsers.parse("after merging the observation count is reduced by {reduction:d}"))
def assert_merge_reduction(dup_observations, duplicate_pairs, reduction: int):
    merged = merge_duplicates(dup_observations, duplicate_pairs)
    expected = len(dup_observations) - reduction
    assert len(merged) == expected, f"Expected {expected} observations, got {len(merged)}"


# ============================================================================
# Single-source / edge cases
# ============================================================================

@given("a plain VoC text with no source headers", target_fixture="raw_input")
def plain_voc_input() -> str:
    return "Customers are frustrated with long delivery times and lack of communication."


@then(parsers.parse('{count:d} segment is detected with source type "{source_type}"'))
def assert_single_segment(segments, count: int, source_type: str):
    assert len(segments) == count
    assert segments[0].source_type == source_type


@given("text with a source header but no content after it", target_fixture="raw_input")
def empty_segment_input() -> str:
    return "From Customer Comments:\n"


@then(parsers.parse("{count:d} segment is detected"))
def assert_segment_detected(segments, count: int):
    assert len(segments) == count


@then("the segment body is empty")
def assert_empty_body(segments):
    assert segments[0].body == ""


# ============================================================================
# Product-to-BU mapping
# ============================================================================

@given(
    parsers.parse('an observation mentioning "{product}"'),
    target_fixture="bu_text",
)
def observation_with_product(product: str) -> str:
    return f"Issues with {product} delivery in EMEA region."


@when("the product-to-BU mapper runs", target_fixture="bu_result")
def run_bu_mapper(bu_text: str) -> str:
    return lookup_bu(bu_text)


@then(parsers.parse('the business unit is "{expected_bu}"'))
def assert_bu(bu_result: str, expected_bu: str):
    assert bu_result == expected_bu, f"Expected BU '{expected_bu}', got '{bu_result}'"


# ============================================================================
# JTBD framing
# ============================================================================

@given("a preprocessed result with JTBD metadata", target_fixture="jtbd_metadata")
def preprocessed_jtbd_metadata() -> list[ObservationMetadata]:
    return [
        ObservationMetadata(
            observation_id=1,
            source_type="Customer VoC",
            text="Delivery delays of 5 months",
            original_excerpt="Delivery delays of 5 months",
            products=["ProLiant DL380"],
            theater="EMEA",
            business_unit="HPE Compute",
            jtbd="Receive ordered hardware within committed delivery window",
            date_references=["April 2025"],
            sentiment="Negative",
        ),
        ObservationMetadata(
            observation_id=2,
            source_type="Industry Analysis",
            text="DRAM supply constrained",
            original_excerpt="DRAM supply constrained",
            products=[],
            theater="Global",
            business_unit="Cross-BU",
            jtbd="Maintain affordable access to memory components",
            date_references=["2026"],
            sentiment="Negative",
        ),
    ]


@then('no JTBD field starts with "HPE"')
def assert_jtbd_customer_framing(jtbd_metadata: list[ObservationMetadata]):
    for obs in jtbd_metadata:
        assert not obs.jtbd.startswith("HPE"), (
            f"JTBD should use customer framing, not vendor: '{obs.jtbd}'"
        )


# ============================================================================
# Step1a integration
# ============================================================================

@given("a workflow state with preprocessed_voc_data set", target_fixture="state_with_preprocessed")
def state_with_preprocessed() -> BMIWorkflowState:
    return {
        "session_id": "test-preprocess-001",
        "current_step": "preprocess_voc",
        "input_type": "text",
        "llm_backend": "azure",
        "voc_data": "raw text here",
        "preprocessed_voc_data": "=== PREPROCESSED INPUT (3 observations) ===\n[1] test obs",
    }


@given("a workflow state without preprocessed_voc_data", target_fixture="state_without_preprocessed")
def state_without_preprocessed() -> BMIWorkflowState:
    return {
        "session_id": "test-preprocess-002",
        "current_step": "ingest",
        "input_type": "text",
        "llm_backend": "azure",
        "voc_data": "Customers delay onboarding because the current process is too complex",
    }


@when("the Step 1a prompt is built", target_fixture="prompt_messages")
def build_prompt(request):
    # Determine which fixture to use
    state = None
    for fixture_name in ("state_with_preprocessed", "state_without_preprocessed"):
        try:
            state = request.getfixturevalue(fixture_name)
            break
        except Exception:
            continue
    assert state is not None

    preprocessed = state.get("preprocessed_voc_data")
    if preprocessed:
        return _build_messages(preprocessed, is_preprocessed=True)
    else:
        return _build_messages(state.get("voc_data", ""), is_preprocessed=False)


@then(parsers.parse('the user prompt contains "{fragment}"'))
def assert_prompt_contains(prompt_messages, fragment: str):
    user_msg = prompt_messages[-1].content
    assert fragment.lower() in user_msg.lower(), (
        f"Expected '{fragment}' in user prompt, got: {user_msg[:200]}..."
    )


# ============================================================================
# Full pipeline
# ============================================================================

def _mock_llm_for_preprocessing(observations_count: int):
    """Create a mock LLM that returns valid PreprocessingResult."""
    mock_llm = MagicMock()
    mock_structured = MagicMock()
    mock_llm.with_structured_output.return_value = mock_structured

    mock_observations = [
        ObservationMetadata(
            observation_id=i,
            source_type="Customer VoC" if i <= 3 else "Industry Analysis",
            text=f"Test observation {i}",
            original_excerpt=f"Test observation {i}",
            products=["ProLiant DL380"] if i <= 2 else [],
            theater="EMEA" if i <= 2 else "Global",
            business_unit="HPE Compute" if i <= 2 else "Cross-BU",
            jtbd=f"Accomplish customer job {i}",
            date_references=["2026"],
            sentiment="Negative" if i <= 3 else "Neutral",
        )
        for i in range(1, observations_count + 1)
    ]
    mock_structured.invoke.return_value = PreprocessingResult(
        observations=mock_observations
    )
    return mock_llm


@when("the full preprocessing pipeline runs", target_fixture="pipeline_result")
def run_full_pipeline(raw_input: str):
    state: BMIWorkflowState = {
        "session_id": "test-pipeline-001",
        "current_step": "ingest",
        "input_type": "text",
        "llm_backend": "azure",
        "voc_data": raw_input,
    }

    # Count how many observations the rule-based phase would produce
    segments = detect_segments(raw_input)
    observations = reindex_observations(segments)
    obs_count = len(observations)

    mock_llm = _mock_llm_for_preprocessing(obs_count)
    return run_preprocessing(state, mock_llm)


@then(parsers.parse('the preprocessed output contains "{fragment}"'))
def assert_preprocessed_contains(pipeline_result: BMIWorkflowState, fragment: str):
    preprocessed = pipeline_result.get("preprocessed_voc_data", "")
    assert fragment in preprocessed, (
        f"Expected '{fragment}' in preprocessed output, got: {preprocessed[:300]}..."
    )


@then("the preprocessing metadata has a positive total_observations count")
def assert_positive_observations(pipeline_result: BMIWorkflowState):
    metadata = pipeline_result.get("preprocessing_metadata", {})
    assert metadata.get("total_observations", 0) > 0


@then("the observation index is a non-empty list")
def assert_observation_index(pipeline_result: BMIWorkflowState):
    index = pipeline_result.get("observation_index", [])
    assert isinstance(index, list)
    assert len(index) > 0
