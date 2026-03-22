Feature: CSV ingestion
  The backend must load CSV survey exports into rows keyed by header names.

  Scenario: Load survey rows from a CSV file
    Given a CSV file with headers "Reference,Overall Comments"
    And a CSV row "ACME-1,Slow onboarding"
    And a CSV row "ACME-2,Helpful support"
    When the CSV ingestion loader reads the CSV file
    Then 2 CSV rows are loaded
    And CSV row 1 column "Reference" is "ACME-1"
    And CSV row 2 column "Overall Comments" is "Helpful support"
