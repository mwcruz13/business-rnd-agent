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
    And the workflow state contains an agent recommendation

  Scenario: Step 1 extracts a multi-signal radar from firmware assessment VoC
    Given a workflow state with the firmware assessment VoC sample
    When the Step 1 signal scanner node runs
    Then the workflow state contains at least 6 detected signals
    And the detected signals include "Competitors are shifting firmware assessment toward automated self-serve delivery"
    And the detected signals include "A lower-cost self-serve offer can unlock SMB and edge nonconsumers"
    And every interpreted signal only uses SOC Radar filter names
    And the first interpreted signal uses the classification "Disruptive — New-Market"
    And the first priority matrix entry has a score of 9
    And the first priority matrix entry uses the tier "Act"
    And the workflow state contains coverage gaps
