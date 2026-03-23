from __future__ import annotations

import os
from typing import Any

import requests


BACKEND_API_BASE_URL = os.environ.get("BACKEND_API_BASE_URL", "http://localhost:8000")


class FrontendApiError(RuntimeError):
    pass


def get_health() -> dict[str, Any]:
    return _request_json("GET", "/health")


def start_run(
    *,
    input_text: str | None,
    input_path: str | None = None,
    input_format: str | None = None,
    llm_backend: str = "azure",
    pause_at_checkpoints: bool = True,
) -> dict[str, Any]:
    payload = {
        "input_text": input_text,
        "input_path": input_path,
        "input_format": input_format,
        "llm_backend": llm_backend,
        "pause_at_checkpoints": pause_at_checkpoints,
    }
    return _request_json("POST", "/runs", json=payload)


def get_run_state(session_id: str) -> dict[str, Any]:
    return _request_json("GET", f"/runs/{session_id}")


def resume_run(session_id: str, *, decision: str, edit_state: dict[str, Any] | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {"decision": decision}
    if edit_state is not None:
        payload["edit_state"] = edit_state
    return _request_json("POST", f"/runs/{session_id}/resume", json=payload)


def _request_json(method: str, path: str, *, json: dict[str, Any] | None = None) -> dict[str, Any]:
    response = requests.request(method, f"{BACKEND_API_BASE_URL}{path}", json=json, timeout=30)
    if response.ok:
        return response.json()

    detail = _extract_error_detail(response)
    raise FrontendApiError(detail)


def _extract_error_detail(response: requests.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return f"Backend request failed with status {response.status_code}"

    detail = payload.get("detail")
    if isinstance(detail, str):
        return detail
    return f"Backend request failed with status {response.status_code}"