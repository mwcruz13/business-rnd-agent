from fastapi.testclient import TestClient
from pytest_bdd import given, scenarios, then, when

from backend.app.main import app, settings


scenarios("features/health.feature")


@given("the BMI backend API client", target_fixture="api_client")
def api_client() -> TestClient:
    return TestClient(app)


@when("the client requests the health endpoint", target_fixture="response")
def request_health_endpoint(api_client: TestClient):
    return api_client.get("/health")


@then("the response status code is 200")
def assert_status_code(response) -> None:
    assert response.status_code == 200


@then('the response body status is "ok"')
def assert_response_status(response) -> None:
    assert response.json()["status"] == "ok"


@then("the response body includes the configured llm backend")
def assert_response_backend(response) -> None:
    assert response.json()["llm_backend"] == settings.llm_backend
