"""Step 8a entry point — Evidence Audit."""
from __future__ import annotations

from backend.app.config import get_settings
from backend.app.llm.factory import get_chat_model
from backend.app.nodes.step8a_evidence_audit_llm import run_step8a_llm
from backend.app.state import BMIWorkflowState


def run_step(state: BMIWorkflowState) -> BMIWorkflowState:
    backend = state.get("llm_backend")
    llm = get_chat_model(get_settings(), backend) if backend else None
    return run_step8a_llm(state, llm)
