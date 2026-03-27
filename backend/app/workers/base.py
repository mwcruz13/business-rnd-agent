"""Base worker abstraction for BMI milestone steps.

Every milestone worker must implement this interface so the orchestrator
and workflow service can interact with workers uniformly.
"""
from __future__ import annotations

import abc
from typing import Any

from backend.app.state import BMIWorkflowState


class BaseWorker(abc.ABC):
    """Abstract base for a BMI milestone worker.

    Subclasses implement ``execute`` with the step-specific logic.
    The ``run`` method wraps ``execute`` and tracks completion in state.
    """

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Step name matching the WORKFLOW_STEP_ORDER entry (e.g. 'step1_signal')."""

    @property
    @abc.abstractmethod
    def step_number(self) -> int:
        """1-based step index (1–8)."""

    @property
    @abc.abstractmethod
    def description(self) -> str:
        """Short human-readable description of what this worker does."""

    @abc.abstractmethod
    def execute(self, state: BMIWorkflowState) -> BMIWorkflowState:
        """Run the step logic and return updated state.

        This is the pure business logic — it must NOT modify
        ``completed_steps``.  Completion tracking is handled by ``run``.
        """

    def run(self, state: BMIWorkflowState) -> BMIWorkflowState:
        """Execute the step and record completion in ``completed_steps``.

        This is the entry point used by the orchestrator graph and
        the workflow service.  It delegates to ``execute``, then appends
        this worker's name to the completed list.
        """
        result = self.execute(state)
        completed = list(result.get("completed_steps") or [])
        if self.name not in completed:
            completed.append(self.name)
        return {**result, "completed_steps": completed}
