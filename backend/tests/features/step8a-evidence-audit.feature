Feature: Step 8a evidence audit
  The Step 8a workflow node must audit each Test-first assumption against the upstream VoC and signal context before selecting experiments.

  Scenario: Step 8a classifies delivery-delay evidence as weak when VoC complaints exist
    Given a workflow state with test-first assumptions and delivery-delay VoC evidence
    When the Step 8a evidence audit node runs
    Then the workflow current step is "evidence_audit"
    And the workflow state contains assumption evidence audits
    And the delivery-delay assumption is classified as "Weak"
    And the delivery-delay audit includes a non-empty evidence summary

  Scenario: Step 8a classifies silent assumptions as none
    Given a workflow state with test-first assumptions and delivery-delay VoC evidence
    When the Step 8a evidence audit node runs
    Then the CXL adoption assumption is classified as "None"

  Scenario: Step 8a audits every test-first assumption
    Given a workflow state with test-first assumptions and delivery-delay VoC evidence
    When the Step 8a evidence audit node runs
    Then the audit count matches the number of test-first assumptions

  Scenario: Step 8a falls back to Step 7 voc evidence strength when no LLM is available
    Given a workflow state with test-first assumptions and delivery-delay VoC evidence
    When the Step 8a evidence audit node runs without an LLM
    Then the workflow current step is "evidence_audit"
    And the delivery-delay assumption is classified as "Weak"
    And the CXL adoption assumption is classified as "None"
