from __future__ import annotations

from dataclasses import dataclass

from backend.app.patterns.loader import PatternLibraryLoader
from backend.app.skills.loader import PromptAssetLoader
from backend.app.state import BMIWorkflowState


@dataclass(frozen=True)
class ExperimentCard:
    name: str
    category: str
    evidence_strength: str
    what_it_tests: str
    best_used_when: str
    usually_runs_after: list[str]
    usually_runs_next: list[str]


@dataclass(frozen=True)
class TopAssumption:
    assumption: str
    category: str
    quadrant: str


EVIDENCE_ORDER = {"Weak": 1, "Medium": 2, "Strong": 3}
PRECOIL_EVIDENCE_LABEL = {"Weak": "light", "Medium": "medium", "Strong": "strong"}
PRIMARY_METRICS = {
    "Desirability": "Qualified customer signals that the problem is painful enough to act on now",
    "Feasibility": "Successful completion of the critical workflow without manual recovery",
    "Viability": "Observed willingness to commit commercial intent before full delivery",
}
SECONDARY_METRICS = {
    "Desirability": "Response quality, follow-up interest, and objection themes",
    "Feasibility": "Time to complete, intervention count, and delivery friction",
    "Viability": "Pricing objections, stakeholder alignment, and next-step commitment",
}
PATH_BY_CATEGORY = {
    "Desirability": ["Problem Interviews", "Landing Page", "Fake Door"],
    "Feasibility": ["Expert Interviews", "Throwaway Prototype", "Wizard of Oz"],
    "Viability": ["Competitor Analysis", "Mock Sale", "Pre-Order Test"],
}

# Expanded matrix — supports evidence-aware selection in future releases.
# Keys: DVF category → evidence level → list of candidate experiment names.
# Default selection (current behavior) uses the "Weak" tier via PATH_BY_CATEGORY.
EXPERIMENT_MATRIX = {
    "Desirability": {
        "Weak": ["Problem Interviews", "Solution Interviews", "Surveys / Questionnaires"],
        "Medium": ["Landing Page", "Fake Door", "A/B Testing"],
        "Strong": [],  # Escalate to Feasibility/Viability
    },
    "Feasibility": {
        "Weak": ["Expert Interviews", "Paper Prototype", "Wireframe Prototype"],
        "Medium": ["Throwaway Prototype", "Usability Testing", "3D Prototype"],
        "Strong": ["Concierge Test", "Wizard of Oz", "Single-Feature MVP"],
    },
    "Viability": {
        "Weak": ["Competitor Analysis", "Analogous Markets"],
        "Medium": ["Mock Sale", "Letter of Intent", "Price Testing"],
        "Strong": ["Pre-Order Test", "Crowdfunding", "Paid Pilot"],
    },
}


def _load_assets() -> tuple[dict[str, ExperimentCard], dict[str, object]]:
    pattern_loader = PatternLibraryLoader()
    library = pattern_loader.load_library("experiment-library.json").data
    precoil_library = pattern_loader.load_library("precoil-emt-pattern-library.json").data
    prompt_loader = PromptAssetLoader()
    prompt_loader.load_skill_asset("testing-business-ideas")
    prompt_loader.load_skill_asset("precoil-emt")

    if int(library["metadata"].get("card_count", 0)) != 44:
        raise ValueError("Unexpected experiment card count")

    cards = {
        item["name"]: ExperimentCard(
            name=item["name"],
            category=item["category"],
            evidence_strength=item["evidence_strength"],
            what_it_tests=item["what_it_tests"],
            best_used_when=item["best_used_when"],
            usually_runs_after=item["usually_runs_after"],
            usually_runs_next=item["usually_runs_next"],
        )
        for item in library["experiments"]
    }
    return cards, precoil_library


def _extract_top_assumptions(assumptions: str) -> list[TopAssumption]:
    if "## Importance × Evidence Map" not in assumptions:
        return []

    matrix_lines = assumptions.split("## Importance × Evidence Map", 1)[1].splitlines()
    rows: list[TopAssumption] = []
    for line in matrix_lines:
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.split("|")[1:-1]]
        if len(cells) != 3:
            continue
        assumption, category, quadrant = cells
        if assumption == "Assumption" or assumption.startswith("------------"):
            continue
        if quadrant == "Test first":
            rows.append(TopAssumption(assumption=assumption, category=category, quadrant=quadrant))
    return rows


