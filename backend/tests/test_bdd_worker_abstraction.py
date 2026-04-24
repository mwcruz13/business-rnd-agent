"""BDD step definitions for the worker abstraction feature.

Registry scenarios are purely structural — no LLM calls needed.
The execute/run scenarios invoke the real Step 1 worker (LLM-backed).
"""
from pytest_bdd import given, parsers, scenarios, then, when

from backend.app.graph import WORKFLOW_STEP_ORDER
from backend.app.state import BMIWorkflowState
from backend.app.workers.registry import WorkerRegistry


scenarios("features/worker-abstraction.feature")


# ── Shared fixtures ──────────────────────────────────────────────────

FIRMWARE_ASSESSMENT_VOC = (
    "Enterprise customers report that firmware update cycles are too slow to "
    "keep pace with security patches.  Internal engineering teams spend 60% of "
    "their time on regression testing that could be automated.  Competitors have "
    "begun offering self-serve firmware assessment portals that bypass traditional "
    "support channels."
)


def _minimal_step1_state() -> BMIWorkflowState:
    return BMIWorkflowState(
        session_id="worker-test",
        current_step="ingest",
        input_type="text",
        llm_backend="azure",
        voc_data=FIRMWARE_ASSESSMENT_VOC,
        completed_steps=[],
    )


# ── Registry scenarios ───────────────────────────────────────────────

@given("the worker registry", target_fixture="registry")
def worker_registry() -> WorkerRegistry:
    return WorkerRegistry()


@then("every worker has a non-empty name matching a known step")
def assert_worker_names(registry: WorkerRegistry) -> None:
    for worker in registry.get_all_workers():
        assert worker.name, f"Worker has empty name"
        assert worker.name in WORKFLOW_STEP_ORDER, (
            f"Worker name '{worker.name}' not in WORKFLOW_STEP_ORDER"
        )


@then("every worker has a positive step number")
def assert_worker_step_numbers(registry: WorkerRegistry) -> None:
    for worker in registry.get_all_workers():
        assert worker.step_number >= 1, (
            f"Worker '{worker.name}' step_number={worker.step_number} must be positive"
        )


@then("no two workers share the same name")
def assert_no_duplicate_names(registry: WorkerRegistry) -> None:
    workers = registry.get_all_workers()
    names = [w.name for w in workers]
    assert len(set(names)) == len(names), f"Duplicate names: {names}"


@when("I list all workers in order", target_fixture="worker_names")
def list_workers(registry: WorkerRegistry) -> list[str]:
    return [w.name for w in registry.get_all_workers()]


@then("the worker names match the workflow step order exactly")
def assert_order(worker_names: list[str]) -> None:
    assert worker_names == list(WORKFLOW_STEP_ORDER)


@when(
    parsers.parse('I look up the worker for "{step_name}"'),
    target_fixture="looked_up_worker",
)
def lookup_worker(registry: WorkerRegistry, step_name: str):
    return registry.get_worker(step_name)


@then(parsers.parse('the returned worker name is "{expected}"'))
def assert_looked_up_name(looked_up_worker, expected: str) -> None:
    assert looked_up_worker.name == expected


@then(parsers.parse("the returned worker step number is {expected:d}"))
def assert_looked_up_number(looked_up_worker, expected: int) -> None:
    assert looked_up_worker.step_number == expected


# ── Execute / run scenarios (LLM-backed) ─────────────────────────────

@given("a minimal workflow state for step 1", target_fixture="step1_state")
def minimal_step1_state() -> BMIWorkflowState:
    return _minimal_step1_state()


@when("the step1_signal worker executes", target_fixture="execute_result")
def worker_execute(step1_state: BMIWorkflowState) -> BMIWorkflowState:
    registry = WorkerRegistry()
    worker = registry.get_worker("step1_signal")
    return worker.execute(step1_state)


@then(parsers.parse('the returned state contains "{key}"'))
def assert_state_key(execute_result: BMIWorkflowState, key: str) -> None:
    assert key in execute_result, f"Key '{key}' missing from result state"
    assert execute_result[key], f"Key '{key}' is empty in result state"


@when("the step1_signal worker runs", target_fixture="run_result")
def worker_run(step1_state: BMIWorkflowState) -> BMIWorkflowState:
    registry = WorkerRegistry()
    worker = registry.get_worker("step1_signal")
    return worker.run(step1_state)


@then(parsers.parse('"{step_name}" is in the completed_steps list'))
def assert_completed(run_result: BMIWorkflowState, step_name: str) -> None:
    completed = run_result.get("completed_steps", [])
    assert step_name in completed, (
        f"'{step_name}' not in completed_steps: {completed}"
    )
