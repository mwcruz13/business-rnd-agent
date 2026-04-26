"""Portfolio computation service.

Computes Innovation Risk and Expected Return scores from CXIF workflow
state data so that each initiative can be plotted on the Invincible-Company
style 2×2 quadrant chart (Explore / Exploit).
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.db.models import WorkflowRun


# ---------------------------------------------------------------------------
# Score helpers
# ---------------------------------------------------------------------------

_QUADRANT_WEIGHT = {
    "Test first": 3,
    "Monitor": 2,
    "Deprioritize": 1,
    "Safe zone": 0,
}

_EVIDENCE_PENALTY = {
    "None": 2,
    "Weak": 1,
    "Medium": 0,
}

_VP_LEVEL = {"High": 3, "Medium": 2, "Low": 1}

# Workflow step order — earlier step ⇒ higher uncertainty ⇒ higher risk
_STEP_ORDER = [
    "step1a_signal_scan",
    "step1b_signal_recommend",
    "step2_pattern",
    "step3_profile",
    "step4_vpm",
    "step5a_ideation",
    "step5b_scoring",
    "step6_design",
    "step7_risk",
    "step8a_evidence_audit",
    "step8b_card_selection",
    "step8c_path_sequencing",
    "step8_pdsa",
    "step9_artifact_designer",
]


def _step_progress(current_step: str) -> float:
    """Return 0.0 – 1.0 representing how far through the workflow."""
    try:
        idx = _STEP_ORDER.index(current_step)
    except ValueError:
        idx = 0
    return idx / max(len(_STEP_ORDER) - 1, 1)


def compute_risk_score(state: dict[str, Any] | None) -> float:
    """Compute an Innovation Risk score (0–100) from workflow state.

    - Uses DVF assumption quadrants + evidence from ``step7_structured``.
    - Adds a base-risk bonus for *invent* pattern direction.
    - Falls back to a progress-based estimate when step 7 data is absent.
    """
    if not state:
        return 50.0

    structured = state.get("step7_structured")
    if structured and isinstance(structured, dict):
        categories = structured.get("categories") or structured.get("dvf_categories") or []
        if isinstance(categories, list):
            raw = 0.0
            count = 0
            for cat in categories:
                assumptions = cat.get("assumptions", [])
                for a in assumptions:
                    q = a.get("suggested_quadrant", "Monitor")
                    e = a.get("voc_evidence_strength", "None")
                    raw += _QUADRANT_WEIGHT.get(q, 2) + _EVIDENCE_PENALTY.get(e, 1)
                    count += 1
            if count > 0:
                # Max per assumption = 3 + 2 = 5
                normalised = (raw / (count * 5)) * 80  # 0-80 range

                # Pattern direction bonus
                direction = state.get("pattern_direction", "")
                if direction == "invent":
                    normalised += 15
                return min(normalised, 100.0)

    # Fallback: estimate from workflow progress (less progress = more risk)
    current_step = state.get("current_step", "step1a_signal_scan")
    progress = _step_progress(current_step)
    base = 70 - (progress * 40)  # range 70 (step 1) → 30 (step 14)

    direction = state.get("pattern_direction", "")
    if direction == "invent":
        base += 15

    return min(max(base, 0.0), 100.0)


def compute_return_score(state: dict[str, Any] | None) -> float:
    """Compute an Expected Return score (0–100) from workflow state.

    - Uses VP ranking dimensions (coverage, differentiation, evidence) from
      ``vp_rankings``.
    - Falls back to a neutral 50 when VP scoring has not been reached.
    """
    if not state:
        return 50.0

    rankings = state.get("vp_rankings")
    if rankings and isinstance(rankings, list):
        best = 0.0
        for vp in rankings:
            score = (
                _VP_LEVEL.get(vp.get("coverage_score", "Low"), 1)
                + _VP_LEVEL.get(vp.get("differentiation_score", "Low"), 1)
                + _VP_LEVEL.get(vp.get("evidence_score", "Low"), 1)
            )
            best = max(best, score)
        # Max = 9 (3×High), normalise to 0–100
        return (best / 9) * 100

    return 50.0


# ---------------------------------------------------------------------------
# Quadrant label
# ---------------------------------------------------------------------------

def _quadrant_label(risk: float, ret: float) -> str:
    """Assign quadrant per The Invincible Company portfolio map.

    X-axis is *risk* (100 on the left, 0 on the right).  A project with
    risk > 50 is still in the high-risk EXPLORE zone; once experiments
    de-risk it below 50 it moves into the EXPLOIT zone.
    """
    if risk > 50 and ret <= 50:
        return "explore"
    if risk <= 50 and ret > 50:
        return "exploit"
    if risk > 50 and ret > 50:
        return "explore-high-return"
    return "exploit-low-return"


# ---------------------------------------------------------------------------
# Portfolio entry builder
# ---------------------------------------------------------------------------

def _count_assumptions(state: dict[str, Any]) -> int:
    structured = state.get("step7_structured")
    if not structured or not isinstance(structured, dict):
        return 0
    count = 0
    categories = structured.get("categories") or structured.get("dvf_categories") or []
    for cat in categories:
        count += len(cat.get("assumptions", []))
    return count


def _count_experiments(state: dict[str, Any]) -> int:
    cards = state.get("experiment_cards")
    if cards and isinstance(cards, list):
        return len(cards)
    selections = state.get("experiment_card_selections")
    if selections and isinstance(selections, list):
        return len(selections)
    return 0


def build_portfolio_entry(run: WorkflowRun) -> dict[str, Any]:
    """Build a single portfolio entry dict from a WorkflowRun row."""
    state = run.state_json or {}
    portfolio = run.portfolio_json or {}

    risk = compute_risk_score(state)
    ret = compute_return_score(state)

    # Apply overrides from portfolio_json
    risk = portfolio.get("risk_score_override", risk)
    ret = portfolio.get("return_score_override", ret)

    now = datetime.now(timezone.utc)
    created = run.created_at
    if created and created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    days_running = (now - created).days if created else 0

    return {
        "session_id": run.session_id,
        "initiative_name": portfolio.get("initiative_name") or run.session_name or run.session_id,
        "expected_revenue": portfolio.get("expected_revenue"),
        "testing_cost": portfolio.get("testing_cost"),
        "risk_score": round(risk, 1),
        "return_score": round(ret, 1),
        "quadrant": _quadrant_label(risk, ret),
        "pattern_direction": state.get("pattern_direction", "unknown"),
        "selected_patterns": state.get("selected_patterns", []),
        "current_step": run.current_step,
        "status": run.status,
        "created_at": run.created_at.isoformat() if run.created_at else None,
        "updated_at": run.updated_at.isoformat() if run.updated_at else None,
        "days_running": days_running,
        "vp_count": len(state.get("vp_alternatives", [])),
        "assumption_count": _count_assumptions(state),
        "experiment_count": _count_experiments(state),
        "completed_steps_count": len(state.get("completed_steps", [])),
        "risk_score_override": portfolio.get("risk_score_override"),
        "return_score_override": portfolio.get("return_score_override"),
        "notes": portfolio.get("notes"),
    }


def get_portfolio_entries(db: Session) -> list[dict[str, Any]]:
    """Return all portfolio entries, sorted by created_at descending."""
    runs = db.scalars(
        select(WorkflowRun)
        .where(WorkflowRun.status != "failed")
        .order_by(WorkflowRun.created_at.desc())
    ).all()
    return [build_portfolio_entry(r) for r in runs]


def get_portfolio_detail(db: Session, session_id: str) -> dict[str, Any]:
    """Return deep-detail for the project detail panel."""
    run = db.scalar(
        select(WorkflowRun).where(WorkflowRun.session_id == session_id)
    )
    if not run:
        return None

    state = run.state_json or {}
    entry = build_portfolio_entry(run)

    # DVF assumptions (hypothesis log)
    hypotheses = []
    structured = state.get("step7_structured")
    if structured and isinstance(structured, dict):
        categories = structured.get("categories") or structured.get("dvf_categories") or []
        for cat in categories:
            cat_name = cat.get("category", "Unknown")
            for a in cat.get("assumptions", []):
                hypotheses.append({
                    "assumption": a.get("assumption", ""),
                    "category": cat_name,
                    "quadrant": a.get("suggested_quadrant", "Monitor"),
                    "evidence_strength": a.get("voc_evidence_strength", "None"),
                    "rationale": a.get("rationale", ""),
                })

    # Experiment cards
    experiments = []
    cards = state.get("experiment_cards") or state.get("experiment_card_selections") or []
    for card in cards:
        experiments.append({
            "name": card.get("card_name") or card.get("name") or card.get("experiment_name", ""),
            "type": card.get("card_type") or card.get("type", ""),
            "assumption": card.get("assumption", ""),
            "cost_estimate": card.get("cost_estimate") or card.get("estimated_cost", ""),
            "duration": card.get("duration") or card.get("estimated_duration", ""),
            "status": card.get("status", "planned"),
        })

    # VP rankings
    vp_rankings = state.get("vp_rankings", [])

    # Completed steps (learning log)
    completed_steps = state.get("completed_steps", [])

    entry["hypotheses"] = hypotheses
    entry["experiments"] = experiments
    entry["vp_rankings"] = vp_rankings
    entry["completed_steps"] = completed_steps
    entry["business_model_canvas"] = state.get("business_model_canvas", "")
    entry["value_proposition_canvas"] = state.get("value_proposition_canvas", "")

    return entry
