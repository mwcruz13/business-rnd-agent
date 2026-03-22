Feature: Step 2 pattern matcher
  The second workflow node must transform Step 1 signal outputs into a pattern-direction recommendation for the consultant checkpoint.

  Scenario: Step 2 prepares a recommendation from interpreted signals
    Given a workflow state with interpreted signals from Step 1
    When the Step 2 pattern matcher node runs
    Then the workflow current step is "pattern_select"
    And the interpreted signals are preserved in the workflow state
    And the workflow state contains an agent recommendation

  Scenario: Step 2 recommends shift without inventing unavailable SHIFT patterns
    Given a workflow state with interpreted signals from Step 1
    When the Step 2 pattern matcher node runs
    Then the agent recommendation says to explore SHIFT first
    And the agent recommendation includes "pending_library_source"
    And Step 2 does not set the consultant checkpoint fields

  Scenario: Step 2 recommends an INVENT pattern for a new-market signal
    Given a workflow state with a new-market interpreted signal from Step 1
    When the Step 2 pattern matcher node runs
    Then the agent recommendation says to explore INVENT first
    And the agent recommendation references the verified INVENT pattern "Market Explorers"
    And Step 2 does not set the consultant checkpoint fields
