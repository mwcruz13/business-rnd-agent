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

  Scenario: Step 1 output passes structural compliance checks
    Given a workflow state with the firmware assessment VoC sample
    When the Step 1 signal scanner node runs
    Then the workflow state contains at least 1 detected signals
    And every signal zone is a valid SOC Radar zone
    And every interpreted signal only uses SOC Radar filter names
    And every interpreted signal uses a valid classification
    And every priority score equals impact times speed
    And every priority tier matches its score range
    And the workflow state contains coverage gaps

  Scenario: Step 1 produces a quality-assessed signal scan from firmware assessment VoC
    Given a workflow state with the firmware assessment VoC sample
    When the Step 1 signal scanner node runs
    And the LLM judge evaluates the signal scan against the SOC Radar SKILL
    Then the judge completeness score is at least 3
    And the judge relevance score is at least 4
    And the judge groundedness score is at least 4
    And the judge SKILL compliance score is at least 3
