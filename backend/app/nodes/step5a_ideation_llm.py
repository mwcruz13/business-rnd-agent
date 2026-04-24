"""Step 5a LLM-backed VP Portfolio Ideation.

Generates N distinct, pattern-coherent Value Proposition alternatives
using the Strategyzer Value Proposition Design and Invincible Company
methodologies. Each alternative explores a different pattern flavor or
customer job focus while maintaining coherence with the selected
business model patterns from Step 2.
"""
from __future__ import annotations

import json
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from backend.app.llm.retry import invoke_with_retry
from backend.app.patterns.loader import PatternLibraryLoader
from backend.app.skills.loader import PromptAssetLoader
from backend.app.state import BMIWorkflowState


# ---------------------------------------------------------------------------
# Structured output schemas
# ---------------------------------------------------------------------------

class ProductService(BaseModel):
    type: str = Field(description="Digital, Physical, Intangible, or Financial")
    product_service: str = Field(
        description="A specific product or service the supplier offers"
    )
    relevance: str = Field(description="Core, Nice-to-have, or Supporting")


class PainReliever(BaseModel):
    type: str = Field(description="Functional, Social, or Emotional")
    pain_reliever: str = Field(
        description="How the supplier's product or service relieves this customer pain"
    )
    pain_addressed: str = Field(
        description="Must reference a specific customer pain from the empathy profile"
    )
    relevance: str = Field(description="Substantial, Nice-to-have, or Minor")


class GainCreator(BaseModel):
    type: str = Field(description="Functional, Social, Emotional, or Financial")
    gain_creator: str = Field(
        description="How the supplier's product or service creates or enhances this customer gain"
    )
    gain_addressed: str = Field(
        description="Must reference a specific customer gain from the empathy profile"
    )
    relevance: str = Field(description="Substantial, Nice-to-have, or Minor")


class AdLibPrototype(BaseModel):
    statement: str = Field(
        description="OUR [product] HELP [segment] WHO WANT TO [job] BY [pain relief] AND [gain creation]"
    )


class VPAlternative(BaseModel):
    """A single Value Proposition alternative within the portfolio."""
    name: str = Field(description="Descriptive VP name")
    pattern_flavor_applied: str = Field(
        description="Which pattern flavor(s) this VP explores"
    )
    strategic_rationale: str = Field(
        description="Why this VP is coherent with the pattern's strategic imperative"
    )
    target_segment: str = Field(
        description="Who this VP serves — must align with the pattern"
    )
    primary_job_focus: str = Field(
        description="Which customer job from the empathy profile is the primary focus"
    )
    context_scenario: str = Field(
        description="The customer context or situation being addressed"
    )
    products_services: list[ProductService] = Field(
        description="At least 1 product or service"
    )
    pain_relievers: list[PainReliever] = Field(
        description="At least 1 pain reliever mapped to customer pains"
    )
    gain_creators: list[GainCreator] = Field(
        description="At least 1 gain creator mapped to customer gains"
    )
    ad_lib_prototype: AdLibPrototype
    pattern_coherence_note: str = Field(
        description="How this VP answers the pattern's trigger question affirmatively"
    )


class VPIdeationOutput(BaseModel):
    """Complete Step 5a output: VP Portfolio Ideation."""
    pattern_context: str = Field(
        description="Selected patterns and direction summary"
    )
    ideation_rationale: str = Field(
        description="How alternatives were derived from pattern × empathy matrix"
    )
    alternatives: list[VPAlternative] = Field(
        description="N distinct VP alternatives"
    )
    diversity_check: str = Field(
        description="Self-assessment of how alternatives differ across axes"
    )


# ---------------------------------------------------------------------------
# Pattern context formatting
# ---------------------------------------------------------------------------

