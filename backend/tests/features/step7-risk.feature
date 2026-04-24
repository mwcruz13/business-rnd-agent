Feature: Step 7 risk mapper
  The seventh workflow node must transform the design outputs into prioritized DVF assumptions using the Precoil EMT format.

  Scenario: Step 7 prepares assumptions from the design outputs
    Given a workflow state with completed Step 6 design outputs
    When the Step 7 risk mapper node runs
    Then the workflow current step is "risk_map"
    And the business model canvas is preserved in the workflow state
    And the workflow state contains assumptions

  Scenario: Step 7 returns Precoil EMT assumption mapping structures
    Given a workflow state with completed Step 6 design outputs
    When the Step 7 risk mapper node runs
    Then the assumptions use the Precoil EMT headings
    And the assumptions include between 6 and 15 formatted assumptions
    And the assumptions include all DVF categories
    And the assumptions include a DVF tension check
    And the assumptions include an importance evidence matrix
    And the assumptions identify at least one test-first risk

  Scenario: Step 7 assumptions use only valid quadrant values
    Given a workflow state with completed Step 6 design outputs
    When the Step 7 risk mapper node runs
    Then every assumption quadrant is one of "Test first, Monitor, Deprioritize, Safe zone"

  Scenario: Step 7 stores structured assumption data alongside markdown
    Given a workflow state with completed Step 6 design outputs
    When the Step 7 risk mapper node runs
    Then the workflow state contains structured step 7 output
    And the structured output has 3 DVF categories with between 2 and 5 assumptions each
    And every structured assumption has a suggested quadrant
    And every structured assumption has a voc evidence strength

  Scenario: Step 7 DVF tensions identify cross-category conflicts
    Given a workflow state with completed Step 6 design outputs
    When the Step 7 risk mapper node runs
    Then the assumptions include at least 1 DVF tension
    And each DVF tension references two assumptions from different categories