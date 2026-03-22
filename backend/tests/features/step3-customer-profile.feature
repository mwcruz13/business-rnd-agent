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
    And the customer profile includes at least 3 customer jobs
    And the customer profile includes at least 3 customer pains
    And the customer profile includes at least 3 customer gains
