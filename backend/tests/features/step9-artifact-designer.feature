Feature: Step 9 artifact designer
  Step 9 must convert experiment cards into concrete, build-ready artifact definitions.

  Scenario: Step 9 emits artifact designs for each experiment card
    Given a workflow state with experiment cards ready for artifact design
    When the Step 9 artifact designer node runs
    Then the workflow current step is "pdsa_plan"
    And the workflow state contains artifact designs
    And each artifact design includes a concrete artifact name
    And each artifact design includes a deliverable checklist
