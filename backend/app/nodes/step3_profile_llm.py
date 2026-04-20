"""Step 3 LLM-backed customer empathy profile using the CXIF BMI Coach SKILL.

Loads the cxif-bmi-coach SKILL.md as the system prompt, sends the VoC data
plus upstream workflow context to the chat model, and returns a structured
Customer Empathy Profile compatible with the BMIWorkflowState contract.
"""
from __future__ import annotations

import json

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from backend.app.skills.loader import PromptAssetLoader
from backend.app.llm.retry import invoke_with_retry
from backend.app.state import BMIWorkflowState


# ---------------------------------------------------------------------------
# Structured output schemas
# ---------------------------------------------------------------------------

class CustomerJob(BaseModel):
    type: str = Field(description="Functional, Social, Emotional, or Supporting")
    job: str = Field(description="Task or problem the customer is trying to solve")
    importance: str = Field(description="High, Medium, or Low")


class CustomerPain(BaseModel):
    type: str = Field(description="Functional, Social, Emotional, or Ancillary")
    pain: str = Field(description="Difficulty or challenge encountered")
    severity: str = Field(description="Severe, Moderate, or Light")


class CustomerGain(BaseModel):
    type: str = Field(description="Functional, Social, Emotional, or Financial")
    gain: str = Field(description="Outcome or benefit required, expected, or desired")
    relevance: str = Field(description="Essential, Expected, Desired, or Unexpected")


class CustomerEmpathyProfile(BaseModel):
    """Complete Step 3 output: CXIF Phase 1 Empathy profile."""
    customer_segment: str = Field(description="Description of the customer segment being profiled")
    jobs: list[CustomerJob] = Field(description="Customer jobs grounded in VoC evidence")
    pains: list[CustomerPain] = Field(description="Customer pains grounded in VoC evidence")
    gains: list[CustomerGain] = Field(description="Customer gains grounded in VoC evidence")


# ---------------------------------------------------------------------------
# CXIF trigger questions — sourced from CXIF training material (Empathize phase)
# Used by the empathy gate to request additional context from the human.
# ---------------------------------------------------------------------------

EMPATHY_TRIGGER_QUESTIONS: dict[str, list[tuple[str, str]]] = {
    "jobs": [
        ("Functional", "What important issue is the customer trying to resolve in his work or personal life?"),
        ("Social", "How does your customer want to be perceived by others?"),
        ("Emotional", "What jobs, if completed, would give the user a sense of self-satisfaction?"),
        ("Supporting", "Does the user switch roles throughout this process?"),
    ],
    "pains": [
        ("Functional", "What are the main difficulties and challenges your customers encounter?"),
        ("Social", "What negative social consequences do your customers encounter or fear?"),
        ("Emotional", "What makes your customer feel bad? E.g. what are their frustrations, annoyances, or the things that give them a headache?"),
        ("Ancillary", "What annoys your customers when/before/after getting a job done?"),
    ],
    "gains": [
        ("Functional", "What outcomes and benefits your customers require, expect, desire or would be surprised by?"),
        ("Social", "What positive social consequences do your customers desire?"),
        ("Emotional", "How do current solutions delight your customers?"),
        ("Financial", "How do your customers measure success and failure, and which savings would make your customers happy?"),
    ],
}


def check_empathy_gate(profile: CustomerEmpathyProfile) -> dict[str, list[tuple[str, str]]]:
    """Return CXIF trigger questions for any section that has zero items or lacks type diversity."""
    gaps: dict[str, list[tuple[str, str]]] = {}

    if not profile.jobs:
        gaps["jobs"] = EMPATHY_TRIGGER_QUESTIONS["jobs"]
    elif len({j.type for j in profile.jobs}) < 2:
        existing_types = {j.type for j in profile.jobs}
        gaps["jobs"] = [(t, q) for t, q in EMPATHY_TRIGGER_QUESTIONS["jobs"] if t not in existing_types]

    if not profile.pains:
        gaps["pains"] = EMPATHY_TRIGGER_QUESTIONS["pains"]
    elif len({p.type for p in profile.pains}) < 2:
        existing_types = {p.type for p in profile.pains}
        gaps["pains"] = [(t, q) for t, q in EMPATHY_TRIGGER_QUESTIONS["pains"] if t not in existing_types]

    if not profile.gains:
        gaps["gains"] = EMPATHY_TRIGGER_QUESTIONS["gains"]
    elif len({g.type for g in profile.gains}) < 2:
        existing_types = {g.type for g in profile.gains}
        gaps["gains"] = [(t, q) for t, q in EMPATHY_TRIGGER_QUESTIONS["gains"] if t not in existing_types]

    return gaps


def format_gate_questions(gaps: dict[str, list[tuple[str, str]]]) -> str:
    """Format trigger questions as markdown for the human-in-the-loop."""
    lines = [
        "## Additional Context Needed",
        "",
        "The empathy profile is missing information in the following sections.",
        "Please answer the trigger questions below to help build a complete profile:",
        "",
    ]
    for section, questions in gaps.items():
        lines.append(f"### {section.title()}")
        for type_name, question in questions:
            lines.append(f"- **{type_name}**: {question}")
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------

