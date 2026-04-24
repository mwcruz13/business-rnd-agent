Feature: Step 5a VP Portfolio Ideation
  The Step 5a node generates multiple distinct Value Proposition alternatives
  that are coherent with the business model patterns selected upstream in Step 2.

  Scenario: Step 5a generates the configured number of VP alternatives
    Given a workflow state with completed Step 4 outputs and pattern context
    When the Step 5a ideation node runs
    Then the workflow current step is "vp_ideation"
    And the workflow state contains vp_alternatives
    And the number of VP alternatives matches the configured count

  Scenario: Each VP alternative is pattern-coherent
    Given a workflow state with completed Step 4 outputs and pattern context
    When the Step 5a ideation node runs
    Then each VP alternative declares a pattern flavor applied
    And each VP alternative includes a pattern coherence note
    And each VP alternative references the selected patterns

  Scenario: VP alternatives have complete Value Map structure
    Given a workflow state with completed Step 4 outputs and pattern context
    When the Step 5a ideation node runs
    Then each VP alternative includes at least 1 product or service
    And each VP alternative includes at least 1 pain reliever
    And each VP alternative includes at least 1 gain creator
    And each VP alternative includes an ad-lib prototype

  Scenario: VP alternatives are diverse across ideation axes
    Given a workflow state with completed Step 4 outputs and pattern context
    When the Step 5a ideation node runs
    Then the VP alternatives have distinct names
    And the VP alternatives target different primary job focuses
    And the ideation output includes a diversity check

  Scenario: Step 5a populates combined value_proposition_canvas for backward compatibility
    Given a workflow state with completed Step 4 outputs and pattern context
    When the Step 5a ideation node runs
    Then the workflow state contains a value proposition canvas
    And the value proposition canvas includes headings for each VP alternative
