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
        "Weak": [
            "Problem Interviews", "Solution Interviews", "Surveys / Questionnaires",
            "Desk Research", "Search Trends", "Keyword Research",
            "Journey Mapping", "Focus Groups", "Forced Ranking",
            "Card Sorting", "Storyboard", "Explainer Video", "Ad Campaign",
        ],
        "Medium": [
            "Landing Page", "Fake Door", "A/B Testing",
            "Customer Observation", "Ethnographic Field Study",
            "Contextual Inquiry", "Diary Study",
        ],
        "Strong": [],  # No Strong-evidence Desirability cards in the library
    },
    "Feasibility": {
        "Weak": ["Expert Interviews", "Paper Prototype", "Wireframe Prototype", "Patent Search"],
        "Medium": ["Throwaway Prototype", "Usability Testing", "3D Prototype"],
        "Strong": [
            "Concierge Test", "Wizard of Oz", "Single-Feature MVP",
            "Piecemeal MVP", "Minimum Viable Product",
        ],
    },
    "Viability": {
        "Weak": ["Competitor Analysis", "Analogous Markets"],
        "Medium": [
            "Mock Sale", "Letter of Intent", "Price Testing",
            "Revenue Model Test", "Channel Test",
        ],
        "Strong": [
            "Pre-Order Test", "Crowdfunding", "Paid Pilot",
            "Presales", "Cohort / Retention Analysis",
        ],
    },
}

ASSET_BLUEPRINTS = {
    "Problem Interviews": {
        "artifact_name": "Interview Guide v1 + Screener",
        "artifact_spec": "10-question interview script, participant screener form, and evidence capture template.",
        "acceptance_criteria": "Guide covers trigger, impact, alternatives, urgency, and decision moments with no leading prompts.",
    },
    "Landing Page": {
        "artifact_name": "Single-Offer Landing Page",
        "artifact_spec": "One-page value proposition page with one CTA, analytics tags, and conversion event instrumentation.",
        "acceptance_criteria": "Visitors can understand the offer in under 30 seconds and CTA conversion can be measured end to end.",
    },
    "Fake Door": {
        "artifact_name": "In-Product Fake Door Flow",
        "artifact_spec": "Clickable feature entry point, confirmation screen, and follow-up capture for intent rationale.",
        "acceptance_criteria": "Clickthrough and post-click intent reasons are recorded with user segment context.",
    },
    "Throwaway Prototype": {
        "artifact_name": "Workflow Throwaway Prototype",
        "artifact_spec": "Clickable prototype of critical onboarding path with 3-5 tasks and failure-state branches.",
        "acceptance_criteria": "Prototype allows observation of completion, drop-off points, and manual recovery events.",
    },
    "Usability Testing": {
        "artifact_name": "Usability Test Script + Task Pack",
        "artifact_spec": "Moderator script, task scenarios, and observation sheet for errors, time on task, and interventions.",
        "acceptance_criteria": "Tasks map directly to the assumption risk and can produce comparable results across participants.",
    },
    "Wizard of Oz": {
        "artifact_name": "Wizard of Oz Service Runbook",
        "artifact_spec": "Operator playbook, backstage handoff checklist, and visible user journey script.",
        "acceptance_criteria": "Backstage steps are repeatable and customer-facing flow appears consistently automated.",
    },
    "Mock Sale": {
        "artifact_name": "Mock Offer Deck + Pricing Script",
        "artifact_spec": "Offer narrative, pricing options, objection-handling script, and commitment capture form.",
        "acceptance_criteria": "Sales conversation produces explicit commit/no-commit signal and objection categories.",
    },
    "Pre-Order Test": {
        "artifact_name": "Pre-Order Checkout Package",
        "artifact_spec": "Pricing page, reservation checkout flow, and terms/fulfillment communication template.",
        "acceptance_criteria": "Prospects can place a reversible commitment and completion events are captured reliably.",
    },
}

_STOP_WORDS = frozenset({
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
    "has", "he", "in", "is", "it", "its", "of", "on", "or", "that",
    "the", "to", "was", "were", "will", "with", "you", "whether",
    "this", "not", "can", "do", "does", "i", "we", "they", "my",
    "our", "believe",
})


