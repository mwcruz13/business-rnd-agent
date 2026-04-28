"""Worker for VoC preprocessing — Step 0 (runs before signal scan)."""
from __future__ import annotations

from backend.app.config import get_settings
from backend.app.llm.factory import get_chat_model
from backend.app.nodes.preprocess_voc import run_preprocessing
from backend.app.state import BMIWorkflowState
from backend.app.workers.base import BaseWorker


class PreprocessWorker(BaseWorker):
    """Step 0 — VoC input preprocessing (segmentation, cleaning, metadata)."""

    @property
    def name(self) -> str:
        return "step0_preprocess"

    @property
    def step_number(self) -> int:
        return 1

    @property
    def description(self) -> str:
        return "Segment, clean, and enrich VoC input with metadata tags"

    def execute(self, state: BMIWorkflowState) -> BMIWorkflowState:
        llm = get_chat_model(get_settings(), state.get("llm_backend"))
        return run_preprocessing(state, llm)