def _get_category_path(category: str, cards: dict[str, ExperimentCard]) -> list[ExperimentCard]:
    path_names = PATH_BY_CATEGORY.get(category)
    if not path_names:
        raise ValueError(f"Unexpected assumption category: {category}")

    path = [cards[name] for name in path_names]
    for index, card in enumerate(path):
        if card.category != category:
            raise ValueError(f"Experiment {card.name} does not match category {category}")
        if index == 0:
            continue
        previous = path[index - 1]
        if card.name not in previous.usually_runs_next and previous.name not in card.usually_runs_after:
            raise ValueError(f"Experiment path for {category} is not logically sequenced")
        if EVIDENCE_ORDER[card.evidence_strength] < EVIDENCE_ORDER[previous.evidence_strength]:
            raise ValueError(f"Experiment path for {category} violates evidence ordering")
    return path


def _format_selection(assumption: TopAssumption, path: list[ExperimentCard]) -> str:
    lines = [
        "## Experiment Selection",
        "",
        "### Assumption",
        assumption.assumption,
        "",
        f"**Category:** {assumption.category}",
        "**Current evidence level:** None",
        "",
        "### Recommended Experiments",
        "",
        "| Priority | Experiment Card | Evidence Strength | Why This Fits | What It Reduces |",
        "|----------|----------------|-------------------|---------------|-----------------|",
    ]
    for priority, card in enumerate(path, start=1):
        why_this_fits = f"{card.best_used_when}; it is the right {card.evidence_strength.lower()}-evidence move for this {assumption.category.lower()} risk."
        what_it_reduces = f"It reduces uncertainty about whether {card.what_it_tests.lower()}."
        lines.append(
            f"| {priority} | {card.name} | {card.evidence_strength} | {why_this_fits} | {what_it_reduces} |"
        )
    lines.extend(
        [
            "",
            "### Selection rationale",
            f"This sequence starts with {path[0].name} because the assumption currently has no direct evidence and needs the cheapest credible signal first. The path then escalates through {path[1].name} and {path[2].name} only if the earlier signals justify stronger investment.",
        ]
    )
    return "\n".join(lines)


def _format_precoil_brief(assumption: TopAssumption, primary_card: ExperimentCard) -> str:
    return "\n".join(
        [
            "## Experiment Brief",
            "",
            "### Assumption to Test",
            assumption.assumption,
            "",
            f"**Category:** {assumption.category}",
            "",
            "### What You're Trying to Learn",
            f"This experiment tests whether the team should increase confidence in the assumption that {assumption.assumption[10:].lower() if assumption.assumption.startswith('I believe ') else assumption.assumption.lower()}",
            "",
            "### Experiment Type",
            primary_card.name,
            "",
            "### How to Run It",
            f"1. Prepare the audience, script, and artifact needed for {primary_card.name.lower()}.",
            f"2. Run the experiment with the target stakeholders most affected by this {assumption.category.lower()} risk.",
            "3. Review the signals against explicit success and failure thresholds before deciding whether to escalate.",
            "",
            "### How to Measure It",
            f"- Metric: {PRIMARY_METRICS[assumption.category]}",
            "- Success looks like: At least 70% of the target signal indicates the assumption is directionally correct and worth testing at a stronger evidence level.",
            "- Failure looks like: Fewer than 40% of the target signal supports the assumption or the objections show the risk is materially different than expected.",
            "",
            "### Estimated Effort",
            "- Setup: short",
            "- Run time: short",
            f"- Evidence strength: {PRECOIL_EVIDENCE_LABEL[primary_card.evidence_strength]}",
            "",
            "### Remaining Uncertainty",
            f"This experiment will not fully resolve whether later-stage evidence from {', '.join(card.name for card in [primary_card][1:])} is needed to confirm the assumption under real operating conditions.",
        ]
    )


