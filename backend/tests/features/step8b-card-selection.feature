Feature: Step 8b card selection
  Step 8b must select evidence-aware experiment card candidates from the canonical 44-card library.

  Scenario: Step 8b differentiates same-category assumptions by content
    Given a workflow state with audited assumptions ready for card selection
    When the Step 8b card selection node runs
    Then the workflow current step is "card_selection"
    And the workflow state contains experiment card selections
    And the two desirability assumptions have different primary cards

  Scenario: Step 8b skips weak cards when weak evidence already exists
    Given a workflow state with audited assumptions ready for card selection
    When the Step 8b card selection node runs
    Then the feasibility assumption with weak prior evidence starts at medium or strong

  Scenario: Step 8b selections use only canonical card names and include rationale
    Given a workflow state with audited assumptions ready for card selection
    When the Step 8b card selection node runs
    Then every selected card name exists in the experiment library
    And each assumption has between 3 and 5 candidates
    And each candidate includes rationale text

  Scenario: Step 8b falls back to deterministic evidence-gated selection without an LLM
    Given a workflow state with audited assumptions ready for card selection
    When the Step 8b card selection node runs without an LLM
    Then the workflow current step is "card_selection"
    And each assumption has between 3 and 5 candidates
