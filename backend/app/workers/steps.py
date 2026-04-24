"""Concrete worker implementations for the 8 BMI milestone steps.

Steps 1–7 use LLM-backed execution via their ``_llm.py`` peers.
Step 8 is deterministic (no LLM).

Each worker is a thin adapter: it instantiates the LLM (if needed)
and delegates to the existing step implementation module.
The ``_llm.py`` files remain the single source of business logic.
"""
from __future__ import annotations

from backend.app.config import get_settings
from backend.app.llm.factory import get_chat_model
from backend.app.nodes.step1_signal_llm import run_step1_llm
from backend.app.nodes.step2_pattern_llm import run_step2_llm
from backend.app.nodes.step3_profile_llm import run_step3_llm
from backend.app.nodes.step4_vpm_llm import run_step4_llm
from backend.app.nodes.step5a_ideation_llm import run_step5a_llm
from backend.app.nodes.step5b_scoring_llm import run_step5b_llm
from backend.app.nodes.step6_design_llm import run_step6_llm
from backend.app.nodes.step7_risk_llm import run_step7_llm
from backend.app.nodes.step8a_evidence_audit import run_step as run_step8a_default
from backend.app.nodes.step8b_card_selection import run_step as run_step8b_default
from backend.app.nodes.step8c_path_sequencing import run_step as run_step8c_default
from backend.app.nodes.step8_pdsa import run_step as run_step8_deterministic
from backend.app.nodes.step9_artifact_designer import run_step as run_step9_default
from backend.app.state import BMIWorkflowState
from backend.app.workers.base import BaseWorker


class SignalScannerWorker(BaseWorker):
    """Step 1 — SOC Radar signal scan from VoC input."""

    @property
    def name(self) -> str:
        return "step1_signal"

    @property
    def step_number(self) -> int:
        return 1

    @property
    def description(self) -> str:
        return "SOC Radar signal scan from VoC input"

    def execute(self, state: BMIWorkflowState) -> BMIWorkflowState:
        return run_step1_llm(state, get_chat_model(get_settings(), state.get("llm_backend")))


class PatternMatcherWorker(BaseWorker):
    """Step 2 — Hybrid pattern matching (affinity shortlist + LLM reasoning)."""

    @property
    def name(self) -> str:
        return "step2_pattern"

    @property
    def step_number(self) -> int:
        return 2

    @property
    def description(self) -> str:
        return "Hybrid pattern matching (affinity shortlist + LLM reasoning)"

    def execute(self, state: BMIWorkflowState) -> BMIWorkflowState:
        return run_step2_llm(state, get_chat_model(get_settings(), state.get("llm_backend")))


class CustomerProfileWorker(BaseWorker):
    """Step 3 — CXIF empathy profile and empathy gate."""

    @property
    def name(self) -> str:
        return "step3_profile"

    @property
    def step_number(self) -> int:
        return 3

    @property
    def description(self) -> str:
        return "CXIF empathy profile and empathy gate"

    def execute(self, state: BMIWorkflowState) -> BMIWorkflowState:
        return run_step3_llm(state, get_chat_model(get_settings(), state.get("llm_backend")))


class ValueDriverWorker(BaseWorker):
    """Step 4 — CXIF Measure and Define (value driver tree + insights)."""

    @property
    def name(self) -> str:
        return "step4_vpm"

    @property
    def step_number(self) -> int:
        return 4

    @property
    def description(self) -> str:
        return "CXIF Measure and Define (value driver tree + actionable insights)"

    def execute(self, state: BMIWorkflowState) -> BMIWorkflowState:
        return run_step4_llm(state, get_chat_model(get_settings(), state.get("llm_backend")))


class VPIdeationWorker(BaseWorker):
    """Step 5a — VP Portfolio Ideation."""

    @property
    def name(self) -> str:
        return "step5a_ideation"

    @property
    def step_number(self) -> int:
        return 5

    @property
    def description(self) -> str:
        return "VP Portfolio Ideation (pattern-coherent alternatives)"

    def execute(self, state: BMIWorkflowState) -> BMIWorkflowState:
        return run_step5a_llm(state, get_chat_model(get_settings(), state.get("llm_backend")))


