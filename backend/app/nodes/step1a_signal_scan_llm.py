"""Step 1a LLM-backed signal scan and interpretation.

Loads the soc-radar SKILL.md as the system prompt, sends the VOC input
to the configured chat model, and returns structured signal outputs
for Phase 1 (Scan) and Phase 2 (Interpret) only.

Phase 3 (Prioritize) and Phase 4 (Recommend) are handled by step1b.
"""
from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from backend.app.llm.retry import invoke_with_retry
from backend.app.skills.loader import PromptAssetLoader
from backend.app.state import BMIWorkflowState


# ---------------------------------------------------------------------------
# Structured output schemas — Phase 1 (Scan) + Phase 2 (Interpret)
# ---------------------------------------------------------------------------

class DetectedSignal(BaseModel):
    signal_id: str = Field(description="Short snake_case identifier")
    signal: str = Field(description="Concise signal description grounded in source input")
    zone: str = Field(
        description="Primary SOC Radar signal zone. Must be one of: Nonconsumption, "
        "Overserved Customers, Low-End Foothold, New-Market Foothold, "
        "Business Model Anomaly, Enabling Technology, Regulatory / Policy Shift"
    )
    source_type: str = Field(default="Internal VoC")
    observable_behavior: str = Field(description="What is actually happening")
    evidence: list[str] = Field(description="Direct excerpts from the input")
    supporting_comments: list[int] = Field(
        description="Comment numbers from the input that support this signal (e.g., [3, 5, 12])"
    )


class DisruptionFilterAssessment(BaseModel):
    filter_name: str = Field(description="One of the 6 disruption filter names")
    result: str = Field(description="Yes, No, or Unclear")
    confidence: str = Field(description="Low, Medium, or High")
    rationale: str = Field(description="1-2 sentence rationale specific to this signal")


class InterpretedSignal(BaseModel):
    signal_id: str
    signal: str
    zone: str
    classification: str = Field(
        description="Sustaining, Disruptive — New-Market, or Disruptive — Low-End"
    )
    confidence: str = Field(description="Low, Medium, or High")
    # --- Sustaining fields (populated when classification == Sustaining) ---
    sustaining_rationale: str = Field(
        default="",
        description="Why this serves existing customers along known dimensions (sustaining only)"
    )
    competitive_implication: str = Field(
        default="",
        description="Whether and how the incumbent can respond (sustaining only)"
    )
    # --- Disruptive fields (populated when classification starts with Disruptive) ---
    litmus_test: str = Field(
        default="",
        description="Pass or Fail with 1-sentence rationale (disruptive only)"
    )
    filters: list[DisruptionFilterAssessment] = Field(
        default_factory=list,
        description="6-filter assessment table (disruptive only)"
    )
    filters_passed: int = Field(
        default=0,
        description="Count of filters with result=Yes"
    )
    disruptive_potential: str = Field(
        default="",
        description="Low, Medium, or High (disruptive only)"
    )
    value_network_insight: str = Field(
        default="",
        description="Why the incumbent's value network causes them to ignore this signal"
    )
    alternative_explanation: str = Field(
        default="",
        description="At least one reason this might not be disruptive"
    )
    key_evidence_gap: str = Field(
        default="",
        description="What additional data would most change the assessment"
    )


class ScanInterpretResult(BaseModel):
    """Step 1a output — Scan and Interpret phases."""
    signals: list[DetectedSignal]
    interpreted_signals: list[InterpretedSignal]


# ---------------------------------------------------------------------------
# Coverage gap computation
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


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------

def _build_messages(voc_data: str) -> list[SystemMessage | HumanMessage]:
    normalized = voc_data.strip()
    if not normalized:
        raise ValueError("Workflow input cannot be empty")

    skill_asset = PromptAssetLoader().load_skill_asset("soc-radar")

    system_prompt = (
        "{skill_body}\n\n"
        "You are the SOC Radar agent for the BMI consultant workflow.\n"
        "Execute ONLY Phase 1 (Scan) and Phase 2 (Interpret) from the skill above.\n"
        "Do NOT produce prioritization scores or recommendations — those come in a separate pass.\n\n"
        "SIGNAL EXTRACTION RULES:\n"
        "- Extract at least 7 distinct signals when the input contains 10+ observations\n"
        "- Do not collapse related phenomena into a single signal\n"
        "- Cite specific input comment numbers as supporting_comments for every signal\n"
        "- Every input comment should be cited by at least one signal\n\n"
        "CLASSIFICATION GATE:\n"
        "- Classify EVERY signal as Sustaining or Disruptive before any filter analysis\n"
        "- Sustaining signals: provide sustaining_rationale and competitive_implication; "
        "leave filter fields empty\n"
        "- Disruptive signals: apply litmus test, then assess ALL 6 filters with individual "
        "result/confidence/rationale per filter\n\n"
        "VALID SIGNAL ZONES: Nonconsumption, Overserved Customers, Low-End Foothold, "
        "New-Market Foothold, Business Model Anomaly, Enabling Technology, "
        "Regulatory / Policy Shift.\n"
        "VALID FILTERS: Asymmetric Motivation, Asymmetric Skills, Trajectory, "
        "Performance Overshoot, Barrier Removal, Business Model Conflict.\n"
    ).format(skill_body=skill_asset.body)

    user_prompt = (
        "Analyze the following Voice of Customer material.\n"
        "Execute Phase 1 (Scan) and Phase 2 (Interpret) only.\n\n"
        "{voc}"
    ).format(voc=normalized)

    return [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]


# ---------------------------------------------------------------------------
# Core execution
# ---------------------------------------------------------------------------

def run_step1a_llm(state: BMIWorkflowState, llm: BaseChatModel) -> BMIWorkflowState:
    """Run Step 1a signal scan + interpretation via the LLM and return updated state."""
    voc_data = str(state.get("voc_data", ""))
    messages = _build_messages(voc_data)

    structured_llm = llm.with_structured_output(ScanInterpretResult)
    result: ScanInterpretResult = invoke_with_retry(structured_llm, messages, step_name="step1a_signal_scan")

    return {
        **state,
        "current_step": "signal_scan",
        "signals": [s.model_dump() for s in result.signals],
        "interpreted_signals": [s.model_dump() for s in result.interpreted_signals],
        "coverage_gaps": _build_coverage_gaps(result.signals),
    }
