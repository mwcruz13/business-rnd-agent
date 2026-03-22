Feature: Plain text ingestion
  The backend must load plain-text VoC input files so the workflow can start from consultant-provided documents.

  Scenario: Load a UTF-8 text source file
    Given a UTF-8 text file containing "customer jobs and pains"
    When the text ingestion loader reads the file
    Then the loaded text is "customer jobs and pains"
