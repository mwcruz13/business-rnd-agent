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
from backend.app.nodes.step5_define_llm import run_step5_llm
from backend.app.nodes.step6_design_llm import run_step6_llm
from backend.app.nodes.step7_risk_llm import run_step7_llm
from backend.app.nodes.step8_pdsa import run_step as run_step8_deterministic
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
        return run_step1_llm(state, get_chat_model(get_settings()))


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
        return run_step2_llm(state, get_chat_model(get_settings()))


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
        return run_step3_llm(state, get_chat_model(get_settings()))


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
        return run_step4_llm(state, get_chat_model(get_settings()))


class ValuePropositionWorker(BaseWorker):
    """Step 5 — Value Proposition Canvas."""

    @property
    def name(self) -> str:
        return "step5_define"

    @property
    def step_number(self) -> int:
        return 5

    @property
    def description(self) -> str:
        return "Value Proposition Canvas"

    def execute(self, state: BMIWorkflowState) -> BMIWorkflowState:
        return run_step5_llm(state, get_chat_model(get_settings()))


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
        return run_step6_llm(state, get_chat_model(get_settings()))


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
        return run_step7_llm(state, get_chat_model(get_settings()))


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
