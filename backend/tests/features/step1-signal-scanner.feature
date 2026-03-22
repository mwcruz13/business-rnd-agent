Feature: Step 1 signal scanner
  The first workflow node must transform raw VoC input into the structured Step 1 state required by the rest of the BMI pipeline.

  Scenario: Step 1 prepares structured signal outputs from VoC input
    Given a workflow state with VoC data "Customers delay onboarding because the current process is too complex"
    When the Step 1 signal scanner node runs
    Then the workflow current step is "signal_scan"
    And the original VoC data is preserved in the workflow state
    And the workflow state contains a signals list
    And the workflow state contains an interpreted signals list
    And the workflow state contains a priority matrix list

  Scenario: Step 1 classifies onboarding friction using the SOC Radar library
    Given a workflow state with VoC data "Customers delay onboarding because the current process is too complex"
    When the Step 1 signal scanner node runs
    Then the first detected signal uses the zone "Overserved Customers"
    And the first interpreted signal uses the classification "Disruptive — Low-End"
    And the interpreted signal only uses SOC Radar filter names
    And the first priority matrix entry has a score of 4
    And the first priority matrix entry uses the tier "Investigate"
