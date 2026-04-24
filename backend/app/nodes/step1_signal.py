from __future__ import annotations

from backend.app.nodes.step1a_signal_scan import run_step as run_1a
from backend.app.nodes.step1b_signal_recommend import run_step as run_1b
from backend.app.state import BMIWorkflowState


def run_step(state: BMIWorkflowState) -> BMIWorkflowState:
    """Backward-compatible entry point — runs 1a then 1b."""
    state_after_1a = run_1a(state)
    return run_1b(state_after_1a)
