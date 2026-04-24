Feature: Step 5b VP Scoring
  The Step 5b node evaluates and ranks VP alternatives from Step 5a on
  desirability criteria aligned with Strategyzer Value Proposition Design.

  Scenario: Step 5b scores all VP alternatives
    Given a workflow state with completed Step 5a VP alternatives
    When the Step 5b scoring node runs
    Then the workflow current step is "vp_scoring"
    And the workflow state contains vp_rankings
    And the number of rankings matches the number of VP alternatives

  Scenario: Each ranking includes all five scoring criteria
    Given a workflow state with completed Step 5a VP alternatives
    When the Step 5b scoring node runs
    Then each ranking includes a coverage score
    And each ranking includes an evidence score
    And each ranking includes a pattern fit score
    And each ranking includes a differentiation score
    And each ranking includes a testability score
    And each ranking includes an overall recommendation

  Scenario: Step 5b provides LLM recommendations
    Given a workflow state with completed Step 5a VP alternatives
    When the Step 5b scoring node runs
    Then the workflow state contains vp_recommended indices
    And the vp_recommended indices are valid alternative indices
    And the vp_rankings include a comparative summary
