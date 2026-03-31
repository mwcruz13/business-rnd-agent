from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest

from backend.app.nodes import step1_signal
from backend.app.nodes.step1_signal_llm import SignalScanResult
from backend.app.workers import steps as worker_steps
from backend.app.llm.factory import get_chat_model
from backend.app.workflow import get_run_state
from backend.app.workflow import run_workflow_from_voc_data


class FakeStructuredInvoker:
    def __init__(self, result: SignalScanResult) -> None:
        self.result = result

    def invoke(self, messages: list[object]) -> SignalScanResult:
        return self.result


class FakeStructuredChatModel:
    def __init__(self, result: SignalScanResult) -> None:
        self.result = result

    def with_structured_output(self, schema: type[SignalScanResult]) -> FakeStructuredInvoker:
        return FakeStructuredInvoker(self.result)


def _sample_result() -> SignalScanResult:
    return SignalScanResult.model_validate(
        {
            "signals": [
                {
                    "signal_id": "self_serve_friction",
                    "signal": "Customers are asking for a lower-friction self-serve firmware assessment",
                    "zone": "New-Market Foothold",
                    "source_type": "Internal VoC",
                    "observable_behavior": "Customers describe delay and friction in the current firmware assessment process.",
                    "evidence": [
                        "Customers report onboarding friction and too many manual steps.",
                        "Customers need faster time-to-value.",
                    ],
                }
            ],
            "interpreted_signals": [
                {
                    "signal_id": "self_serve_friction",
                    "signal": "Customers are asking for a lower-friction self-serve firmware assessment",
                    "zone": "New-Market Foothold",
                    "classification": "Disruptive — New-Market",
                    "confidence": "Medium",
                    "rationale": "The input suggests a simpler access path could unlock customers not well served by the current workflow.",
                    "alternative_explanation": "This may still be an operational improvement request rather than a true disruptive foothold.",
                    "key_evidence_gap": "Need evidence of willingness to adopt self-serve over the current consultant-led path.",
                    "filters": ["Barrier Removal", "Asymmetric Motivation"],
                }
            ],
            "priority_matrix": [
                {
                    "signal_id": "self_serve_friction",
                    "signal": "Customers are asking for a lower-friction self-serve firmware assessment",
                    "impact": 3,
                    "speed": 2,
                    "score": 6,
                    "tier": "Investigate",
                    "rationale": "The request appears adjacent to core value delivery and is repeated across the input.",
                }
            ],
            "coverage_gaps": [
                {
                    "zone": "Regulatory Shift",
                    "note": "No direct evidence found in this input.",
                }
            ],
            "agent_recommendation": "Investigate whether a self-serve offer addresses nonconsumption caused by current delivery friction.",
        }
    )


def test_workflow_service_can_pause_after_step1_in_llm_mode(monkeypatch) -> None:
    session_id = f"workflow-step1-llm-mode-{uuid4()}"
    fake_model = FakeStructuredChatModel(_sample_result())

    # Patch both the old node module (for any direct callers) and
    # the new worker module (which the orchestrator now uses)
    for target_module in (step1_signal, worker_steps):
        monkeypatch.setattr(
            target_module,
            "get_settings",
            lambda: SimpleNamespace(llm_backend="azure"),
        )
        monkeypatch.setattr(target_module, "get_chat_model", lambda settings, llm_backend=None: fake_model)

    first_pause = run_workflow_from_voc_data(
        "Customers report onboarding friction, too many manual steps, and delays before they reach value.",
        session_id=session_id,
        llm_backend="azure",
        pause_at_checkpoints=True,
    )

    assert first_pause["run_status"] == "paused"
    assert first_pause["pending_checkpoint"] == "checkpoint_1"
    assert first_pause["current_step"] == "signal_scan"
    assert first_pause["signals"][0]["zone"] == "New-Market Foothold"
    assert first_pause["interpreted_signals"][0]["classification"] == "Disruptive — New-Market"
    assert first_pause["priority_matrix"][0]["score"] == 6
    assert "self-serve" in first_pause["agent_recommendation"]

    persisted = get_run_state(session_id)
    assert persisted["run_status"] == "paused"
    assert persisted["pending_checkpoint"] == "checkpoint_1"
    assert persisted["signals"][0]["signal"] == first_pause["signals"][0]["signal"]


def test_get_chat_model_uses_runtime_ollama_override() -> None:
    settings = SimpleNamespace(
        llm_backend="azure",
        ollama_base_url="http://ollama.local:11434",
        ollama_model="nemotron-test",
        azure_openai_endpoint="https://example.openai.azure.com",
        azure_openai_api_key="secret",
        azure_openai_api_version="2025-01-01-preview",
        azure_openai_deployment_chat="chat-deployment",
    )

    model = get_chat_model(settings, "ollama")

    assert model.__class__.__name__ == "ChatOllama"
    assert getattr(model, "model") == "nemotron-test"
    assert str(getattr(model, "base_url")) == "http://ollama.local:11434"


def test_get_chat_model_rejects_unsupported_backend() -> None:
    settings = SimpleNamespace(
        llm_backend="azure",
        ollama_base_url="http://ollama.local:11434",
        ollama_model="nemotron-test",
        azure_openai_endpoint="https://example.openai.azure.com",
        azure_openai_api_key="secret",
        azure_openai_api_version="2025-01-01-preview",
        azure_openai_deployment_chat="chat-deployment",
    )

    with pytest.raises(ValueError, match="Unsupported llm_backend: openai"):
        get_chat_model(settings, "openai")