"""Step 8b entry point — Card Selection."""
from __future__ import annotations

from backend.app.config import get_settings
from backend.app.llm.factory import get_chat_model
from backend.app.nodes.step8b_card_selection_llm import run_step8b_llm
from backend.app.state import BMIWorkflowState


def run_step(state: BMIWorkflowState) -> BMIWorkflowState:
    backend = state.get("llm_backend")
    llm = get_chat_model(get_settings(), backend) if backend else None
    return run_step8b_llm(state, llm)
