from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest

from backend.app.nodes import step1a_signal_scan, step1b_signal_recommend
from backend.app.nodes.step1a_signal_scan_llm import ScanInterpretResult, DetectedSignal, InterpretedSignal
from backend.app.nodes.step1b_signal_recommend_llm import (
    PrioritizeRecommendResult,
    PriorityEntry,
    ReinforcementMap,
    SignalRecommendation,
    RPVAssessment,
    NextStep,
    ExperimentCandidate,
)
from backend.app.workers import steps as worker_steps
from backend.app.llm.factory import get_chat_model
from backend.app.workflow import get_run_state
from backend.app.workflow import run_workflow_from_voc_data


class FakeStructuredInvoker:
    def __init__(self, result: object) -> None:
        self.result = result

    def invoke(self, messages: list[object]) -> object:
        return self.result


class FakeStructuredChatModel:
    """Dispatch different results based on which schema is requested."""
    def __init__(self, results: dict[type, object]) -> None:
        self.results = results

    def with_structured_output(self, schema: type) -> FakeStructuredInvoker:
        return FakeStructuredInvoker(self.results[schema])


def _sample_scan_result() -> ScanInterpretResult:
    return ScanInterpretResult(
        signals=[
            DetectedSignal(
                signal_id="self_serve_friction",
                signal="Customers are asking for a lower-friction self-serve firmware assessment",
                zone="New-Market Foothold",
                source_type="Internal VoC",
                observable_behavior="Customers describe delay and friction in the current firmware assessment process.",
                evidence=[
                    "Customers report onboarding friction and too many manual steps.",
                    "Customers need faster time-to-value.",
                ],
                supporting_comments=[1, 2],
            )
        ],
        interpreted_signals=[
            InterpretedSignal(
                signal_id="self_serve_friction",
                signal="Customers are asking for a lower-friction self-serve firmware assessment",
                zone="New-Market Foothold",
                classification="Disruptive — New-Market",
                confidence="Medium",
                litmus_test="Pass — nonconsumers exist who cannot access the current workflow",
                filters=[],
                filters_passed=0,
                disruptive_potential="Medium",
                value_network_insight="The incumbent's value network is optimized for consultant-led delivery.",
                alternative_explanation="This may still be an operational improvement request rather than a true disruptive foothold.",
                key_evidence_gap="Need evidence of willingness to adopt self-serve over the current consultant-led path.",
            ),
        ],
    )


def _sample_recommend_result() -> PrioritizeRecommendResult:
    return PrioritizeRecommendResult(
        priority_matrix=[
            PriorityEntry(
                signal_id="self_serve_friction",
                signal="Customers are asking for a lower-friction self-serve firmware assessment",
                classification="Disruptive — New-Market",
                impact=3,
                speed=2,
                score=6,
                tier="Investigate",
                rationale="The request appears adjacent to core value delivery and is repeated across the input.",
            )
        ],
        reinforcement_map=ReinforcementMap(
            chain=["self_serve_friction"],
            strategic_insight="Reducing friction is the primary intervention point.",
        ),
        recommendations=[
            SignalRecommendation(
                signal_id="self_serve_friction",
                action_tier="Investigate",
                what_we_know="Onboarding is slow.",
                what_we_dont_know=["How many customers are affected"],
                rpv_assessment=RPVAssessment(
                    resources="Incumbent has engineering resources.",
                    processes="Current processes favor consultant-led delivery.",
                    values="Margin expectations make self-serve unattractive.",
                    assessment="Would choose not to respond",
                ),
                next_steps=[
                    NextStep(action="Interview 5 customers", owner="CX Lead", timeframe="30 days"),
                    NextStep(action="Map self-serve journey", owner="Product Manager", timeframe="45 days"),
                ],
                experiment_candidate=ExperimentCandidate(
                    assumption="We believe that early adopters will switch within 30 days",
                    experiment_type="Customer Interview",
                    success="5+ customers express willingness",
                    failure="Fewer than 2 customers interested",
                ),
            ),
        ],
        agent_recommendation="Investigate whether a self-serve offer addresses nonconsumption caused by current delivery friction.",
    )


def test_workflow_service_can_pause_after_step1_in_llm_mode(monkeypatch) -> None:
    session_id = f"workflow-step1-llm-mode-{uuid4()}"
    fake_model = FakeStructuredChatModel({
        ScanInterpretResult: _sample_scan_result(),
        PrioritizeRecommendResult: _sample_recommend_result(),
    })

    # Patch the node modules that actually call the LLM
    for target_module in (step1a_signal_scan, step1b_signal_recommend, worker_steps):
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
    assert first_pause["pending_checkpoint"] == "checkpoint_1a"
    assert first_pause["current_step"] == "signal_scan"
    assert first_pause["signals"][0]["zone"] == "New-Market Foothold"
    assert first_pause["interpreted_signals"][0]["classification"] == "Disruptive — New-Market"

    persisted = get_run_state(session_id)
    assert persisted["run_status"] == "paused"
    assert persisted["pending_checkpoint"] == "checkpoint_1a"
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