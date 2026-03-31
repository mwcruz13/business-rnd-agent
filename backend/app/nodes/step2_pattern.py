"""Step 2 — Thin wrapper that wires the LLM into the hybrid pattern matcher.

Follows the same two-file convention as step1_signal.py / step1_signal_llm.py:
the wrapper instantiates the LLM at invocation time and delegates to the
full implementation in step2_pattern_llm.py.
"""
from __future__ import annotations

from backend.app.config import get_settings
from backend.app.llm.factory import get_chat_model
from backend.app.nodes.step2_pattern_llm import run_step2_llm
from backend.app.state import BMIWorkflowState


def run_step(state: BMIWorkflowState) -> BMIWorkflowState:
    return run_step2_llm(state, get_chat_model(get_settings(), state.get("llm_backend")))