def _format_implementation_plan(assumption: TopAssumption, primary_card: ExperimentCard) -> str:
    return "\n".join(
        [
            "## Experiment Implementation Plan",
            "",
            "### Experiment Overview",
            f"- **Experiment card:** {primary_card.name}",
            f"- **Category:** {primary_card.category}",
            f"- **Evidence strength:** {primary_card.evidence_strength}",
            "",
            "### Assumption to Test",
            assumption.assumption,
            "",
            "### Goal",
            primary_card.what_it_tests,
            "",
            "### Best For",
            primary_card.best_used_when,
            "",
            "### Implementation Steps",
            f"1. Prepare the interview guide, landing asset, or prototype needed for {primary_card.name.lower()}.",
            f"2. Run {primary_card.name.lower()} with the defined audience segment tied to this assumption.",
            "3. Capture the primary and secondary metrics as the experiment runs.",
            "4. Compare results against the decision thresholds and choose whether to escalate to the next evidence level.",
            "",
            "### What to Measure",
            f"- **Primary metric:** {PRIMARY_METRICS[assumption.category]}",
            f"- **Secondary metrics:** {SECONDARY_METRICS[assumption.category]}",
            "",
            "### Success and Failure Criteria",
            "- **Success looks like:** A clear signal strong enough to justify the next recommended experiment.",
            "- **Failure looks like:** A clear signal that materially lowers confidence in the assumption.",
            "- **Ambiguous result looks like:** Mixed evidence that requires reframing or rerunning a weak or medium test before escalation.",
            "",
            "### Estimated Effort",
            "| Element | Estimate |",
            "|---------|----------|",
            "| Setup | Short |",
            "| Run time | Short |",
            "| Cost | Low |",
            "",
            "### Common Pitfall",
            f"Using {primary_card.name.lower()} without explicit decision thresholds turns the result into narrative evidence instead of decision-grade evidence.",
            "",
            "### What This Experiment Will Not Resolve",
            f"It will not replace the need for {assumption.category.lower()} evidence from stronger follow-on tests.",
        ]
    )


def _format_evidence_sequence(assumption: TopAssumption, path: list[ExperimentCard]) -> str:
    move_signals = {
        "Desirability": [
            "Interview evidence shows the problem is frequent, painful, and worth immediate attention.",
            "Prospects convert on the landing page at a level that justifies testing feature-level behavior.",
            "Feature-level interest remains strong enough to move into a live product or operating test.",
        ],
        "Feasibility": [
            "Expert feedback shows the constraint is solvable without major blockers.",
            "The simulated workflow proves the core capability can be delivered with manageable effort.",
            "Users value the output enough to justify building the smallest production capability.",
        ],
        "Viability": [
            "Competitive evidence shows there is room for a differentiated commercial approach.",
            "Prospects express concrete purchase intent rather than abstract interest.",
            "Customers commit enough money or resources to justify a paid market test.",
        ],
    }

    lines = [
        "## Evidence Sequence",
        "",
        "### Assumption",
        assumption.assumption,
        "",
        f"**Category:** {assumption.category}",
        "",
        "### Sequence",
        "",
        "| Step | Experiment Card | Evidence Strength | Move to Next When |",
        "|------|----------------|-------------------|-------------------|",
    ]
    for index, card in enumerate(path, start=1):
        lines.append(
            f"| {index} | {card.name} | {card.evidence_strength} | {move_signals[assumption.category][index - 1]} |"
        )
    lines.extend(
        [
            "",
            "### If signals are weak or mixed at any step",
            "Reframe the assumption, tighten the success criteria, or rerun the cheapest credible test before escalating to a stronger one.",
        ]
    )
    return "\n".join(lines)


