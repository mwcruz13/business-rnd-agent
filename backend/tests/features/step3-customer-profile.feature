Feature: Step 3 customer profile builder
  The third workflow node must turn the approved pattern direction into a customer profile grounded in the earlier signal analysis.

  Scenario: Step 3 prepares a customer profile from approved direction and patterns
    Given a workflow state with a consultant-approved pattern direction
    When the Step 3 customer profile node runs
    Then the workflow current step is "empathize"
    And the selected patterns are preserved in the workflow state
    And the workflow state contains a customer profile

  Scenario: Step 3 returns a CXIF empathy profile structure
    Given a workflow state with a consultant-approved pattern direction
    When the Step 3 customer profile node runs
    Then the customer profile uses the CXIF empathy headings
    And the customer profile includes the selected pattern context
    And the customer profile includes at least 1 customer jobs
    And the customer profile includes at least 1 customer pains
    And the customer profile includes at least 1 customer gains

  Scenario: Step 3 empathy gate fires when a profile section is empty
    Given a customer empathy profile with an empty gains section
    When the empathy gate evaluates the profile
    Then the gate produces CXIF trigger questions for the gains section

  Scenario: Step 3 retry with supplemental VoC skips the gate
    Given a workflow state with supplemental VoC from the consultant
    When the Step 3 customer profile node runs
    Then the workflow current step is "empathize"
    And the workflow state contains a customer profile
    And the workflow state does not contain empathy gap questions
