"""Step 4 LLM-backed CXIF Measure + Define synthesis.

Uses the cxif-bmi-coach SKILL as system prompt to generate a Value Driver Tree
(Measure phase) and Context Analysis with actionable insights (Define phase)
from the upstream empathy profile and VoC data.
"""
from __future__ import annotations

import json

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from backend.app.skills.loader import PromptAssetLoader
from backend.app.state import BMIWorkflowState


# ---------------------------------------------------------------------------
# Structured output schemas
# ---------------------------------------------------------------------------

class SuccessMeasure(BaseModel):
    key_deliverable: str
    success_measure: str
    baseline: str
    target: str
    driver_type: str = Field(description="Time, Effort, Volume, Cost, Satisfaction, or Revenue")


class ValueDriverTree(BaseModel):
    customer_business_outcome: str = Field(description="The measurable business outcome the customer aims to achieve")
    success_measures: list[SuccessMeasure] = Field(description="At least 2 key deliverables with success criteria")


class ValueChainEntry(BaseModel):
    activity: str
    role_in_value_creation: str
    weak_link: str = Field(description="Yes or No")
    impact_on_customer: str


class FrictionPoint(BaseModel):
    journey_phase: str
    touchpoint: str
    customer_experience: str
    friction_type: str = Field(description="Delay, Effort, Confusion, Access, or Cost")
    opportunity: str


class ProblemStatement(BaseModel):
    number: int
    problem_statement: str
    jobs_affected: str
    pains_addressed: str
    priority: str = Field(description="High, Medium, or Low")


class ContextAnalysis(BaseModel):
    value_chain: list[ValueChainEntry] = Field(description="At least 1 value chain entry")
    friction_points: list[FrictionPoint] = Field(description="At least 1 friction point")
    who: str = Field(description="Customer segment")
    does: str = Field(description="What the customer is trying to do")
    because: str = Field(description="Why they need to do it")
    but_statement: str = Field(description="What is preventing them")
    problem_statements: list[ProblemStatement] = Field(description="At least 1 problem statement")


class Step4Output(BaseModel):
    """Complete Step 4 output combining CXIF Measure and Define phases."""
    value_driver_tree: ValueDriverTree
    context_analysis: ContextAnalysis


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------

def _build_messages(state: BMIWorkflowState) -> list[SystemMessage | HumanMessage]:
    customer_profile = str(state.get("customer_profile", ""))
    if not customer_profile.strip():
        raise ValueError("Customer profile is required for Step 4")

    skill_asset = PromptAssetLoader().load_step_prompt("step4_measure_define")
    selected_patterns = ", ".join(state.get("selected_patterns", [])) or "approved patterns"
    pattern_direction = str(state.get("pattern_direction", ""))

    system_prompt = (
        f"{skill_asset.body}\n\n"
        "You are the CXIF Measure + Define agent for the BMI consultant workflow.\n"
        "Execute Phase 2 (Measure) and Phase 3 (Define) from the CXIF framework.\n\n"
        "MEASURE PHASE — produce a Value Driver Tree:\n"
        "- Identify the Customer Business Outcome (measurable benefit the customer aims to achieve).\n"
        "- Define Key Deliverables with Success Measures, Baselines, and Targets.\n"
        "- Success measures should use customer terms (time-to-value, effort, satisfaction, cost).\n"
        "- Reference the selected patterns in the business outcome.\n\n"
        "DEFINE PHASE — produce a Context Analysis:\n"
        "- You are analyzing the value chain from the SUPPLIER'S perspective — identify where the\n"
        "  supplier's activities, resources, and partnerships create or fail to create value for the customer.\n"
        "- Assess the value chain to identify supplier-side weak links affecting the customer.\n"
        "- Map customer journey friction points caused by supplier operations (by phase, touchpoint, experience, friction type).\n"
        "- Consider BOTH the customer context AND the supplier context — people, systems, patterns, and problems on both sides.\n"
        "- Synthesize actionable insights as a WHO-DOES-BECAUSE-BUT statement.\n"
        "- Frame at least 1 prioritized problem statement grounded in the empathy profile.\n\n"
        "RULES:\n"
        "- Ground all outputs in the customer profile, signals, and VoC evidence.\n"
        "- Do not fabricate data without supporting evidence.\n"
        "- Use the customer's language, not internal jargon."
    )

    signal_summary = json.dumps(state.get("interpreted_signals", [])[:3], indent=2)

    user_prompt = (
        f"Pattern direction: {pattern_direction}\n"
        f"Selected patterns: {selected_patterns}\n\n"
        f"Customer Empathy Profile:\n{customer_profile}\n\n"
        f"Interpreted signals:\n{signal_summary}\n\n"
        f"Voice of Customer:\n{state.get('voc_data', '')}"
    )
    return [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]


