"""Worker abstraction layer for BMI milestone steps.

Provides a uniform interface for the orchestrator and workflow service
to interact with step execution — regardless of whether the worker
uses LLM or deterministic logic internally.

Design reference: docs/agentic-orchestrator-implementation-plan.md §Phase 2.
"""

from backend.app.workers.base import BaseWorker
from backend.app.workers.registry import WorkerRegistry, get_worker_registry

__all__ = ["BaseWorker", "WorkerRegistry", "get_worker_registry"]
