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


def build_graph():
    graph = StateGraph(BMIWorkflowState)
    graph.add_node("step1_signal", run_step1_signal)
    graph.add_node("step2_pattern", run_step2_pattern)
    graph.add_node("step3_profile", run_step3_profile)
    graph.add_node("step4_vpm", run_step4_vpm)
    graph.add_node("step5_define", run_step5_define)
    graph.add_node("step6_design", run_step6_design)
    graph.add_node("step7_risk", run_step7_risk)
    graph.add_node("step8_pdsa", run_step8_pdsa)

    graph.add_edge(START, WORKFLOW_STEP_ORDER[0])
    for source_step, target_step in zip(WORKFLOW_STEP_ORDER, WORKFLOW_STEP_ORDER[1:]):
        graph.add_edge(source_step, target_step)
    graph.add_edge(WORKFLOW_STEP_ORDER[-1], END)

    return graph.compile()
