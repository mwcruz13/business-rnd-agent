Feature: VoC input preprocessing
  The preprocessing step segments multi-source text, cleans artifacts,
  re-indexes observations sequentially, and enriches each observation
  with metadata (source type, products, theater, BU, JTBD).

  # -------------------------------------------------------------------
  # Phase 1 — Rule-based segmentation and cleaning (deterministic)
  # -------------------------------------------------------------------

  Scenario: Multi-source text is segmented by source type
    Given a raw VoC input with 4 distinct source headers
    When the rule-based segmentation runs
    Then 4 segments are detected
    And the segment source types include "Customer VoC" and "Industry Analysis"

  Scenario: Observations are numbered sequentially across segments
    Given a raw VoC input with 4 distinct source headers
    When the rule-based segmentation runs
    And observations are re-indexed
    Then observation IDs are sequential starting from 1 with no gaps

  Scenario: URL references and formatting artifacts are stripped
    Given text containing "[site.com]" and "✅" and "---"
    When the text cleaner runs
    Then the cleaned text does not contain "[site.com]"
    And the cleaned text does not contain "✅"
    And standalone "---" dividers are removed

  Scenario: Near-duplicate observations are merged
    Given two observations with near-identical text
    When near-duplicate detection runs
    Then 1 duplicate pair is found
    And after merging the observation count is reduced by 1

  Scenario: Single-source input with no headers
    Given a plain VoC text with no source headers
    When the rule-based segmentation runs
    Then 1 segment is detected with source type "Unknown"

  Scenario: Empty segment body after header is handled gracefully
    Given text with a source header but no content after it
    When the rule-based segmentation runs
    Then 1 segment is detected
    And the segment body is empty

  # -------------------------------------------------------------------
  # Phase 2 — LLM metadata extraction
  # -------------------------------------------------------------------

  Scenario: BU is tagged from product mention
    Given an observation mentioning "ProLiant DL380"
    When the product-to-BU mapper runs
    Then the business unit is "HPE Compute"

  Scenario: BU defaults to Unknown for unrecognized products
    Given an observation mentioning "FooBar 9000"
    When the product-to-BU mapper runs
    Then the business unit is "Unknown"

  Scenario: JTBD uses customer framing not vendor framing
    Given a preprocessed result with JTBD metadata
    Then no JTBD field starts with "HPE"

  # -------------------------------------------------------------------
  # Integration with step1a
  # -------------------------------------------------------------------

  Scenario: Step1a consumes preprocessed_voc_data when available
    Given a workflow state with preprocessed_voc_data set
    When the Step 1a prompt is built
    Then the user prompt contains "preprocessed"

  Scenario: Step1a falls back to voc_data when preprocessed is absent
    Given a workflow state without preprocessed_voc_data
    When the Step 1a prompt is built
    Then the user prompt contains "Voice of Customer"

  # -------------------------------------------------------------------
  # Full preprocessing pipeline
  # -------------------------------------------------------------------

  Scenario: Full preprocessing produces valid structured output
    Given a raw VoC input with 4 distinct source headers
    When the full preprocessing pipeline runs
    Then the preprocessed output contains "=== PREPROCESSED INPUT"
    And the preprocessed output contains "METADATA SUMMARY"
    And the preprocessing metadata has a positive total_observations count
    And the observation index is a non-empty list
