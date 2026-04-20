"""Step 6 LLM-backed CXIF Business Model Canvas and Fit Assessment.

Uses the cxif-bmi-coach SKILL to generate a Business Model Canvas
(Desirability, Feasibility, Viability) and a three-layer Fit Assessment
(Problem-Solution, Product-Market, Business Model) from the upstream
Value Proposition Canvas.
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

class BMCBuildingBlock(BaseModel):
    building_block: str = Field(description="E.g. Customer Segments, Value Proposition, Channels, etc.")
    description: str


class ProblemSolutionFitRow(BaseModel):
    customer_need: str = Field(description="A job, pain, or gain from the empathy profile")
    importance: str = Field(description="High, Medium, or Low")
    mapped_element: str = Field(description="Value proposition element that addresses this need")
    fit: str = Field(description="Strong, Partial, or Weak")


class FitStatusRow(BaseModel):
    criterion: str
    status: str = Field(description="Validated, Assumed, or Unknown")
    evidence: str


class BusinessModelFitRow(BaseModel):
    dimension: str = Field(description="Desirable, Feasible, or Viable")
    status: str = Field(description="Validated, Assumed, or Unknown")
    evidence: str


class Step6Output(BaseModel):
    """Complete Step 6 output: BMC + Fit Assessment."""
    desirability_blocks: list[BMCBuildingBlock] = Field(
        description="Customer Segments, Value Proposition, Channels, Customer Relationships"
    )
    feasibility_blocks: list[BMCBuildingBlock] = Field(
        description="Key Partnerships, Key Activities, Key Resources"
    )
    viability_blocks: list[BMCBuildingBlock] = Field(
        description="Revenue Streams, Cost Structure"
    )
    problem_solution_fit: list[ProblemSolutionFitRow] = Field(description="At least 1 row")
    product_market_fit: list[FitStatusRow] = Field(description="At least 2 criteria")
    business_model_fit: list[BusinessModelFitRow] = Field(description="At least 2 dimensions")


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------

def _build_messages(state: BMIWorkflowState) -> list[SystemMessage | HumanMessage]:
    vpc = str(state.get("value_proposition_canvas", ""))
    if not vpc.strip():
        raise ValueError("Value Proposition Canvas is required for Step 6")

    skill_asset = PromptAssetLoader().load_step_prompt("step6_business_model")
    selected_patterns = ", ".join(state.get("selected_patterns", [])) or "approved patterns"
    pattern_direction = str(state.get("pattern_direction", ""))

    system_prompt = (
        f"{skill_asset.body}\n\n"
        "You are the CXIF Business Model Design agent for the BMI consultant workflow.\n"
        "You are designing a business model FROM THE SUPPLIER'S PERSPECTIVE.\n"
        "Feasibility blocks (Key Partnerships, Key Activities, Key Resources) describe the SUPPLIER'S\n"
        "operational capabilities needed to deliver the value proposition.\n"
        "Viability blocks (Revenue Streams, Cost Structure) describe the SUPPLIER'S financial model.\n"
        "Desirability blocks describe how the SUPPLIER reaches and serves the customer.\n\n"
        "Execute the Design phase (Business Model Canvas + Fit Assessment) from the CXIF framework.\n\n"
        "BUSINESS MODEL CANVAS:\n"
        "- Desirability: Customer Segments, Value Proposition, Channels, Customer Relationships.\n"
        "- Feasibility: Key Partnerships, Key Activities, Key Resources.\n"
        "- Viability: Revenue Streams, Cost Structure.\n"
        "- Reference the selected patterns in the Value Proposition block.\n\n"
        "FIT ASSESSMENT:\n"
        "- Problem-Solution Fit: map customer needs to value proposition elements.\n"
        "- Product-Market Fit Status: assess criteria with status (Assumed/Demonstrated/Unknown) and evidence.\n"
        "- Business Model Fit Status: assess Desirable/Feasible/Viable dimensions.\n\n"
        "RULES:\n"
        "- Ground all outputs in the upstream Value Proposition Canvas and empathy profile.\n"
        "- Be honest about what is Assumed vs Validated vs Unknown.\n"
        "- Do not fabricate evidence."
    )

    voc_data = str(state.get('voc_data', ''))[:2000]

    user_prompt = (
        f"Pattern direction: {pattern_direction}\n"
        f"Selected patterns: {selected_patterns}\n\n"
        f"Value Proposition Canvas:\n{vpc}\n\n"
        f"Customer Profile:\n{state.get('customer_profile', '')}\n\n"
        f"Actionable Insights:\n{state.get('actionable_insights', '')}\n\n"
        f"Original Voice of Customer evidence (reference for grounding):\n{voc_data}"
    )
    return [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]


# ---------------------------------------------------------------------------
# Markdown rendering
# ---------------------------------------------------------------------------

def _render_bmc(output: Step6Output, selected_patterns: list[str]) -> str:
    pattern_context = ", ".join(selected_patterns) or "approved patterns"
    lines = [
        "## Business Model Canvas",
        "",
        "### Desirability",
        "| Building Block | Description |",
        "|---------------|-------------|",
    ]
    for block in output.desirability_blocks:
        desc = block.description
        if block.building_block == "Value Proposition" and pattern_context not in desc:
            desc = f"{desc} Pattern context: {pattern_context}."
        lines.append(f"| {block.building_block} | {desc} |")

    lines.extend([
        "",
        "### Feasibility",
        "| Building Block | Description |",
        "|---------------|-------------|",
    ])
    for block in output.feasibility_blocks:
        lines.append(f"| {block.building_block} | {block.description} |")

    lines.extend([
        "",
        "### Viability",
        "| Building Block | Description |",
        "|---------------|-------------|",
    ])
    for block in output.viability_blocks:
        lines.append(f"| {block.building_block} | {block.description} |")

    return "\n".join(lines)


def _render_fit(output: Step6Output) -> str:
    lines = [
        "## Fit Assessment",
        "",
        "### Problem-Solution Fit",
        "| Customer Need (Job/Pain/Gain) | Importance to Customer | Mapped Value Proposition Element | Fit? |",
        "|------------------------------|----------------------|--------------------------------|------|",
    ]
    for row in output.problem_solution_fit:
        lines.append(f"| {row.customer_need} | {row.importance} | {row.mapped_element} | {row.fit} |")

    lines.extend([
        "",
        "### Product-Market Fit Status",
        "| Criterion | Status | Evidence |",
        "|-----------|--------|----------|",
    ])
    for row in output.product_market_fit:
        lines.append(f"| {row.criterion} | {row.status} | {row.evidence} |")

    lines.extend([
        "",
        "### Business Model Fit Status",
        "| Dimension | Status | Evidence |",
        "|-----------|--------|----------|",
    ])
    for row in output.business_model_fit:
        lines.append(f"| {row.dimension} | {row.status} | {row.evidence} |")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Core execution
# ---------------------------------------------------------------------------

def run_step6_llm(state: BMIWorkflowState, llm: BaseChatModel) -> BMIWorkflowState:
    """Run Step 6 CXIF Business Model Canvas + Fit Assessment via the LLM."""
    messages = _build_messages(state)
    structured_llm = llm.with_structured_output(Step6Output)
    result: Step6Output = structured_llm.invoke(messages)

    selected_patterns = state.get("selected_patterns", [])

    return {
        **state,
        "current_step": "design_fit",
        "business_model_canvas": _render_bmc(result, selected_patterns),
        "fit_assessment": _render_fit(result),
    }
