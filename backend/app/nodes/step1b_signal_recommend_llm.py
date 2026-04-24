"""Step 1b LLM-backed signal prioritization and recommendation.

Receives the detected and interpreted signals from Step 1a,
then executes Phase 3 (Prioritize) and Phase 4 (Recommend)
of the SOC Radar framework.
"""
from __future__ import annotations

import json

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from backend.app.llm.retry import invoke_with_retry
from backend.app.skills.loader import PromptAssetLoader
from backend.app.state import BMIWorkflowState


# ---------------------------------------------------------------------------
# Structured output schemas — Phase 3 (Prioritize) + Phase 4 (Recommend)
# ---------------------------------------------------------------------------

class PriorityEntry(BaseModel):
    signal_id: str
    signal: str
    classification: str = Field(description="Carried from interpretation")
    impact: int = Field(ge=1, le=3)
    speed: int = Field(ge=1, le=3)
    score: int = Field(description="impact * speed")
    tier: str = Field(
        description="Act, Investigate, Monitor, Sustaining — Act, or Sustaining — Investigate"
    )
    rationale: str = Field(description="2-3 sentences referencing evidence from Interpret phase")


class ReinforcementMap(BaseModel):
    chain: list[str] = Field(description="Ordered list of signal names forming a causal chain")
    strategic_insight: str = Field(description="Where intervention is most efficient")
    accelerants: list[str] = Field(
        default_factory=list,
        description="Sustaining signals that weaken incumbent's ability to respond"
    )


class RPVAssessment(BaseModel):
    resources: str = Field(description="Can the incumbent deploy capital, talent, or technology?")
    processes: str = Field(description="Are incumbent processes aligned or misaligned?")
    values: str = Field(description="Does cost structure make response attractive?")
    assessment: str = Field(
        description="Can respond / Cannot respond without structural change / Would choose not to respond"
    )


class NextStep(BaseModel):
    action: str = Field(description="Specific action description")
    owner: str = Field(description="Suggested owner role")
    timeframe: str = Field(description="e.g., 30 days, 60 days")


class ExperimentCandidate(BaseModel):
    assumption: str = Field(description="Starts with 'We believe that...'")
    experiment_type: str = Field(
        description="Customer Interview / Smoke Test / Concierge / Prototype / Survey"
    )
    success: str = Field(description="What success looks like")
    failure: str = Field(description="What failure looks like")


class SignalRecommendation(BaseModel):
    signal_id: str
    action_tier: str = Field(description="Act or Investigate")
    what_we_know: str
    what_we_dont_know: list[str]
    rpv_assessment: RPVAssessment
    next_steps: list[NextStep]
    experiment_candidate: ExperimentCandidate


class WatchingBrief(BaseModel):
    signal_id: str
    signal: str
    review_frequency: str = Field(default="Quarterly")
    key_indicator: str
    escalation_trigger: str


class PrioritizeRecommendResult(BaseModel):
    """Step 1b output — Prioritize and Recommend phases."""
    priority_matrix: list[PriorityEntry]
    reinforcement_map: ReinforcementMap
    recommendations: list[SignalRecommendation] = Field(
        default_factory=list,
        description="For Act and Investigate tier signals only"
    )
    watching_briefs: list[WatchingBrief] = Field(
        default_factory=list,
        description="For Monitor tier signals only"
    )
    agent_recommendation: str = Field(description="Summary for the consultant")


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------

def _build_messages(
    voc_data: str,
    signals: list[dict],
    interpreted_signals: list[dict],
) -> list[SystemMessage | HumanMessage]:
    if not signals:
        raise ValueError("Step 1b requires signals from Step 1a")

    skill_asset = PromptAssetLoader().load_skill_asset("soc-radar")

    system_prompt = (
        "{skill_body}\n\n"
        "You are the SOC Radar agent for the BMI consultant workflow.\n"
        "Phase 1 (Scan) and Phase 2 (Interpret) have already been completed.\n"
        "Execute ONLY Phase 3 (Prioritize) and Phase 4 (Recommend).\n\n"
        "PRIORITIZATION RULES:\n"
        "- Score every signal on impact (1-3) and speed (1-3); score = impact * speed\n"
        "- Tier: 7-9 = Act, 4-6 = Investigate, 1-3 = Monitor\n"
        "- Sustaining signals use tiers: Sustaining — Act, Sustaining — Investigate, "
        "Sustaining — Monitor\n"
        "- Past-tense switching language in VoC (e.g., 'we moved to Dell') = speed 3\n"
        "- Multiple independent comments citing the same procurement trigger = impact 3\n\n"
        "REINFORCEMENT MAP:\n"
        "- After scoring, identify causal chains between signals\n"
        "- Note which sustaining signals act as accelerants\n\n"
        "RECOMMENDATION RULES:\n"
        "- Act/Investigate signals: full RPV assessment (Resources, Processes, Values separately), "
        "2+ next steps with owner and timeframe, experiment candidate with success/failure criteria\n"
        "- Monitor signals: watching brief with key indicator and escalation trigger\n"
    ).format(skill_body=skill_asset.body)

    user_prompt = (
        "The following signals were detected and interpreted from Voice of Customer data.\n"
        "Prioritize them and provide recommendations.\n\n"
        "## Original VoC Data\n{voc}\n\n"
        "## Detected Signals\n{signals}\n\n"
        "## Interpreted Signals\n{interpreted}"
    ).format(
        voc=voc_data.strip(),
        signals=json.dumps(signals, indent=2),
        interpreted=json.dumps(interpreted_signals, indent=2),
    )

    return [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]


# ---------------------------------------------------------------------------
# Core execution
# ---------------------------------------------------------------------------

def run_step1b_llm(state: BMIWorkflowState, llm: BaseChatModel) -> BMIWorkflowState:
    """Run Step 1b prioritization + recommendation via the LLM and return updated state."""
    voc_data = str(state.get("voc_data", ""))
    signals = state.get("signals", [])
    interpreted_signals = state.get("interpreted_signals", [])

    messages = _build_messages(voc_data, signals, interpreted_signals)

    structured_llm = llm.with_structured_output(PrioritizeRecommendResult)
    result: PrioritizeRecommendResult = invoke_with_retry(
        structured_llm, messages, step_name="step1b_signal_recommend"
    )

    return {
        **state,
        "current_step": "signal_recommend",
        "priority_matrix": [p.model_dump() for p in result.priority_matrix],
        "reinforcement_map": result.reinforcement_map.model_dump(),
        "signal_recommendations": [r.model_dump() for r in result.recommendations],
        "watching_briefs": [w.model_dump() for w in result.watching_briefs],
        "agent_recommendation": result.agent_recommendation,
    }
