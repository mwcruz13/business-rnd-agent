Feature: Workflow checkpoints
  The workflow service must pause at every step's checkpoint, validate consultant edits, and preserve consultant decisions through completion.

  Scenario: A checkpointed workflow pauses at each step and completes after consultant decisions
    Given a checkpointed workflow input describing onboarding friction
    When the consultant starts the checkpointed workflow
    Then the workflow run status is "paused"
    And the pending checkpoint is "checkpoint_1a"
    And the workflow current step is "signal_scan"
    When the consultant approves the current checkpoint
    Then the workflow run status is "paused"
    And the pending checkpoint is "checkpoint_1b"
    And the workflow current step is "signal_recommend"
    When the consultant approves the current checkpoint
    Then the workflow run status is "paused"
    And the pending checkpoint is "checkpoint_2"
    And the workflow current step is "pattern_select"
    When the consultant edits the current checkpoint with direction "invent" pattern "Market Explorers" rationale "Consultant selected the new-market exploration path."
    Then the workflow run status is "paused"
    And the pending checkpoint is "checkpoint_3"
    And the workflow current step is "empathize"
    When the consultant approves the current checkpoint
    Then the workflow run status is "paused"
    And the pending checkpoint is "checkpoint_4"
    And the workflow current step is "measure_define"
    When the consultant approves the current checkpoint
    Then the workflow run status is "paused"
    And the pending checkpoint is "checkpoint_5a"
    And the workflow current step is "vp_ideation"
    When the consultant approves the current checkpoint
    Then the workflow run status is "paused"
    And the pending checkpoint is "checkpoint_5b"
    And the workflow current step is "vp_scoring"
    When the consultant approves the current checkpoint
    Then the workflow run status is "paused"
    And the pending checkpoint is "checkpoint_6"
    And the workflow current step is "design_fit"
    When the consultant approves the current checkpoint
    Then the workflow run status is "paused"
    And the pending checkpoint is "checkpoint_7"
    And the workflow current step is "risk_map"
    When the consultant approves the current checkpoint
    Then the workflow run status is "paused"
    And the pending checkpoint is "checkpoint_8"
    And the workflow current step is "pdsa_plan"
    When the consultant approves the current checkpoint
    Then the workflow run status is "paused"
    And the pending checkpoint is "checkpoint_9"
    And the workflow current step is "pdsa_plan"
    When the consultant approves the current checkpoint
    Then the workflow run status is "completed"
    And no pending checkpoint remains
    And the workflow current step is "pdsa_plan"
    And the final workflow artifacts include the selected pattern "Market Explorers"
    And the final workflow artifacts do not include the unselected pattern "Cost Differentiators"

  Scenario: Checkpoint 1.5 rejects an edit without pattern direction
    Given a checkpointed workflow already paused at the pattern checkpoint
    When the consultant edits the current checkpoint without pattern direction
    Then checkpoint resume fails with message "Checkpoint checkpoint_2 requires pattern_direction before proceeding"

  Scenario: A retry decision reruns the current checkpointed step instead of advancing
    Given a checkpointed workflow input describing onboarding friction
    When the consultant starts the checkpointed workflow
    And the consultant retries the current checkpoint
    Then the workflow run status is "paused"
    And the pending checkpoint is "checkpoint_1a"
    And the workflow current step is "signal_scan"