def _format_pattern_context(pattern_details: list[dict[str, Any]]) -> str:
    """Format rich pattern details for injection into the LLM prompt."""
    sections: list[str] = []
    for p in pattern_details:
        lines = [
            f"### Pattern: {p['name']}",
            f"- **Direction:** {p['direction'].upper()}",
            f"- **Category:** {p['category']}",
            f"- **Strategic Imperative:** {p['strategic_imperative']}",
            f"- **Description:** {p['description']}",
            f"- **Trigger Question:** {p['trigger_question']}",
            f"- **Assessment Question:** {p['assessment_question']}",
        ]
        if p.get("flavors"):
            lines.append("- **Flavors:**")
            for flavor in p["flavors"]:
                lines.append(f"  - **{flavor['name']}:** {flavor.get('description', '')}")
                if flavor.get("trigger_question"):
                    lines.append(f"    Trigger: {flavor['trigger_question']}")
                if flavor.get("examples"):
                    lines.append(f"    Examples: {', '.join(flavor['examples'])}")
        sections.append("\n".join(lines))
    return "\n\n".join(sections)


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------

def _build_messages(
    state: BMIWorkflowState, pattern_details: list[dict[str, Any]]
) -> list[SystemMessage | HumanMessage]:
    customer_profile = str(state.get("customer_profile", ""))
    actionable_insights = str(state.get("actionable_insights", ""))
    if not customer_profile.strip():
        raise ValueError("Customer profile is required for Step 5a")

    skill_asset = PromptAssetLoader().load_step_prompt("step5a_vp_ideation")
    selected_patterns = ", ".join(state.get("selected_patterns", [])) or "approved patterns"
    pattern_direction = str(state.get("pattern_direction", ""))
    pattern_context_text = _format_pattern_context(pattern_details)
    num_alternatives = state.get("num_vp_alternatives") or 3

    # Direction-aware system prompt: INVENT gets creative latitude, SHIFT gets VDT scope
    is_invent = pattern_direction.lower() == "invent"

    direction_guidance = (
        "IMPORTANT: You are in INVENT mode — exploring NEW business models.\n"
        "The Value Driver Tree reflects the CURRENT business model, NOT your target.\n"
        "DO NOT constrain alternatives to one-per-deliverable from the VDT.\n"
        "Your primary creative drivers are: pattern flavors × customer jobs × context scenarios.\n"
        "Each alternative must explore genuinely different market opportunities.\n"
        "The VDT is provided only for awareness of what exists today — diverge from it.\n"
    ) if is_invent else (
        "You are in SHIFT mode — improving the existing business model.\n"
        "The Value Driver Tree defines the scope of improvement.\n"
        "Use it to understand WHICH value areas to address, but still generate\n"
        f"{num_alternatives} distinct alternatives by varying HOW the pattern improves each area.\n"
        "Do not collapse alternatives to one-per-deliverable — vary flavors, job focus, and context.\n"
    )

    system_prompt = (
        f"{skill_asset.body}\n\n"
        "You are the CXIF Value Proposition Portfolio Ideation agent.\n"
        "You are designing MULTIPLE distinct value propositions FROM THE SUPPLIER'S PERSPECTIVE.\n"
        "Each alternative must be coherent with the selected business model patterns.\n"
        "Patterns are the PRIMARY design constraint — they determine segment, operating model, and revenue mechanics.\n\n"
        f"{direction_guidance}\n"
        f"Generate exactly {num_alternatives} distinct VP alternatives.\n"
        "Each must explore a DIFFERENT pattern flavor or customer job focus.\n"
        "Each must satisfy all 5 pattern-coherence validation rules.\n"
        "Do not produce minor variations of the same proposition.\n"
    )

    voc_data = str(state.get("voc_data", ""))[:2000]
    vdt_content = state.get("value_driver_tree", "") or ""

    # Frame VDT differently based on direction
    vdt_section = (
        f"## Value Driver Tree (Background Context Only — DO NOT CONSTRAIN)\n"
        f"The following describes the CURRENT model. Your job is to invent BEYOND it.\n"
        f"{vdt_content}"
    ) if is_invent else (
        f"## Value Driver Tree (Improvement Scope)\n"
        f"Use this to understand the value areas that need improvement.\n"
        f"{vdt_content}"
    )

    user_prompt = (
        f"## Pattern Direction: {pattern_direction}\n"
        f"## Selected Patterns: {selected_patterns}\n\n"
        f"## Full Pattern Details\n{pattern_context_text}\n\n"
        f"## Customer Empathy Profile\n{customer_profile}\n\n"
        f"## Context Analysis & Actionable Insights\n{actionable_insights}\n\n"
        f"{vdt_section}\n\n"
        f"## Original Voice of Customer Evidence (for grounding)\n{voc_data}\n\n"
        f"Generate exactly {num_alternatives} distinct VP alternatives."
    )
    return [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]