class VPScoringWorker(BaseWorker):
    """Step 5b — VP Portfolio Scoring."""

    @property
    def name(self) -> str:
        return "step5b_scoring"

    @property
    def step_number(self) -> int:
        return 5

    @property
    def description(self) -> str:
        return "VP Portfolio Scoring and Ranking"

    def execute(self, state: BMIWorkflowState) -> BMIWorkflowState:
        return run_step5b_llm(state, get_chat_model(get_settings(), state.get("llm_backend")))


class BusinessModelWorker(BaseWorker):
    """Step 6 — Business Model Canvas + Fit Assessment."""

    @property
    def name(self) -> str:
        return "step6_design"

    @property
    def step_number(self) -> int:
        return 6

    @property
    def description(self) -> str:
        return "Business Model Canvas and Fit Assessment"

    def execute(self, state: BMIWorkflowState) -> BMIWorkflowState:
        return run_step6_llm(state, get_chat_model(get_settings(), state.get("llm_backend")))


class RiskMapWorker(BaseWorker):
    """Step 7 — Precoil EMT assumption mapping."""

    @property
    def name(self) -> str:
        return "step7_risk"

    @property
    def step_number(self) -> int:
        return 7

    @property
    def description(self) -> str:
        return "Precoil EMT assumption mapping"

    def execute(self, state: BMIWorkflowState) -> BMIWorkflowState:
        return run_step7_llm(state, get_chat_model(get_settings(), state.get("llm_backend")))


class ExperimentPlanWorker(BaseWorker):
    """Step 8 — Deterministic experiment card selection and plan generation."""

    @property
    def name(self) -> str:
        return "step8_pdsa"

    @property
    def step_number(self) -> int:
        return 8

    @property
    def description(self) -> str:
        return "Experiment card selection and plan generation"

    def execute(self, state: BMIWorkflowState) -> BMIWorkflowState:
        return run_step8_deterministic(state)


class EvidenceAuditWorker(BaseWorker):
    """Step 8a — Evidence audit of Test-first assumptions against VoC/signals."""

    @property
    def name(self) -> str:
        return "step8a_evidence_audit"

    @property
    def step_number(self) -> int:
        return 8

    @property
    def description(self) -> str:
        return "Evidence audit of Test-first assumptions against VoC and signal context"

    def execute(self, state: BMIWorkflowState) -> BMIWorkflowState:
        return run_step8a_default(state)


class CardSelectionWorker(BaseWorker):
    """Step 8b — Evidence-aware experiment card selection."""

    @property
    def name(self) -> str:
        return "step8b_card_selection"

    @property
    def step_number(self) -> int:
        return 8

    @property
    def description(self) -> str:
        return "Evidence-aware card selection from the canonical experiment library"

    def execute(self, state: BMIWorkflowState) -> BMIWorkflowState:
        return run_step8b_default(state)


class PathSequencingWorker(BaseWorker):
    """Step 8c — Sequence an evidence-progressive path from selected cards."""

    @property
    def name(self) -> str:
        return "step8c_path_sequencing"

    @property
    def step_number(self) -> int:
        return 8

    @property
    def description(self) -> str:
        return "Evidence-progressive sequencing of selected experiment cards"

    def execute(self, state: BMIWorkflowState) -> BMIWorkflowState:
        return run_step8c_default(state)


class ArtifactDesignerWorker(BaseWorker):
    """Step 9 — Produce concrete artifact definitions for each experiment card."""

    @property
    def name(self) -> str:
        return "step9_artifact_designer"

    @property
    def step_number(self) -> int:
        return 9

    @property
    def description(self) -> str:
        return "Generate build-ready artifact definitions for selected experiments"

    def execute(self, state: BMIWorkflowState) -> BMIWorkflowState:
        return run_step9_default(state)
