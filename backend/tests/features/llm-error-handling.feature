Feature: LLM error handling
  The workflow must handle LLM failures gracefully rather than crashing silently.

  Scenario: Step node retries on LLM structured output failure
    Given a workflow state with VoC data "Customers need faster onboarding"
    And the LLM is configured to fail on the first call then succeed
    When the Step 1 signal scanner node runs
    Then the workflow state contains a signals list
    And the LLM was called exactly 2 times

  Scenario: Step node raises a clear error after max retries exhausted
    Given a workflow state with VoC data "Customers need faster onboarding"
    And the LLM is configured to always fail
    When the Step 1 signal scanner node runs expecting failure
    Then the error message indicates an LLM failure
    And the error message names the step that failed