# ---------------------------------------------------------------------------
# Markdown rendering
# ---------------------------------------------------------------------------

def _render_vp_alternative(alt: VPAlternative, index: int) -> str:
    """Render a single VP alternative to markdown."""
    lines = [
        f"## VP Alternative {index + 1}: {alt.name}",
        "",
        f"**Pattern Flavor:** {alt.pattern_flavor_applied}",
        f"**Target Segment:** {alt.target_segment}",
        f"**Primary Job Focus:** {alt.primary_job_focus}",
        f"**Context:** {alt.context_scenario}",
        f"**Strategic Rationale:** {alt.strategic_rationale}",
        "",
        "### Value Map",
        "",
        "#### Products & Services",
        "| Type | Product/Service | Relevance |",
        "|------|----------------|-----------|",
    ]
    for ps in alt.products_services:
        lines.append(f"| {ps.type} | {ps.product_service} | {ps.relevance} |")

    lines.extend([
        "",
        "#### Pain Relievers",
        "| Type | Pain Reliever | Pain Addressed | Relevance |",
        "|------|--------------|----------------|-----------|",
    ])
    for pr in alt.pain_relievers:
        lines.append(
            f"| {pr.type} | {pr.pain_reliever} | {pr.pain_addressed} | {pr.relevance} |"
        )

    lines.extend([
        "",
        "#### Gain Creators",
        "| Type | Gain Creator | Gain Addressed | Relevance |",
        "|------|-------------|----------------|-----------|",
    ])
    for gc in alt.gain_creators:
        lines.append(
            f"| {gc.type} | {gc.gain_creator} | {gc.gain_addressed} | {gc.relevance} |"
        )

    stmt = alt.ad_lib_prototype.statement
    if stmt.upper().startswith("OUR "):
        stmt = stmt[4:]
    lines.extend([
        "",
        "### Ad-Lib Prototype",
        f"> **OUR** {stmt}",
        "",
        f"**Pattern Coherence:** {alt.pattern_coherence_note}",
    ])
    return "\n".join(lines)


def _render_portfolio(result: VPIdeationOutput, selected_patterns: list[str]) -> str:
    """Render the full VP portfolio to combined markdown."""
    pattern_context = ", ".join(selected_patterns) or "approved patterns"
    lines = [
        "# Value Proposition Portfolio",
        "",
        f"Pattern context: {pattern_context}.",
        f"Ideation rationale: {result.ideation_rationale}",
        "",
    ]
    for i, alt in enumerate(result.alternatives):
        lines.append(_render_vp_alternative(alt, i))
        lines.append("")

    lines.append(f"**Diversity Check:** {result.diversity_check}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Core execution
# ---------------------------------------------------------------------------

def run_step5a_llm(state: BMIWorkflowState, llm: BaseChatModel) -> BMIWorkflowState:
    """Run Step 5a VP Portfolio Ideation via the LLM."""
    selected_patterns = state.get("selected_patterns", [])
    pattern_details = PatternLibraryLoader().load_pattern_details(selected_patterns)

    messages = _build_messages(state, pattern_details)
    structured_llm = llm.with_structured_output(VPIdeationOutput)
    result: VPIdeationOutput = invoke_with_retry(
        structured_llm, messages, step_name="step5a_ideation"
    )

    # Serialize alternatives to dicts for state storage
    vp_alternatives = [alt.model_dump() for alt in result.alternatives]

    return {
        **state,
        "current_step": "vp_ideation",
        "vp_alternatives": vp_alternatives,
        "value_proposition_canvas": _render_portfolio(result, selected_patterns),
    }