def _format_worksheet(assumption: TopAssumption, primary_card: ExperimentCard, next_card: ExperimentCard | None) -> str:
    next_if_mixed = next_card.name if next_card else "Refine the same experiment"
    next_if_positive = next_card.name if next_card else "Summarize the evidence and decide whether to stop"
    return "\n".join(
        [
            "## Experiment Worksheet",
            "",
            "### Experiment Overview",
            f"- **Experiment card:** {primary_card.name}",
            f"- **Category:** {primary_card.category}",
            f"- **Evidence strength target:** {primary_card.evidence_strength}",
            "- **Date:** TBD",
            "- **Owner:** TBD",
            "- **Status:** Planned",
            "",
            "### Assumption To Test",
            f"- **Assumption statement:** {assumption.assumption}",
            "- **Why this assumption matters:** It is currently in the Test first quadrant and blocks confidence in the business model.",
            "- **What would break if it is wrong:** The proposed direction would need redesign before larger investment.",
            "- **Customer segment or stakeholder:** Operational buyers, onboarding stakeholders, and internal delivery teams tied to the risk.",
            "",
            "### Learning Objective",
            f"- **What we are trying to learn:** Whether {primary_card.what_it_tests.lower()} in a way that materially increases confidence in this assumption.",
            f"- **Why this experiment is the right test now:** {primary_card.best_used_when}.",
            "- **What evidence already exists:** None",
            "",
            "### Experiment Design",
            f"- **Experiment type:** {primary_card.name}",
            "- **Test audience:** The stakeholders closest to the risk described in the assumption.",
            "- **Sample size target:** 8 qualified participants or decision points",
            "- **Channel or environment:** The lowest-cost environment that still produces credible evidence.",
            f"- **Asset needed:** A runnable artifact tailored for {primary_card.name.lower()}.",
            "- **Timebox:** 1 week",
            "",
            "### Success And Failure Criteria",
            f"- **Primary metric:** {PRIMARY_METRICS[assumption.category]}",
            f"- **Secondary metrics:** {SECONDARY_METRICS[assumption.category]}",
            "- **Success looks like:** The result clearly strengthens confidence and justifies moving to the next experiment.",
            "- **Failure looks like:** The result clearly lowers confidence or exposes a more important risk.",
            "- **Ambiguous result looks like:** The signal is mixed and leaves the assumption unresolved.",
            "",
            "### Execution Plan",
            "1. **Prepare:** Finalize the artifact, audience list, and threshold definitions.",
            f"2. **Launch or run:** Execute {primary_card.name.lower()} with the selected audience.",
            "3. **Capture observations:** Record what people said, what they did, and where friction appeared.",
            "4. **Analyze:** Compare the captured evidence with the success and failure thresholds.",
            "5. **Decide next step:** Escalate, refine, rerun, or stop based on the evidence quality.",
            "",
            "### Sequencing",
            f"- **Usually runs after:** {', '.join(primary_card.usually_runs_after) if primary_card.usually_runs_after else 'None'}",
            f"- **If signal is positive, move next to:** {next_if_positive}",
            f"- **If signal is weak or mixed, move next to:** {next_if_mixed}",
            "",
            "### Evidence Captured",
            "- What customers said: To be filled after experiment",
            "- What customers did: To be filled after experiment",
            "- What surprised us: To be filled after experiment",
            "- What changed in our confidence: To be filled after experiment",
            "",
            "### Decision",
            "- Outcome: To be filled after experiment",
            "- Decision: To be filled after experiment",
            "- Next experiment: To be filled after experiment",
            "- Owner and due date: To be filled after experiment",
        ]
    )


def _build_card_object(
    assumption: TopAssumption,
    primary_card: ExperimentCard,
    path: list[ExperimentCard],
    card_index: int,
) -> dict[str, object]:
    next_card = path[1] if len(path) > 1 else None
    return {
        "id": f"exp-{card_index:03d}",
        "assumption": assumption.assumption,
        "category": assumption.category,
        "evidence_strength": primary_card.evidence_strength,
        "card_name": primary_card.name,
        "what_it_tests": primary_card.what_it_tests,
        "best_used_when": primary_card.best_used_when,
        "test_audience": "The stakeholders closest to the risk described in the assumption.",
        "sample_size": 8,
        "timebox": "1 week",
        "primary_metric": PRIMARY_METRICS[assumption.category],
        "secondary_metrics": SECONDARY_METRICS[assumption.category],
        "success_looks_like": "The result clearly strengthens confidence and justifies moving to the next experiment.",
        "failure_looks_like": "The result clearly lowers confidence or exposes a more important risk.",
        "ambiguous_looks_like": "The signal is mixed and leaves the assumption unresolved.",
        "sequencing": {
            "usually_runs_after": list(primary_card.usually_runs_after),
            "next_if_positive": next_card.name if next_card else None,
            "next_if_mixed": next_card.name if next_card else None,
        },
        "selection_rationale": (
            f"This sequence starts with {primary_card.name} because the assumption currently "
            f"has no direct evidence and needs the cheapest credible signal first."
        ),
        "evidence_path": [
            {
                "step": idx + 1,
                "card_name": c.name,
                "evidence_strength": c.evidence_strength,
            }
            for idx, c in enumerate(path)
        ],
        "status": "planned",
        "owner": None,
        "date_started": None,
        "date_completed": None,
        "evidence": {
            "what_customers_said": None,
            "what_customers_did": None,
            "what_surprised_us": None,
            "confidence_change": None,
            "decision": None,
            "next_experiment": None,
            "notes": None,
        },
    }


