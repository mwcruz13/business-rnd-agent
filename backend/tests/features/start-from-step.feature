Feature: Start workflow from any step
  Consultants can enter the workflow at any step by providing
  pre-filled upstream state. The system validates that all
  required upstream fields are present before execution begins.

  Scenario: Starting at step 1 requires only voc_data
    Given initial state with voc_data "Customer onboarding is slow"
    When the workflow is started from step 1
    Then the run status is "paused"
    And the pending checkpoint is "checkpoint_1"

  Scenario: Starting at step 2 with complete upstream state succeeds
    Given initial state with upstream fields for step 2
    When the workflow is started from step 2
    Then the run status is "paused"
    And the pending checkpoint is "checkpoint_2"

  Scenario: Starting at step 3 with complete upstream state succeeds
    Given initial state with upstream fields for step 3
    When the workflow is started from step 3
    Then the run status is "paused"
    And the pending checkpoint is "checkpoint_3"

  Scenario: Starting at step 3 without required fields fails
    Given initial state with voc_data "Customer onboarding is slow"
    When the workflow is started from step 3
    Then the start is rejected with a message containing "missing required upstream state"

  Scenario: Starting at step 4 with complete upstream state succeeds
    Given initial state with upstream fields for step 4
    When the workflow is started from step 4
    Then the run status is "paused"
    And the pending checkpoint is "checkpoint_4"

  Scenario: Starting at step 5 with complete upstream state succeeds
    Given initial state with upstream fields for step 5
    When the workflow is started from step 5
    Then the run status is "paused"
    And the pending checkpoint is "checkpoint_5a"

  Scenario: Starting at step 6 with complete upstream state succeeds
    Given initial state with upstream fields for step 6
    When the workflow is started from step 6
    Then the run status is "paused"
    And the pending checkpoint is "checkpoint_6"

  Scenario: Starting at step 7 with complete upstream state succeeds
    Given initial state with upstream fields for step 7
    When the workflow is started from step 7
    Then the run status is "paused"
    And the pending checkpoint is "checkpoint_7"

  Scenario: Starting at step 8 with complete upstream state succeeds
    Given initial state with upstream fields for step 8
    When the workflow is started from step 8
    Then the run status is "paused"
    And the pending checkpoint is "checkpoint_8"

  Scenario: Starting at step 0 is rejected
    Given initial state with voc_data "Customer onboarding is slow"
    When the workflow is started from step 0
    Then the start is rejected with a message containing "step_number must be between 1 and 9"

  Scenario: Starting at step 9 with complete upstream state succeeds
    Given initial state with upstream fields for step 9
    When the workflow is started from step 9
    Then the run status is "paused"
    And the pending checkpoint is "checkpoint_9"

  Scenario: Starting at step 10 is rejected
    Given initial state with voc_data "Customer onboarding is slow"
    When the workflow is started from step 10
    Then the start is rejected with a message containing "step_number must be between 1 and 9"
