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
    And the workflow state contains structured experiment cards

  Scenario: Step 8 produces interactive experiment card objects
    Given a workflow state with completed Step 7 risk outputs
    When the Step 8 PDSA experiment designer node runs
    Then each experiment card has a unique id and correct structure
    And each experiment card matches a top assumption
    And each experiment card starts with planned status and empty evidence
    And experiment card evidence can be updated with valid Zone B fields
    And experiment card rejects updates to Zone A fields

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

  Scenario: Step 8 reads structured data instead of parsing markdown
    Given a workflow state with completed Step 7 risk outputs including structured data
    When the Step 8 PDSA experiment designer node runs
    Then the experiment cards reference assumptions from the structured step 7 output
    And the experiment card count matches the number of test-first assumptions in structured output

  Scenario: Step 8 falls back to markdown parsing when structured data is absent
    Given a workflow state with Step 7 markdown output but no structured data
    When the Step 8 PDSA experiment designer node runs
    Then the workflow state contains experiment selections
    And the workflow state contains structured experiment cards

  Scenario: Step 8 produces empty artifacts when no test-first assumptions exist
    Given a workflow state with Step 7 output containing zero test-first assumptions
    When the Step 8 PDSA experiment designer node runs
    Then the workflow state contains empty experiment selections
    And the workflow state contains empty experiment cards
    And the workflow current step is "pdsa_plan"