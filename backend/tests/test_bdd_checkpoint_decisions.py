from pytest_bdd import parsers, scenarios, then, when

from backend.app.checkpoints import validate_decision


scenarios("features/checkpoint-decisions.feature")


@when(parsers.parse('the checkpoint decision "{decision}" is validated'), target_fixture="validation_outcome")
def validate_checkpoint_decision(decision: str) -> dict[str, str | None]:
    try:
        return {"value": validate_decision(decision), "error": None}
    except ValueError as error:
        return {"value": None, "error": str(error)}


@then(parsers.parse('the validated checkpoint decision is "{expected}"'))
def assert_validated_decision(validation_outcome: dict[str, str | None], expected: str) -> None:
    assert validation_outcome["value"] == expected
    assert validation_outcome["error"] is None


@then(parsers.parse('checkpoint validation fails with message "{expected_message}"'))
def assert_validation_failure(validation_outcome: dict[str, str | None], expected_message: str) -> None:
    assert validation_outcome["value"] is None
    assert validation_outcome["error"] == expected_message
