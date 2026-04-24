Feature: Step 8c path sequencing
  Step 8c must convert Step 8b card selections into coherent 3-card experiment paths.

  Scenario: Step 8c outputs three cards per assumption in non-decreasing evidence order
    Given a workflow state with experiment card selections ready for path sequencing
    When the Step 8c path sequencing node runs
    Then the workflow current step is "path_sequencing"
    And the workflow state contains experiment paths
    And each assumption path has exactly 3 cards
    And each path is non-decreasing by evidence strength

  Scenario: Step 8c uses only cards from Step 8b candidates
    Given a workflow state with experiment card selections ready for path sequencing
    When the Step 8c path sequencing node runs
    Then each path card is selected from that assumption candidate list

  Scenario: Step 8c falls back to deterministic sequencing without an LLM
    Given a workflow state with experiment card selections ready for path sequencing
    When the Step 8c path sequencing node runs without an LLM
    Then the workflow current step is "path_sequencing"
    And each assumption path has exactly 3 cards