def _build_messages(
    voc_data: str,
    interpreted_signals: list[dict],
    selected_patterns: list[str],
    pattern_direction: str,
    supplemental_voc: str = "",
) -> list[SystemMessage | HumanMessage]:
    normalized = voc_data.strip()
    if not normalized:
        raise ValueError("Workflow input cannot be empty")

    skill_asset = PromptAssetLoader().load_step_prompt("step3_empathize")

    system_prompt = (
        f"{skill_asset.body}\n\n"
        "You are the CXIF Empathy agent for the BMI consultant workflow.\n"
        "Execute ONLY Phase 1 (Empathize) from the CXIF framework.\n"
        "Work with the provided VoC material and upstream signal analysis.\n"
        "Generate a Customer Empathy Profile grounded in evidence from the source material.\n\n"
        "RULES:\n"
        "- Generate jobs, pains, and gains proportional to the evidence available.\n"
        "- Produce at least 1 of each where evidence exists. Do not fabricate items without supporting evidence.\n"
        "- Cover multiple types (Functional, Social, Emotional, etc.) where the evidence supports it.\n"
        "- Aim for at least 2 distinct types per section (jobs, pains, gains).\n"
        "- Jobs must describe what the CUSTOMER is trying to accomplish, not what the supplier wants.\n"
        "- Pains must describe what annoys the CUSTOMER, not supplier-side concerns.\n"
        "- Gains must describe what the CUSTOMER values, not supplier assumptions.\n"
        "- Use the customer's language from the VoC, not internal jargon.\n"
        "- Rank jobs by importance, pains by severity, and gains by relevance.\n"
        "- The customer segment must reference the pattern direction and selected patterns."
    )

    signal_summary = json.dumps(interpreted_signals[:3], indent=2) if interpreted_signals else "No signal data"
    pattern_context = ", ".join(selected_patterns) or "approved patterns"

    user_prompt = (
        f"Pattern direction: {pattern_direction}\n"
        f"Selected patterns: {pattern_context}\n\n"
        f"Interpreted signals from Step 1:\n{signal_summary}\n\n"
        f"Voice of Customer material:\n{normalized}"
    )
    if supplemental_voc.strip():
        user_prompt += f"\n\nAdditional context from consultant:\n{supplemental_voc.strip()}"

    return [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]


# ---------------------------------------------------------------------------
# Markdown rendering
# ---------------------------------------------------------------------------

def _render_profile_markdown(profile: CustomerEmpathyProfile, selected_patterns: list[str]) -> str:
    pattern_context = ", ".join(selected_patterns) or "approved patterns"
    lines = [
        "## Customer Empathy Profile",
        "",
        "### Customer Segment",
        profile.customer_segment,
        f"Consultant-approved pattern context: {pattern_context}.",
        "",
        "### Customer Jobs",
        "| Type | Job | Importance |",
        "|------|-----|------------|",
    ]
    for job in profile.jobs:
        lines.append(f"| {job.type} | {job.job} | {job.importance} |")

    lines.extend([
        "",
        "### Customer Pains",
        "| Type | Pain | Severity |",
        "|------|------|----------|",
    ])
    for pain in profile.pains:
        lines.append(f"| {pain.type} | {pain.pain} | {pain.severity} |")

    lines.extend([
        "",
        "### Customer Gains",
        "| Type | Gain | Relevance |",
        "|------|------|-----------|",
    ])
    for gain in profile.gains:
        lines.append(f"| {gain.type} | {gain.gain} | {gain.relevance} |")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Core execution
# ---------------------------------------------------------------------------

def run_step3_llm(state: BMIWorkflowState, llm: BaseChatModel) -> BMIWorkflowState:
    """Run Step 3 customer empathy profile via the LLM and return updated workflow state.

    Empathy gate: after the LLM produces the profile, checks for completely
    empty sections (jobs, pains, or gains).  On the first run, if any section
    is empty the gate fires — the partial profile is stored and CXIF trigger
    questions are returned so the human-in-the-loop can supply additional
    context.  On a retry (``supplemental_voc`` present in state) the gate is
    skipped and whatever the LLM produces is accepted (single retry).
    """
    voc_data = str(state.get("voc_data", ""))
    supplemental_voc = str(state.get("supplemental_voc", ""))
    interpreted_signals = state.get("interpreted_signals", [])
    selected_patterns = state.get("selected_patterns", [])
    pattern_direction = str(state.get("pattern_direction", ""))

    messages = _build_messages(
        voc_data, interpreted_signals, selected_patterns,
        pattern_direction, supplemental_voc,
    )

    structured_llm = llm.with_structured_output(CustomerEmpathyProfile)
    result: CustomerEmpathyProfile = invoke_with_retry(structured_llm, messages, step_name="step3_customer_profile")

    customer_profile = _render_profile_markdown(result, selected_patterns)

    # --- Empathy gate (section-level, single retry) ---
    is_retry = bool(supplemental_voc.strip())
    gaps = check_empathy_gate(result)

    if gaps and not is_retry:
        return {
            **state,
            "current_step": "empathize",
            "customer_profile": customer_profile,
            "empathy_gap_questions": format_gate_questions(gaps),
        }

    # Happy path or retry — accept the profile as-is.
    return {
        **state,
        "current_step": "empathize",
        "customer_profile": customer_profile,
    }
