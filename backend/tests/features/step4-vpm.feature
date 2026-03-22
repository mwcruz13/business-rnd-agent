Feature: Step 4 VPM synthesizer
  The fourth workflow node must transform the Step 3 empathy profile into measurable success drivers and problem framing.

  Scenario: Step 4 prepares value drivers and actionable insights from the empathy profile
    Given a workflow state with a completed Step 3 empathy profile
    When the Step 4 VPM synthesizer node runs
    Then the workflow current step is "measure_define"
    And the customer profile is preserved in the workflow state
    And the workflow state contains a value driver tree
    And the workflow state contains actionable insights

  Scenario: Step 4 returns CXIF Measure and Define structures
    Given a workflow state with a completed Step 3 empathy profile
    When the Step 4 VPM synthesizer node runs
    Then the value driver tree uses the CXIF measure headings
    And the actionable insights use the CXIF define headings
    And the value driver tree includes the approved pattern context
    And the actionable insights include a WHO-DOES-BECAUSE-BUT statement