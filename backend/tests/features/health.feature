Feature: Backend health endpoint
  The backend must expose a health endpoint so the UI, CLI, and container checks can confirm the service is ready.

  Scenario: Health endpoint reports service readiness
    Given the BMI backend API client
    When the client requests the health endpoint
    Then the response status code is 200
    And the response body status is "ok"
    And the response body includes the configured llm backend
