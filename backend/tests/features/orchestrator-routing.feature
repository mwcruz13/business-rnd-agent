Feature: Orchestrator routing
  The orchestrator node must route to the correct next worker based on
  completed_steps, and terminate when all milestones are done.

  Scenario: Orchestrator routes to step 1a when no steps completed
    Given a workflow state with no completed steps
    When the orchestrator decides the next step
    Then the next step is "step1a_signal_scan"

  Scenario: Orchestrator routes to step 1b after step 1a completed
    Given a workflow state with completed steps "step1a_signal_scan"
    When the orchestrator decides the next step
    Then the next step is "step1b_signal_recommend"

  Scenario: Orchestrator routes to step 2 after step 1a and 1b completed
    Given a workflow state with completed steps "step1a_signal_scan,step1b_signal_recommend"
    When the orchestrator decides the next step
    Then the next step is "step2_pattern"

  Scenario: Orchestrator routes to END after all workflow steps completed
    Given a workflow state with all workflow steps completed
    When the orchestrator decides the next step
    Then the next step is "__end__"

  Scenario: Orchestrator skips to the correct step when resuming mid-workflow
    Given a workflow state with completed steps "step1a_signal_scan,step1b_signal_recommend,step2_pattern,step3_profile"
    When the orchestrator decides the next step
    Then the next step is "step4_vpm"
