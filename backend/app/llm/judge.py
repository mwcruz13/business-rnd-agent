"""LLM-as-Judge module for evaluating SOC Radar Step 1 output quality.

Evaluates the analytical quality of a signal scan against the SOC Radar
SKILL instructions.  Uses gpt-4o (the same chat deployment) with a
structured-output rubric so scores are deterministic to parse.

The judge receives three inputs:
  1. Original VoC text (what the agent was given)
  2. SOC Radar SKILL.md body (the instructions it should have followed)
  3. Step 1 structured output (signals, interpretations, priorities)

It returns a JudgeVerdict with four dimension scores (1-5) and rationales.
"""
from __future__ import annotations

import json
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from backend.app.skills.loader import PromptAssetLoader


# ---------------------------------------------------------------------------
# Structured output schema for the judge verdict
# ---------------------------------------------------------------------------

class DimensionScore(BaseModel):
    """Score and rationale for a single evaluation dimension."""
    score: int = Field(ge=1, le=5, description="Score from 1 (poor) to 5 (excellent)")
    rationale: str = Field(description="Brief explanation justifying the score")


class JudgeVerdict(BaseModel):
    """Complete verdict from the LLM-as-Judge evaluation."""
    completeness: DimensionScore = Field(
        description="Does the scan cover the key themes present in the source text?"
    )
    relevance: DimensionScore = Field(
        description="Is every signal grounded in the source text with no hallucinations?"
    )
    groundedness: DimensionScore = Field(
        description="Does each signal reference observable behavior, not speculation?"
    )
    skill_compliance: DimensionScore = Field(
        description="Did the output follow SOC Radar phases: Scan, Interpret, Prioritize?"
    )


# ---------------------------------------------------------------------------
# Few-shot rubric anchors to reduce scoring subjectivity
# ---------------------------------------------------------------------------

_RUBRIC = """
## Scoring Rubric

For each dimension, assign a score from 1 to 5 using these anchors:

### Completeness
- 5: Every major theme in the source text is captured as a signal. No obvious gaps.
- 4: Most themes captured; one minor theme missing.
- 3: Core themes present but two or more secondary themes omitted.
- 2: Only the most obvious theme captured; significant gaps.
- 1: The scan misses the central themes of the source text entirely.

### Relevance
- 5: Every signal is directly traceable to specific content in the source text.
- 4: All but one signal are traceable; one is weakly connected.
- 3: Most signals are traceable but one or two appear speculative.
- 2: Multiple signals have no clear basis in the source text.
- 1: Most signals are hallucinated or unrelated to the input.

### Groundedness
- 5: Every signal describes observable behavior with direct evidence excerpts.
- 4: Most signals cite observable behavior; one relies on inference.
- 3: Some signals describe observable behavior; others are analyst opinion.
- 2: Most signals are analyst speculation rather than observed behavior.
- 1: Signals are entirely opinion-based with no observable evidence.

### SKILL Compliance
- 5: Output clearly follows all three SOC Radar phases (Scan, Interpret, Prioritize) with correct structure — zones, disruption filters, impact/speed scoring, and tier assignment.
- 4: All three phases present with minor structural issues (e.g., one filter missing).
- 3: Phases are present but with noticeable gaps (e.g., missing confidence levels or alternative explanations).
- 2: One phase is missing or severely incomplete.
- 1: Output does not follow the SOC Radar SKILL structure.
""".strip()


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------

def _build_judge_messages(
    voc_text: str,
    skill_body: str,
    step1_output: dict[str, Any],
) -> list[SystemMessage | HumanMessage]:
    """Build the system + user messages for the judge evaluation."""

    system_prompt = (
        "You are an expert evaluator assessing the quality of a SOC Radar signal scan.\n"
        "You will receive:\n"
        "1. The SOC Radar SKILL instructions that the agent was supposed to follow.\n"
        "2. The original Voice of Customer (VoC) source text.\n"
        "3. The structured output produced by the agent.\n\n"
        "Your job is to evaluate the output on four dimensions: "
        "completeness, relevance, groundedness, and SKILL compliance.\n"
        "Be rigorous but fair. Use the rubric anchors to calibrate your scores.\n"
        "Do NOT give perfect scores unless the output truly deserves them.\n\n"
        f"{_RUBRIC}\n\n"
        "--- SOC RADAR SKILL INSTRUCTIONS ---\n"
        f"{skill_body}"
    )

    # Serialize the step1 output compactly
    output_json = json.dumps(step1_output, indent=2, default=str)

    user_prompt = (
        "--- ORIGINAL VOC SOURCE TEXT ---\n"
        f"{voc_text}\n\n"
        "--- AGENT OUTPUT TO EVALUATE ---\n"
        f"{output_json}\n\n"
        "Evaluate the agent output against the four dimensions. "
        "Return your verdict with a score (1-5) and rationale for each dimension."
    )

    return [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]


# ---------------------------------------------------------------------------
# Core evaluation function
# ---------------------------------------------------------------------------

def evaluate_step1_quality(
    voc_text: str,
    step1_output: dict[str, Any],
    llm: BaseChatModel,
) -> JudgeVerdict:
    """Evaluate the quality of Step 1 signal scan output using LLM-as-Judge.

    Args:
        voc_text: The original VoC source text that was analyzed.
        step1_output: The Step 1 structured output dict containing signals,
            interpreted_signals, priority_matrix, etc.
        llm: A chat model instance (typically gpt-4o) to use as the judge.

    Returns:
        A JudgeVerdict with scores and rationales for each dimension.
    """
    skill_asset = PromptAssetLoader().load_skill_asset("soc-radar")
    messages = _build_judge_messages(voc_text, skill_asset.body, step1_output)

    structured_llm = llm.with_structured_output(JudgeVerdict)
    verdict: JudgeVerdict = structured_llm.invoke(messages)
    return verdict
