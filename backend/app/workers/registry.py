"""Worker registry — the single lookup point for milestone workers.

The orchestrator and workflow service use the registry to resolve
step names to worker instances instead of maintaining their own
runner dictionaries.
"""
from __future__ import annotations

from typing import Callable

from backend.app.state import BMIWorkflowState
from backend.app.workers.base import BaseWorker
from backend.app.workers.steps import (
    ArtifactDesignerWorker,
    BusinessModelWorker,
    CardSelectionWorker,
    CustomerProfileWorker,
    EvidenceAuditWorker,
    ExperimentPlanWorker,
    PathSequencingWorker,
    PatternMatcherWorker,
    RiskMapWorker,
    SignalRecommendWorker,
    SignalScanWorker,
    ValueDriverWorker,
    VPIdeationWorker,
    VPScoringWorker,
)


class WorkerRegistry:
    """Ordered collection of milestone workers indexed by step name.

    Maintains a single canonical list that serves both the graph
    topology and the workflow service execution loop.
    """

    def __init__(self) -> None:
        # Workers in workflow execution order
        workers: list[BaseWorker] = [
            SignalScanWorker(),
            SignalRecommendWorker(),
            PatternMatcherWorker(),
            CustomerProfileWorker(),
            ValueDriverWorker(),
            VPIdeationWorker(),
            VPScoringWorker(),
            BusinessModelWorker(),
            RiskMapWorker(),
            EvidenceAuditWorker(),
            CardSelectionWorker(),
            PathSequencingWorker(),
            ExperimentPlanWorker(),
            ArtifactDesignerWorker(),
        ]
        self._workers_by_name: dict[str, BaseWorker] = {w.name: w for w in workers}
        self._ordered: list[BaseWorker] = workers

    def get_worker(self, step_name: str) -> BaseWorker:
        """Resolve a step name to its worker instance.

        Raises ``KeyError`` if the step name is not registered.
        """
        return self._workers_by_name[step_name]

    def get_all_workers(self) -> list[BaseWorker]:
        """Return all workers in workflow execution order."""
        return list(self._ordered)

    def get_runner(self, step_name: str) -> Callable[[BMIWorkflowState], BMIWorkflowState]:
        """Return the worker's ``execute`` method for backward compatibility.

        This allows callers that expect a plain ``runner(state) -> state``
        function to work without change while the worker abstraction
        is being integrated.
        """
        return self.get_worker(step_name).execute

    def step_names(self) -> list[str]:
        """Return step names in workflow order."""
        return [w.name for w in self._ordered]


# Module-level singleton — avoids repeated instantiation
_registry: WorkerRegistry | None = None


def get_worker_registry() -> WorkerRegistry:
    """Return the shared worker registry singleton."""
    global _registry
    if _registry is None:
        _registry = WorkerRegistry()
    return _registry
