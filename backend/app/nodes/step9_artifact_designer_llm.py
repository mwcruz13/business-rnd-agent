"""Step 9 — LLM-backed Artifact Designer.

For each experiment card, generate a context-specific, build-ready artifact
package instead of hardcoded checklist templates.

Falls back to the deterministic ``step9_artifact_designer.run_step`` when
the LLM is unavailable.
"""
from __future__ import annotations

from typing import Literal

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from backend.app.llm.retry import invoke_with_retry
from backend.app.nodes.step9_artifact_designer import (
    ARTIFACT_TYPES,
    DEFAULT_ARTIFACT_TYPE,
    _build_artifact_design,
)
from backend.app.state import BMIWorkflowState


# ---------------------------------------------------------------------------
# Output schema
# ---------------------------------------------------------------------------


class ArtifactDesign(BaseModel):
    card_id: str = Field(description="The experiment card ID this artifact is for.")
    card_name: str = Field(description="The experiment card name.")
    assumption: str = Field(description="The assumption being tested.")
    artifact_name: str = Field(
        description="A short, descriptive name for the artifact (e.g., 'Firmware Discovery Interview Kit v1')."
    )
    artifact_type: str = Field(
        description="The category of artifact (e.g., Interview Kit, Web Page + Analytics, Service Runbook)."
    )
    artifact_objective: str = Field(
        description=(
            "1-2 sentences describing what this artifact must achieve, tied to the "
            "specific assumption and customer context."
        )
    )
    artifact_scope: str = Field(
        description=(
            "A concise scope statement: what is included and what is explicitly excluded."
        )
    )
    deliverable_checklist: list[str] = Field(
        min_length=3,
        max_length=8,
        description=(
            "3-8 concrete deliverables the consultant must produce. Each item should "
            "be specific enough to hand to a team member as a work item."
        ),
    )
    acceptance_criteria: str = Field(
        description=(
            "How to know the artifact is 'done' — specific quality bar tied to the "
            "assumption being tested."
        )
    )


class ArtifactDesignList(BaseModel):
    artifacts: list[ArtifactDesign] = Field(
        description="One artifact design per experiment card, in the same order as input.",
    )


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------

ARTIFACT_TYPE_GUIDANCE = """
Card-to-artifact-type mapping (use as guidance, not rigid rule):
- Problem Interviews / Solution Interviews → Interview Kit
- Landing Page → Web Page + Analytics
- Fake Door → In-Product Flow
- A/B Testing → Experiment Configuration
- Throwaway Prototype → Interactive Prototype
- Usability Testing → Research Test Kit
- Wizard of Oz → Service Runbook
- Mock Sale → Sales Enablement Kit
- Pre-Order Test → Checkout Flow
- Letter of Intent → Commercial Commitment Pack
- Price Testing → Pricing Script + Survey
- Other → Document Package
"""


def _build_messages(
    state: BMIWorkflowState,
    cards: list[dict[str, object]],
) -> list[SystemMessage | HumanMessage]:
    profile = str(state.get("customer_profile", "")).strip()
    vpc = str(state.get("value_proposition_canvas", "")).strip()
    voc = str(state.get("voc_data", "")).strip()

    system_prompt = (
        "You are the Step 9 Artifact Designer for the BMI consultant workflow.\n\n"
        "Your task: for each experiment card, design a concrete, build-ready artifact "
        "package that a consultant can hand to their team and execute immediately.\n\n"
        "RULES:\n"
        "- Each artifact must be tailored to the SPECIFIC assumption, customer segment, "
        "and business context — never produce generic templates.\n"
        "- artifact_name should be descriptive and version-numbered (e.g., 'Firmware "
        "Assessment Interview Kit v1', not just 'Interview Kit').\n"
        "- artifact_objective must reference the specific assumption and what evidence "
        "the artifact will generate.\n"
        "- deliverable_checklist items must be concrete enough to be individual work items "
        "(e.g., '12-question interview script covering firmware discovery pain points, "
        "current workarounds, and willingness to adopt a self-serve tool' — not just "
        "'Interview script').\n"
        "- acceptance_criteria must tie back to the assumption — how would a reviewer "
        "know the artifact is good enough to generate trustworthy evidence?\n"
        "- For Problem Interviews: include screener criteria, question count with topic "
        "coverage, and an evidence capture mechanism.\n"
        "- For Landing Pages: include headline, value bullets, CTA, and conversion "
        "tracking requirements.\n"
        "- For Mock Sales / Pre-Orders: include pitch structure, pricing artifact, and "
        "commitment capture mechanism.\n"
        "- For Wizard of Oz: include operator script, user-facing experience, and "
        "escalation rules.\n"
        "- Output one artifact per card, in the same order as the input.\n"
        f"\n{ARTIFACT_TYPE_GUIDANCE}"
    )

    card_block = "\n\n".join(
        f"### Card {i + 1}: {card.get('card_name', 'Unknown')}\n"
        f"- **Card ID:** {card.get('id', 'N/A')}\n"
        f"- **Assumption:** {card.get('assumption', 'N/A')}\n"
        f"- **Asset Needed (hint):** {card.get('asset_needed', 'N/A')}\n"
        f"- **Asset Spec (hint):** {card.get('asset_spec', 'N/A')}\n"
        f"- **Success Criteria:** {card.get('success_criteria', 'N/A')}\n"
        f"- **Failure Criteria:** {card.get('failure_criteria', 'N/A')}"
        for i, card in enumerate(cards)
    )

    user_prompt = (
        f"## Experiment cards to design artifacts for\n\n{card_block}\n\n"
        f"## Customer Profile\n{profile[:4000] if profile else '(empty)'}\n\n"
        f"## Value Proposition Canvas\n{vpc[:4000] if vpc else '(empty)'}\n\n"
        f"## VoC Context (first 4000 chars)\n{voc[:4000] if voc else '(empty)'}"
    )

    return [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]


# ---------------------------------------------------------------------------
# Fallback
# ---------------------------------------------------------------------------


def _fallback_designs(cards: list[dict[str, object]]) -> list[dict[str, object]]:
    """Use the deterministic builder as fallback."""
    return [_build_artifact_design(card) for card in cards]


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def run_step9_llm(
    state: BMIWorkflowState,
    llm: BaseChatModel | None,
) -> BMIWorkflowState:
    """Run the artifact designer. Returns updated state with artifact_designs."""
    cards = state.get("experiment_cards") or []

    if not cards:
        return {
            **state,
            "current_step": "pdsa_plan",
            "artifact_designs": [],
        }

    if llm is None:
        return {
            **state,
            "current_step": "pdsa_plan",
            "artifact_designs": _fallback_designs(cards),
        }

    messages = _build_messages(state, cards)
    structured_llm = llm.with_structured_output(ArtifactDesignList)
    try:
        result: ArtifactDesignList = invoke_with_retry(
            structured_llm, messages, step_name="step9_artifact_designer"
        )
        # Align output order with input cards, filling gaps with fallback
        by_card_id = {a.card_id: a for a in result.artifacts}
        designs: list[dict[str, object]] = []
        for card in cards:
            card_id = card.get("id", "")
            match = by_card_id.get(card_id)
            if match is not None:
                designs.append(match.model_dump())
            else:
                designs.append(_build_artifact_design(card))
    except RuntimeError:
        designs = _fallback_designs(cards)

    return {
        **state,
        "current_step": "pdsa_plan",
        "artifact_designs": designs,
    }