def _score_card_fit(assumption_text: str, card: ExperimentCard) -> float:
    """Score how well a card matches an assumption based on word overlap."""
    assumption_words = set(assumption_text.lower().split()) - _STOP_WORDS
    card_words = set(card.what_it_tests.lower().split()) - _STOP_WORDS
    card_words |= set(card.best_used_when.lower().split()) - _STOP_WORDS
    if not assumption_words or not card_words:
        return 0.0
    return len(assumption_words & card_words) / len(assumption_words)


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


def _extract_top_assumptions(assumptions: str, step7_structured: dict[str, object] | None = None) -> list[TopAssumption]:
    """Extract test-first assumptions, preferring structured data over markdown parsing."""
    if step7_structured:
        rows: list[TopAssumption] = []
        for cat in step7_structured.get("categories", []):
            category = cat.get("category", "")
            for a in cat.get("assumptions", []):
                if a.get("suggested_quadrant") == "Test first":
                    text = a.get("assumption", "")
                    if not text.startswith("I believe"):
                        text = f"I believe {text}"
                    rows.append(TopAssumption(assumption=text, category=category, quadrant="Test first"))
        if rows:
            return rows

    # Fallback: parse markdown for backward compatibility
    if "## Importance × Evidence Map" not in assumptions:
        return []

    matrix_lines = assumptions.split("## Importance × Evidence Map", 1)[1].splitlines()
    rows = []
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


