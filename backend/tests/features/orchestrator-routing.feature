Feature: Orchestrator routing
  The orchestrator node must route to the correct next worker based on
  completed_steps, and terminate when all milestones are done.

  Scenario: Orchestrator routes to step 1 when no steps completed
    Given a workflow state with no completed steps
    When the orchestrator decides the next step
    Then the next step is "step1_signal"

  Scenario: Orchestrator routes to step 2 after step 1 completed
    Given a workflow state with completed steps "step1_signal"
    When the orchestrator decides the next step
    Then the next step is "step2_pattern"

  Scenario: Orchestrator routes to END after all 8 steps completed
    Given a workflow state with all 8 steps completed
    When the orchestrator decides the next step
    Then the next step is "__end__"

  Scenario: Orchestrator skips to the correct step when resuming mid-workflow
    Given a workflow state with completed steps "step1_signal,step2_pattern,step3_profile"
    When the orchestrator decides the next step
    Then the next step is "step4_vpm"
