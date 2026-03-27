"""BMI Workflow graph — orchestrator + worker topology.

The orchestrator reads ``completed_steps`` from the workflow state and
routes to the next milestone worker.  Each worker executes its step logic,
appends its name to ``completed_steps``, then returns to the orchestrator.
When all 8 milestones are done the orchestrator routes to END.

This topology replaces the former hardcoded linear chain while keeping the
same step ordering, state shape, and output contract.

Design reference: docs/agentic-orchestrator-implementation-plan.md §Phase 1–2.
"""
from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from backend.app.state import BMIWorkflowState
from backend.app.workers.registry import get_worker_registry


def _get_registry():
    """Lazy access to the worker registry (avoids import-time side effects)."""
    return get_worker_registry()


# Public constants derived from the worker registry.
# These remain module-level so existing callers (workflow.py, tests) can
# import them without change.
WORKFLOW_STEP_ORDER = _get_registry().step_names()

WORKFLOW_STEP_RUNNERS = {
    name: _get_registry().get_runner(name) for name in WORKFLOW_STEP_ORDER
}

_STEP_INDEX = {name: i for i, name in enumerate(WORKFLOW_STEP_ORDER)}


# ---------------------------------------------------------------------------
# Orchestrator node
# ---------------------------------------------------------------------------

def determine_next_step(state: BMIWorkflowState) -> str:
    """Return the name of the next milestone to execute, or ``"__end__"``.

    This is the public API for the orchestrator's routing logic, usable
    both inside the LangGraph graph and by the workflow service for
    step-by-step checkpointed execution.
    """
    completed = set(state.get("completed_steps") or [])
    for step_name in WORKFLOW_STEP_ORDER:
        if step_name not in completed:
            return step_name
    return "__end__"


def steps_completed_before(step_index: int) -> list[str]:
    """Return the list of step names completed before a given index.

    Useful for converting a start_index into a ``completed_steps`` list
    when entering or resuming orchestrated execution.
    """
    return list(WORKFLOW_STEP_ORDER[:step_index])


def _orchestrator(state: BMIWorkflowState) -> BMIWorkflowState:
    """Graph-internal orchestrator node — sets ``next_step`` in state."""
    return {**state, "next_step": determine_next_step(state)}


def get_next_step(state: BMIWorkflowState) -> str:
    """Routing function: read ``next_step`` set by the orchestrator."""
    return state.get("next_step") or WORKFLOW_STEP_ORDER[0]


# ---------------------------------------------------------------------------
# Worker wrappers — delegate to the worker's run() method
# ---------------------------------------------------------------------------

def _make_graph_node(step_name: str):
    """Create a graph node function that delegates to the worker's run method.

    The worker's ``run()`` handles both execution and completion tracking,
    replacing the former closure-based approach.
    """
    def node(state: BMIWorkflowState) -> BMIWorkflowState:
        worker = _get_registry().get_worker(step_name)
        return worker.run(state)
    node.__name__ = f"worker_{step_name}"
    return node


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------

def build_graph():
    """Build the orchestrator-routed LangGraph workflow."""
    graph = StateGraph(BMIWorkflowState)

    # Add orchestrator node
    graph.add_node("orchestrator", _orchestrator)

    # Add worker nodes via the worker abstraction
    for step_name in WORKFLOW_STEP_ORDER:
        node = _make_graph_node(step_name)
        graph.add_node(step_name, node)

    # START → orchestrator
    graph.add_edge(START, "orchestrator")

    # Orchestrator → conditional routing to workers or END
    routing_map = {step_name: step_name for step_name in WORKFLOW_STEP_ORDER}
    routing_map["__end__"] = END
    graph.add_conditional_edges("orchestrator", get_next_step, routing_map)

    # Each worker → back to orchestrator
    for step_name in WORKFLOW_STEP_ORDER:
        graph.add_edge(step_name, "orchestrator")

    return graph.compile()
