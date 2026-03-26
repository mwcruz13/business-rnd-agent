Feature: Workflow orchestrator
  The workflow service must execute the full LangGraph pipeline from raw VoC input through Step 8 outputs.

  Scenario: The LangGraph orchestrator completes the workflow from raw VoC input
    Given a VoC input describing onboarding friction
    When the consultant runs the workflow through the LangGraph orchestrator
    Then the workflow run status is "completed"
    And the workflow current step is "pdsa_plan"
    And the workflow state contains Step 8 experiment artifacts
