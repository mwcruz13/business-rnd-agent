Feature: Worker abstraction layer
  Every BMI milestone step must execute through a consistent worker
  interface so that the orchestrator and workflow service interact with
  workers uniformly — regardless of whether the worker uses an LLM or
  deterministic logic internally.

  Scenario: Every registered worker has a valid name and step number
    Given the worker registry
    Then every worker has a non-empty name matching a known step
    And every worker has a step number between 1 and 8
    And no two workers share the same name or step number

  Scenario: Registry returns workers in workflow order
    Given the worker registry
    When I list all workers in order
    Then the worker names match the workflow step order exactly

  Scenario: Registry resolves a worker by step name
    Given the worker registry
    When I look up the worker for "step1_signal"
    Then the returned worker name is "step1_signal"
    And the returned worker step number is 1

  Scenario: Worker execute returns valid state updates
    Given a minimal workflow state for step 1
    When the step1_signal worker executes
    Then the returned state contains "signals"
    And the returned state contains "interpreted_signals"
    And the returned state contains "priority_matrix"
    And the returned state contains "agent_recommendation"

  Scenario: Worker run tracks completion
    Given a minimal workflow state for step 1
    When the step1_signal worker runs
    Then "step1_signal" is in the completed_steps list
