"""Shared retry wrapper for LLM structured-output invocations."""
from __future__ import annotations

import logging
from typing import TypeVar

from pydantic import BaseModel

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

MAX_RETRIES = 2


def invoke_with_retry(structured_llm: object, messages: list, *, step_name: str) -> T:
    """Invoke ``structured_llm.invoke(messages)`` with retry on failure.

    Retries up to ``MAX_RETRIES`` times. On final failure, raises a
    ``RuntimeError`` that includes the *step_name* for diagnostics.
    """
    last_exc: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return structured_llm.invoke(messages)  # type: ignore[union-attr]
        except Exception as exc:
            last_exc = exc
            logger.warning(
                "LLM invoke failed (step=%s, attempt=%d/%d): %s",
                step_name,
                attempt,
                MAX_RETRIES,
                exc,
            )
    raise RuntimeError(
        f"LLM failure in step '{step_name}' after {MAX_RETRIES} attempts: {last_exc}"
    ) from last_exc
