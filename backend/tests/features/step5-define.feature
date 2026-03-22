Feature: Step 5 define model
  The fifth workflow node must transform the empathy and problem framing outputs into a value proposition canvas.

  Scenario: Step 5 prepares a value proposition canvas from prior context
    Given a workflow state with completed Step 4 outputs
    When the Step 5 define model node runs
    Then the workflow current step is "value_proposition"
    And the actionable insights are preserved in the workflow state
    And the workflow state contains a value proposition canvas

  Scenario: Step 5 returns the CXIF value proposition canvas structure
    Given a workflow state with completed Step 4 outputs
    When the Step 5 define model node runs
    Then the value proposition canvas uses the CXIF value map headings
    And the value proposition canvas includes the approved pattern context
    And the value proposition canvas maps pain relievers to customer pains
    And the value proposition canvas maps gain creators to customer gains
    And the value proposition canvas includes at least 2 ad-lib prototypes