VALID_CARD_STATUSES = {"planned", "running", "evidence_captured", "decision_made"}
VALID_CONFIDENCE_VALUES = {"increased", "decreased", "unchanged"}
VALID_DECISION_VALUES = {"continue", "refine", "stop"}

UPDATABLE_EVIDENCE_FIELDS = {
    "status", "owner", "date_started", "date_completed",
    "evidence",
}


def update_experiment_card_evidence(
    card: dict[str, object],
    updates: dict[str, object],
) -> dict[str, object]:
    """Apply only Zone B (evidence) updates to an experiment card dict.

    Returns a new dict with the updates merged. Raises ValueError for
    invalid field names or values.
    """
    disallowed = set(updates.keys()) - UPDATABLE_EVIDENCE_FIELDS
    if disallowed:
        raise ValueError(f"Cannot update Zone A fields: {', '.join(sorted(disallowed))}")

    result = dict(card)

    if "status" in updates:
        if updates["status"] not in VALID_CARD_STATUSES:
            raise ValueError(
                f"Invalid status '{updates['status']}'. "
                f"Allowed: {', '.join(sorted(VALID_CARD_STATUSES))}"
            )
        result["status"] = updates["status"]

    for field in ("owner", "date_started", "date_completed"):
        if field in updates:
            result[field] = updates[field]

    if "evidence" in updates:
        merged_evidence = dict(result.get("evidence") or {})
        incoming = updates["evidence"]
        if not isinstance(incoming, dict):
            raise ValueError("evidence must be a dict")
        for key, value in incoming.items():
            if key not in {
                "what_customers_said", "what_customers_did",
                "what_surprised_us", "confidence_change",
                "decision", "next_experiment", "notes",
            }:
                raise ValueError(f"Unknown evidence field: {key}")
            if key == "confidence_change" and value is not None:
                if value not in VALID_CONFIDENCE_VALUES:
                    raise ValueError(
                        f"Invalid confidence_change '{value}'. "
                        f"Allowed: {', '.join(sorted(VALID_CONFIDENCE_VALUES))}"
                    )
            if key == "decision" and value is not None:
                if value not in VALID_DECISION_VALUES:
                    raise ValueError(
                        f"Invalid decision '{value}'. "
                        f"Allowed: {', '.join(sorted(VALID_DECISION_VALUES))}"
                    )
            merged_evidence[key] = value
        result["evidence"] = merged_evidence

    return result


def _build_outputs(state: BMIWorkflowState) -> tuple[str, str, str, list[dict[str, object]]]:
    cards, precoil_library = _load_assets()
    if "step_8_behavior" not in precoil_library.get("agent_usage_guidance", {}):
        raise ValueError("Unexpected Precoil step 8 guidance")

    top_assumptions = _extract_top_assumptions(state.get("assumptions", ""))
    selections: list[str] = []
    plans: list[str] = []
    worksheets: list[str] = []
    card_objects: list[dict[str, object]] = []

    for assumption in top_assumptions:
        path = _get_category_path(assumption.category, cards)
        selections.append(_format_selection(assumption, path))
        plans.append(_format_precoil_brief(assumption, path[0]))
        plans.append(_format_implementation_plan(assumption, path[0]))
        plans.append(_format_evidence_sequence(assumption, path))
        worksheets.append(_format_worksheet(assumption, path[0], path[1] if len(path) > 1 else None))
        card_objects.append(_build_card_object(assumption, path[0], path, len(card_objects) + 1))

    return "\n\n".join(selections), "\n\n".join(plans), "\n\n".join(worksheets), card_objects


def run_step(state: BMIWorkflowState) -> BMIWorkflowState:
    experiment_selections, experiment_plans, experiment_worksheets, experiment_cards = _build_outputs(state)
    return {
        **state,
        "current_step": "pdsa_plan",
        "experiment_selections": experiment_selections,
        "experiment_plans": experiment_plans,
        "experiment_worksheets": experiment_worksheets,
        "experiment_cards": experiment_cards,
    }
