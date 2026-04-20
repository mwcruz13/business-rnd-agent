Feature: Step 6 design canvas
  The sixth workflow node must transform the value proposition canvas into a business model canvas and fit assessment.

  Scenario: Step 6 prepares design outputs from the value proposition canvas
    Given a workflow state with a completed Step 5 value proposition canvas
    When the Step 6 design canvas node runs
    Then the workflow current step is "design_fit"
    And the value proposition canvas is preserved in the workflow state
    And the workflow state contains a business model canvas
    And the workflow state contains a fit assessment

  Scenario: Step 6 returns CXIF business model and fit structures
    Given a workflow state with a completed Step 5 value proposition canvas
    When the Step 6 design canvas node runs
    Then the business model canvas uses the CXIF business model headings
    And the fit assessment uses the CXIF fit assessment headings
    And the business model canvas includes the approved pattern context
    And the fit assessment includes problem-solution fit rows
    And the fit assessment includes product-market and business-model status tables

  Scenario: Step 6 business model canvas contains all 9 BMC building blocks
    Given a workflow state with a completed Step 5 value proposition canvas
    When the Step 6 design canvas node runs
    Then the business model canvas contains all 9 standard BMC building blocks
    And the desirability section contains "Customer Segments, Value Proposition, Channels, Customer Relationships"
    And the feasibility section contains "Key Partnerships, Key Activities, Key Resources"
    And the viability section contains "Revenue Streams, Cost Structure"

  Scenario: Step 6 fit assessment includes all three fit levels
    Given a workflow state with a completed Step 5 value proposition canvas
    When the Step 6 design canvas node runs
    Then the fit assessment includes a problem-solution fit section
    And the fit assessment includes a product-market fit section
    And the fit assessment includes a business-model fit section