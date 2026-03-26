"""Step 1 LLM-backed signal scan using the SOC Radar SKILL.

Loads the soc-radar SKILL.md as the system prompt, sends the VOC input
to the configured chat model, and returns structured signal outputs
compatible with the BMIWorkflowState contract.
"""
from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from backend.app.skills.loader import PromptAssetLoader
from backend.app.state import BMIWorkflowState


# ---------------------------------------------------------------------------
# Structured output schemas — these define the contract the LLM must fill.
# ---------------------------------------------------------------------------

class DetectedSignal(BaseModel):
    signal_id: str = Field(description="Short snake_case identifier for the signal")
    signal: str = Field(description="Concise signal description grounded in the source input")
    zone: str = Field(
        description="Primary SOC Radar signal zone. Must be one of: Nonconsumption, "
        "Overserved Customers, Low-End Foothold, New-Market Foothold, "
        "Business Model Anomaly, Enabling Technology, Regulatory / Policy Shift"
    )
    source_type: str = Field(default="Internal VoC")
    observable_behavior: str = Field(description="What is actually happening — not what might happen")
    evidence: list[str] = Field(default_factory=list, description="Direct excerpts from the input")


class InterpretedSignal(BaseModel):
    signal_id: str
    signal: str
    zone: str
    classification: str = Field(description="Sustaining or Disruptive — New-Market / Low-End")
    confidence: str = Field(description="Low, Medium, or High")
    rationale: str
    alternative_explanation: str
    key_evidence_gap: str
    filters: list[str] = Field(default_factory=list, description="Disruption filter names that apply")


class PriorityEntry(BaseModel):
    signal_id: str
    signal: str
    impact: int = Field(ge=1, le=3, description="1=low 2=moderate 3=high")
    speed: int = Field(ge=1, le=3, description="1=slow 2=moderate 3=fast")
    score: int = Field(description="impact * speed")
    tier: str = Field(description="Act, Investigate, or Monitor")
    rationale: str


class SignalScanResult(BaseModel):
    """Complete Step 1 output from the SOC Radar agent."""
    signals: list[DetectedSignal]
    interpreted_signals: list[InterpretedSignal]
    priority_matrix: list[PriorityEntry]
    coverage_gaps: list[dict[str, str]] = Field(default_factory=list)
    agent_recommendation: str = Field(description="Summary recommendation for the consultant")


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------

def _build_messages(voc_data: str) -> list[SystemMessage | HumanMessage]:
    normalized = voc_data.strip()
    if not normalized:
        raise ValueError("Workflow input cannot be empty")

    skill_asset = PromptAssetLoader().load_skill_asset("soc-radar")

    system_prompt = (
        f"{skill_asset.body}\n\n"
        "You are the SOC Radar agent for the BMI consultant workflow.\n"
        "Work ONLY with the provided material. Execute Scan, Interpret, and Prioritize phases in one pass.\n"
        "Return only grounded signals with direct evidence excerpts from the source material.\n"
        "For each signal assign a unique snake_case signal_id.\n\n"
        "VALID SIGNAL ZONES (use exactly one per signal):\n"
        "  Nonconsumption, Overserved Customers, Low-End Foothold, "
        "New-Market Foothold, Business Model Anomaly, Enabling Technology, "
        "Regulatory / Policy Shift.\n"
        "Do NOT use disruption filter names (Asymmetric Motivation, Barrier Removal, etc.) as zones.\n\n"
        "VALID DISRUPTION FILTERS (use zero or more per interpreted signal):\n"
        "  Asymmetric Motivation, Asymmetric Skills, Trajectory, "
        "Performance Overshoot, Barrier Removal, Business Model Conflict.\n"
        "Do NOT invent new filter names.\n\n"
        "Score impact (1-3) and speed (1-3); compute score = impact * speed.\n"
        "Assign tier: score 7-9 → Act, 4-6 → Investigate, 1-3 → Monitor.\n"
        "If no disruptive signals are found, classify all as Sustaining.\n"
        "In agent_recommendation, summarize the highest-priority signals and any coverage blind spots."
    )
    user_prompt = (
        "Analyze the following Voice of Customer material and produce SOC Radar outputs.\n\n"
        f"{normalized}"
    )
    return [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]


# ---------------------------------------------------------------------------
# Core execution
# ---------------------------------------------------------------------------

_VALID_ZONES = {
    "Nonconsumption",
    "Overserved Customers",
    "Low-End Foothold",
    "New-Market Foothold",
    "Business Model Anomaly",
    "Enabling Technology",
    "Regulatory / Policy Shift",
}


def _build_coverage_gaps(signals: list[DetectedSignal]) -> list[dict[str, str]]:
    """Compute coverage gaps deterministically from detected signals."""
    detected_zones = {s.zone for s in signals}
    missing = sorted(_VALID_ZONES - detected_zones)
    return [
        {
            "zone": zone,
            "note": "No direct evidence found in this input; "
            "treat as an intelligence blind spot rather than proof of absence.",
        }
        for zone in missing
    ]


def run_step1_llm(state: BMIWorkflowState, llm: BaseChatModel) -> BMIWorkflowState:
    """Run Step 1 signal scan via the LLM and return updated workflow state."""
    voc_data = str(state.get("voc_data", ""))
    messages = _build_messages(voc_data)

    structured_llm = llm.with_structured_output(SignalScanResult)
    result: SignalScanResult = structured_llm.invoke(messages)

    return {
        **state,
        "current_step": "signal_scan",
        "signals": [s.model_dump() for s in result.signals],
        "interpreted_signals": [s.model_dump() for s in result.interpreted_signals],
        "priority_matrix": [s.model_dump() for s in result.priority_matrix],
        "coverage_gaps": _build_coverage_gaps(result.signals),
        "agent_recommendation": result.agent_recommendation,
    }
