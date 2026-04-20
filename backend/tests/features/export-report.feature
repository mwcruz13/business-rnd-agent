Feature: Report export
  The export pipeline must produce complete reports that include all
  workflow artifacts, including experiment card evidence.

  Scenario: Markdown export includes all step outputs
    Given a completed workflow run with all 8 steps
    When the markdown report is generated
    Then the report includes a Step 1 signal scan section
    And the report includes a Step 2 pattern rationale
    And the report includes a Step 3 customer profile section
    And the report includes a Step 6 fit assessment section
    And the report includes a Step 8 experiment selections section

  Scenario: Markdown export includes experiment card evidence
    Given a completed workflow run with experiment card evidence captured
    When the markdown report is generated
    Then the report includes experiment card status and evidence fields
    And the report includes the evidence decision for each card

  Scenario: Markdown export works for partial runs
    Given a workflow run paused at step 3
    When the markdown report is generated
    Then the report includes steps 1 through 3 only
    And the report does not include step 4 or later sections
