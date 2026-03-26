"""BMI Workflow graph — orchestrator + worker topology.

The orchestrator reads ``completed_steps`` from the workflow state and
routes to the next milestone worker.  Each worker executes its step logic,
appends its name to ``completed_steps``, then returns to the orchestrator.
When all 8 milestones are done the orchestrator routes to END.

This topology replaces the former hardcoded linear chain while keeping the
same step ordering, state shape, and output contract.

Design reference: docs/agentic-orchestrator-implementation-plan.md §Phase 1.
"""
from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from backend.app.nodes.step1_signal import run_step as run_step1_signal
from backend.app.nodes.step2_pattern import run_step as run_step2_pattern
from backend.app.nodes.step3_profile import run_step as run_step3_profile
from backend.app.nodes.step4_vpm import run_step as run_step4_vpm
from backend.app.nodes.step5_define import run_step as run_step5_define
from backend.app.nodes.step6_design import run_step as run_step6_design
from backend.app.nodes.step7_risk import run_step as run_step7_risk
from backend.app.nodes.step8_pdsa import run_step as run_step8_pdsa
from backend.app.state import BMIWorkflowState


WORKFLOW_STEP_ORDER = [
    "step1_signal",
    "step2_pattern",
    "step3_profile",
    "step4_vpm",
    "step5_define",
    "step6_design",
    "step7_risk",
    "step8_pdsa",
]

WORKFLOW_STEP_RUNNERS = {
    "step1_signal": run_step1_signal,
    "step2_pattern": run_step2_pattern,
    "step3_profile": run_step3_profile,
    "step4_vpm": run_step4_vpm,
    "step5_define": run_step5_define,
    "step6_design": run_step6_design,
    "step7_risk": run_step7_risk,
    "step8_pdsa": run_step8_pdsa,
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
# Worker wrappers — run the step and record completion
# ---------------------------------------------------------------------------

def _make_worker(step_name: str, runner):
    """Create a worker node that runs a step and appends to completed_steps."""
    def worker(state: BMIWorkflowState) -> BMIWorkflowState:
        result = runner(state)
        completed = list(result.get("completed_steps") or [])
        if step_name not in completed:
            completed.append(step_name)
        return {**result, "completed_steps": completed}
    worker.__name__ = f"worker_{step_name}"
    return worker


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------

def build_graph():
    """Build the orchestrator-routed LangGraph workflow."""
    graph = StateGraph(BMIWorkflowState)

    # Add orchestrator node
    graph.add_node("orchestrator", _orchestrator)

    # Add worker nodes
    workers = {}
    for step_name, runner in WORKFLOW_STEP_RUNNERS.items():
        worker = _make_worker(step_name, runner)
        workers[step_name] = worker
        graph.add_node(step_name, worker)

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
