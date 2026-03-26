from __future__ import annotations

from backend.app.config import get_settings
from backend.app.llm.factory import get_chat_model
from backend.app.nodes.step6_design_llm import run_step6_llm
from backend.app.state import BMIWorkflowState


def run_step(state: BMIWorkflowState) -> BMIWorkflowState:
    return run_step6_llm(state, get_chat_model(get_settings()))
