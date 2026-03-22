Feature: Checkpoint decisions
  The workflow must only accept approve, edit, or retry as checkpoint decisions.

  Scenario Outline: Accept supported checkpoint decisions
    When the checkpoint decision "<decision>" is validated
    Then the validated checkpoint decision is "<decision>"

    Examples:
      | decision |
      | approve  |
      | edit     |
      | retry    |

  Scenario: Reject unsupported checkpoint decisions
    When the checkpoint decision "skip" is validated
    Then checkpoint validation fails with message "Unsupported decision: skip"
