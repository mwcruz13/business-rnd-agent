from __future__ import annotations

from backend.app.config import get_settings
from backend.app.llm.factory import get_chat_model
from backend.app.nodes.step3_profile_llm import run_step3_llm
from backend.app.state import BMIWorkflowState


def run_step(state: BMIWorkflowState) -> BMIWorkflowState:
    return run_step3_llm(state, get_chat_model(get_settings(), state.get("llm_backend")))