def _select_experiment_path(
    assumption: TopAssumption,
    cards: dict[str, ExperimentCard],
) -> list[ExperimentCard]:
    """Select a content-aware experiment path from EXPERIMENT_MATRIX.

    Uses word overlap between assumption text and card descriptions to pick
    the best-fit cards at each evidence level, following library sequencing
    relationships where possible.  Falls back to PATH_BY_CATEGORY when the
    matrix yields no candidates.
    """
    category = assumption.category
    matrix = EXPERIMENT_MATRIX.get(category)
    if not matrix:
        raise ValueError(f"Unexpected assumption category: {category}")

    def _pick_best(
        candidates: list[ExperimentCard],
        exclude: set[str] | None = None,
        prefer_next_of: ExperimentCard | None = None,
    ) -> ExperimentCard | None:
        if exclude:
            candidates = [c for c in candidates if c.name not in exclude]
        if not candidates:
            return None
        if prefer_next_of:
            preferred = [
                c for c in candidates
                if c.name in prefer_next_of.usually_runs_next
                or prefer_next_of.name in c.usually_runs_after
            ]
            if preferred:
                candidates = preferred
        scored = sorted(
            candidates,
            key=lambda c: _score_card_fit(assumption.assumption, c),
            reverse=True,
        )
        return scored[0]

    weak_cards = [cards[n] for n in matrix.get("Weak", []) if n in cards]
    medium_cards = [cards[n] for n in matrix.get("Medium", []) if n in cards]
    strong_cards = [cards[n] for n in matrix.get("Strong", []) if n in cards]

    first = _pick_best(weak_cards)
    if not first:
        path_names = PATH_BY_CATEGORY.get(category, [])
        return [cards[n] for n in path_names]

    second = _pick_best(medium_cards, prefer_next_of=first)

    if strong_cards:
        third = _pick_best(strong_cards, prefer_next_of=second)
    elif medium_cards and second:
        third = _pick_best(medium_cards, exclude={second.name}, prefer_next_of=first)
    else:
        third = None

    path = [c for c in (first, second, third) if c is not None]

    for i in range(1, len(path)):
        if EVIDENCE_ORDER[path[i].evidence_strength] < EVIDENCE_ORDER[path[i - 1].evidence_strength]:
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
    if len(path) >= 3:
        escalation = (
            f"The path then escalates through {path[1].name} and {path[2].name} "
            f"only if the earlier signals justify stronger investment."
        )
    elif len(path) == 2:
        escalation = (
            f"The path then escalates to {path[1].name} "
            f"only if the earlier signal justifies stronger investment."
        )
    else:
        escalation = ""
    lines.extend(
        [
            "",
            "### Selection rationale",
            (
                f"This sequence starts with {path[0].name} because the assumption currently "
                f"has no direct evidence and needs the cheapest credible signal first. {escalation}"
            ).rstrip(),
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


def _asset_blueprint(card: ExperimentCard) -> dict[str, str]:
    blueprint = ASSET_BLUEPRINTS.get(card.name)
    if blueprint:
        return blueprint
    return {
        "artifact_name": f"{card.name} Evidence Package",
        "artifact_spec": f"Execution-ready asset set tailored to {card.name.lower()} with instrumentation for evidence capture.",
        "acceptance_criteria": "Asset can be executed in one cycle and captures both behavioral signal and decision evidence.",
    }


def _format_worksheet(assumption: TopAssumption, primary_card: ExperimentCard, next_card: ExperimentCard | None) -> str:
    next_if_mixed = next_card.name if next_card else "Refine the same experiment"
    next_if_positive = next_card.name if next_card else "Summarize the evidence and decide whether to stop"
    asset = _asset_blueprint(primary_card)
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
            f"- **Asset needed:** {asset['artifact_name']}",
            f"- **Exact artifact scope:** {asset['artifact_spec']}",
            f"- **Artifact acceptance criteria:** {asset['acceptance_criteria']}",
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
    asset = _asset_blueprint(primary_card)
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
        "asset_needed": asset["artifact_name"],
        "asset_spec": asset["artifact_spec"],
        "asset_acceptance_criteria": asset["acceptance_criteria"],
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


def _path_from_step8c(
    assumption: TopAssumption,
    cards: dict[str, ExperimentCard],
    experiment_paths: list[dict[str, object]],
) -> list[ExperimentCard] | None:
    for item in experiment_paths:
        if str(item.get("assumption", "")).strip() != assumption.assumption:
            continue
        path_cards: list[ExperimentCard] = []
        for card in item.get("path_cards") or []:
            name = str(card.get("card_name", "")).strip()
            if name in cards:
                path_cards.append(cards[name])
        if path_cards:
            return path_cards
    return None


def _build_outputs(state: BMIWorkflowState) -> tuple[str, str, str, list[dict[str, object]]]:
    cards, precoil_library = _load_assets()
    if "step_8_behavior" not in precoil_library.get("agent_usage_guidance", {}):
        raise ValueError("Unexpected Precoil step 8 guidance")

    top_assumptions = _extract_top_assumptions(
        state.get("assumptions", ""),
        step7_structured=state.get("step7_structured"),
    )
    step8c_paths = state.get("experiment_paths") or []
    pattern_context = ", ".join(state.get("selected_patterns", [])) or "approved patterns"
    selections: list[str] = []
    plans: list[str] = []
    worksheets: list[str] = []
    card_objects: list[dict[str, object]] = []

    for assumption in top_assumptions:
        path = _path_from_step8c(assumption, cards, step8c_paths) or _select_experiment_path(assumption, cards)
        selections.append(_format_selection(assumption, path))
        plans.append(_format_precoil_brief(assumption, path[0]))
        plans.append(_format_implementation_plan(assumption, path[0]))
        plans.append(_format_evidence_sequence(assumption, path))
        worksheets.append(_format_worksheet(assumption, path[0], path[1] if len(path) > 1 else None))
        card_objects.append(_build_card_object(assumption, path[0], path, len(card_objects) + 1))

    if not top_assumptions:
        return "", "", "", []

    selections_text = "\n".join([
        "## Pattern Context",
        f"Selected patterns: {pattern_context}",
        "",
    ]) + "\n\n" + "\n\n".join(selections)
    plans_text = "\n".join([
        "## Pattern Context",
        f"Selected patterns: {pattern_context}",
        "",
    ]) + "\n\n" + "\n\n".join(plans)
    worksheets_text = "\n".join([
        "## Pattern Context",
        f"Selected patterns: {pattern_context}",
        "",
    ]) + "\n\n" + "\n\n".join(worksheets)

    return selections_text, plans_text, worksheets_text, card_objects


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
