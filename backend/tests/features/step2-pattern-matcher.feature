Feature: Step 2 hybrid pattern matcher
  The second workflow node uses a hybrid approach (deterministic shortlist
  plus optional LLM reasoning) to recommend business model patterns from
  the Strategyzer library for the consultant checkpoint.

  Scenario: Step 2 prepares a recommendation from interpreted signals
    Given a workflow state with interpreted signals from Step 1
    When the Step 2 pattern matcher node runs
    Then the workflow current step is "pattern_select"
    And the interpreted signals are preserved in the workflow state
    And the workflow state contains an agent recommendation

  Scenario: Step 2 recommends SHIFT patterns for a low-end overserved signal
    Given a workflow state with interpreted signals from Step 1
    When the Step 2 pattern matcher node runs
    Then the agent recommendation says to explore SHIFT first
    And Step 2 pre-fills pattern direction as "shift"
    And Step 2 selects patterns from the SHIFT library
    And the selected patterns are verified library entries

  Scenario: Step 2 recommends INVENT patterns for a new-market signal
    Given a workflow state with a new-market interpreted signal from Step 1
    When the Step 2 pattern matcher node runs
    Then the agent recommendation says to explore INVENT first
    And Step 2 pre-fills pattern direction as "invent"
    And Step 2 selects patterns from the INVENT library
    And the selected patterns include "Market Explorers"
    And the selected patterns are verified library entries
