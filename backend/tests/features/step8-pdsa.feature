Feature: Step 8 PDSA experiment designer
  The eighth workflow node must transform the top Step 7 risks into canonical Testing Business Ideas experiment recommendations, plans, and worksheets.

  Scenario: Step 8 prepares experiment artifacts from the top risk assumptions
    Given a workflow state with completed Step 7 risk outputs
    When the Step 8 PDSA experiment designer node runs
    Then the workflow current step is "pdsa_plan"
    And the assumptions are preserved in the workflow state
    And the workflow state contains experiment selections
    And the workflow state contains experiment plans
    And the workflow state contains experiment worksheets

  Scenario: Step 8 uses canonical experiment cards and documented artifact formats
    Given a workflow state with completed Step 7 risk outputs
    When the Step 8 PDSA experiment designer node runs
    Then the experiment selections use the Testing Business Ideas selection headings
    And the experiment selections recommend canonical cards for each top assumption
    And the first recommended experiments are weak evidence cards
    And the experiment plans use the Precoil brief headings
    And the experiment plans include implementation plans and evidence sequences
    And the experiment worksheets use the Testing Business Ideas worksheet headings
    And the experiment artifacts reproduce the exact top assumptions