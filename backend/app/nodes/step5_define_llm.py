"""Step 5 LLM-backed CXIF Value Proposition Canvas design.

Uses the cxif-bmi-coach SKILL to generate a Value Proposition Canvas
including Products & Services, Pain Relievers, Gain Creators, and Ad-Lib
Prototypes from the upstream empathy profile and problem framing.
"""
from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from backend.app.skills.loader import PromptAssetLoader
from backend.app.state import BMIWorkflowState


# ---------------------------------------------------------------------------
# Structured output schemas
# ---------------------------------------------------------------------------

class ProductService(BaseModel):
    type: str = Field(description="Digital, Physical, Intangible, or Financial")
    product_service: str
    relevance: str = Field(description="Core, Nice-to-have, or Supporting")


class PainReliever(BaseModel):
    type: str = Field(description="Functional, Social, or Emotional")
    pain_reliever: str
    pain_addressed: str = Field(description="Must reference a specific customer pain from the empathy profile")
    relevance: str = Field(description="Substantial, Nice-to-have, or Minor")


class GainCreator(BaseModel):
    type: str = Field(description="Functional, Social, Emotional, or Financial")
    gain_creator: str
    gain_addressed: str = Field(description="Must reference a specific customer gain from the empathy profile")
    relevance: str = Field(description="Substantial, Nice-to-have, or Minor")


class AdLibPrototype(BaseModel):
    statement: str = Field(description="OUR [product] HELP [segment] WHO WANT TO [job] BY [pain relief] AND [gain creation]")


class ValuePropositionCanvas(BaseModel):
    """Complete Step 5 output: CXIF Value Proposition Canvas."""
    products_services: list[ProductService] = Field(description="At least 1 product/service")
    pain_relievers: list[PainReliever] = Field(description="At least 1 pain reliever mapped to customer pains")
    gain_creators: list[GainCreator] = Field(description="At least 1 gain creator mapped to customer gains")
    ad_lib_prototypes: list[AdLibPrototype] = Field(description="At least 2 ad-lib prototype statements")


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------

def _build_messages(state: BMIWorkflowState) -> list[SystemMessage | HumanMessage]:
    customer_profile = str(state.get("customer_profile", ""))
    actionable_insights = str(state.get("actionable_insights", ""))
    if not customer_profile.strip():
        raise ValueError("Customer profile is required for Step 5")

    skill_asset = PromptAssetLoader().load_skill_asset("cxif-bmi-coach")
    selected_patterns = ", ".join(state.get("selected_patterns", [])) or "approved patterns"
    pattern_direction = str(state.get("pattern_direction", ""))

    system_prompt = (
        f"{skill_asset.body}\n\n"
        "You are the CXIF Value Proposition Design agent for the BMI consultant workflow.\n"
        "Execute the Design phase (Value Proposition Canvas) from the CXIF framework.\n\n"
        "RULES:\n"
        "- Products & Services: list the key offerings shaped by the selected patterns.\n"
        "- Pain Relievers: each MUST reference a specific customer pain from the empathy profile.\n"
        "- Gain Creators: each MUST reference a specific customer gain from the empathy profile.\n"
        "- Ad-Lib Prototypes: generate at least 2 statements in the format:\n"
        "  OUR [product/service] HELP [customer segment] WHO WANT TO [job] BY [pain relief] AND [gain creation]\n"
        "- Ground all outputs in upstream evidence. Do not fabricate.\n"
        "- Reference the selected patterns in your outputs."
    )

    user_prompt = (
        f"Pattern direction: {pattern_direction}\n"
        f"Selected patterns: {selected_patterns}\n\n"
        f"Customer Empathy Profile:\n{customer_profile}\n\n"
        f"Context Analysis & Actionable Insights:\n{actionable_insights}\n\n"
        f"Value Driver Tree:\n{state.get('value_driver_tree', '')}"
    )
    return [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]


# ---------------------------------------------------------------------------
# Markdown rendering
# ---------------------------------------------------------------------------

def _render_vpc(vpc: ValuePropositionCanvas, selected_patterns: list[str]) -> str:
    pattern_context = ", ".join(selected_patterns) or "approved patterns"
    lines = [
        "## Value Proposition Canvas",
        "",
        "### Value Map",
        "",
        "#### Products & Services",
        "| Type | Product/Service | Relevance |",
        "|------|----------------|-----------|",
    ]
    for ps in vpc.products_services:
        lines.append(f"| {ps.type} | {ps.product_service} | {ps.relevance} |")

    lines.extend([
        "",
        "#### Pain Relievers",
        "| Type | Pain Reliever | Pain Addressed | Relevance |",
        "|------|--------------|----------------|-----------|",
    ])
    for pr in vpc.pain_relievers:
        lines.append(f"| {pr.type} | {pr.pain_reliever} | {pr.pain_addressed} | {pr.relevance} |")

    lines.extend([
        "",
        "#### Gain Creators",
        "| Type | Gain Creator | Gain Addressed | Relevance |",
        "|------|-------------|----------------|-----------|",
    ])
    for gc in vpc.gain_creators:
        lines.append(f"| {gc.type} | {gc.gain_creator} | {gc.gain_addressed} | {gc.relevance} |")

    lines.extend([
        "",
        "### Ad-Lib Prototype",
    ])
    for proto in vpc.ad_lib_prototypes:
        stmt = proto.statement
        if stmt.upper().startswith("OUR "):
            stmt = stmt[4:]
        lines.append(f"> **OUR** {stmt}")

    lines.append(f"Context anchor: {pattern_context}.")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Core execution
# ---------------------------------------------------------------------------

def run_step5_llm(state: BMIWorkflowState, llm: BaseChatModel) -> BMIWorkflowState:
    """Run Step 5 CXIF Value Proposition Canvas via the LLM."""
    messages = _build_messages(state)
    structured_llm = llm.with_structured_output(ValuePropositionCanvas)
    result: ValuePropositionCanvas = structured_llm.invoke(messages)

    selected_patterns = state.get("selected_patterns", [])

    return {
        **state,
        "current_step": "value_proposition",
        "value_proposition_canvas": _render_vpc(result, selected_patterns),
    }