# ---------------------------------------------------------------------------
# Markdown rendering
# ---------------------------------------------------------------------------

def _render_value_driver_tree(vdt: ValueDriverTree, selected_patterns: list[str]) -> str:
    pattern_context = ", ".join(selected_patterns) or "approved patterns"
    lines = [
        "## Value Driver Tree",
        "",
        "### Customer Business Outcome",
        f"{vdt.customer_business_outcome} The direction is being explored through {pattern_context}.",
        "",
        "### Key Deliverables and Success Measures",
        "| Key Deliverable | Success Measure | Baseline | Target | Driver Type |",
        "|----------------|----------------|----------|--------|-------------|",
    ]
    for sm in vdt.success_measures:
        lines.append(f"| {sm.key_deliverable} | {sm.success_measure} | {sm.baseline} | {sm.target} | {sm.driver_type} |")
    return "\n".join(lines)


def _render_context_analysis(ca: ContextAnalysis) -> str:
    lines = [
        "## Context Analysis",
        "",
        "### Value Chain Assessment",
        "| Activity | Role in Value Creation | Weak Link? | Impact on Customer |",
        "|----------|----------------------|------------|-------------------|",
    ]
    for entry in ca.value_chain:
        lines.append(f"| {entry.activity} | {entry.role_in_value_creation} | {entry.weak_link} | {entry.impact_on_customer} |")

    lines.extend([
        "",
        "### Customer Journey Friction Points",
        "| Journey Phase | Touchpoint | Customer Experience | Friction Type | Opportunity |",
        "|---------------|-----------|-------------------|---------------|-------------|",
    ])
    for fp in ca.friction_points:
        lines.append(f"| {fp.journey_phase} | {fp.touchpoint} | {fp.customer_experience} | {fp.friction_type} | {fp.opportunity} |")

    lines.extend([
        "",
        "### Actionable Insights",
        f"**{ca.who}** DOES **{ca.does}** BECAUSE **{ca.because}** BUT **{ca.but_statement}**",
        "",
        "### Problem Statements",
        "| # | Problem Statement | Jobs Affected | Pains Addressed | Priority |",
        "|---|------------------|--------------|-----------------|----------|",
    ])
    for ps in ca.problem_statements:
        lines.append(f"| {ps.number} | {ps.problem_statement} | {ps.jobs_affected} | {ps.pains_addressed} | {ps.priority} |")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Core execution
# ---------------------------------------------------------------------------

def run_step4_llm(state: BMIWorkflowState, llm: BaseChatModel) -> BMIWorkflowState:
    """Run Step 4 CXIF Measure + Define via the LLM."""
    messages = _build_messages(state)
    structured_llm = llm.with_structured_output(Step4Output)
    result: Step4Output = structured_llm.invoke(messages)

    selected_patterns = state.get("selected_patterns", [])

    return {
        **state,
        "current_step": "measure_define",
        "value_driver_tree": _render_value_driver_tree(result.value_driver_tree, selected_patterns),
        "actionable_insights": _render_context_analysis(result.context_analysis),
    }
