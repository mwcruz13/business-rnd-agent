"""Export a BMI workflow session to a structured Markdown report.

Usage (inside container):
    python -m backend.cli.export_report --session-id <ID> [--output reports/my_report.md]
    bmi export-report --session-id <ID>                          # via CLI entrypoint

If --session-id is omitted the most recent completed session is used.
If --output is omitted, the report is written to reports/<session_id>.md.
"""

from __future__ import annotations

import json
import textwrap
from datetime import datetime
from pathlib import Path
from typing import Any

import typer

from backend.app.db.models import WorkflowRun
from backend.app.db.session import SessionLocal

# ---------------------------------------------------------------------------
# Markdown rendering helpers
# ---------------------------------------------------------------------------

_STEP_TITLES: dict[str, str] = {
    "agent_recommendation": "Step 1-2 — Signal Scan & Pattern Selection",
    "customer_profile": "Step 3 — Customer Empathy Profile",
    "value_driver_tree": "Step 4 — Value Driver Tree",
    "actionable_insights": "Step 4 — Actionable Insights",
    "value_proposition_canvas": "Step 5 — Value Proposition Canvas",
    "business_model_canvas": "Step 6 — Business Model Canvas",
    "fit_assessment": "Step 6 — Fit Assessment",
    "assumptions": "Step 7 — Assumptions & Risk Map",
    "experiment_selections": "Step 8 — Experiment Selections",
    "experiment_plans": "Step 8 — Experiment Implementation Plans",
    "experiment_worksheets": "Step 8 — Experiment Worksheets",
}


def _render_signal_table(signals: list[dict[str, Any]]) -> str:
    """Render detected signals as a markdown table."""
    if not signals:
        return "_No signals detected._\n"
    lines = [
        "| # | Signal | Zone | Source | Observable Behavior |",
        "|---|--------|------|--------|---------------------|",
    ]
    for i, s in enumerate(signals, 1):
        sig = s.get("signal", "").replace("\n", " ")
        zone = s.get("zone", "")
        src = s.get("source_type", "")
        obs = s.get("observable_behavior", "").replace("\n", " ")
        lines.append(f"| {i} | {sig} | {zone} | {src} | {obs} |")
    lines.append("")
    # Evidence bullets
    for i, s in enumerate(signals, 1):
        evidence = s.get("evidence", [])
        if evidence:
            lines.append(f"**Signal {i} evidence:**")
            for ev in evidence:
                lines.append(f"- {ev}")
            lines.append("")
    return "\n".join(lines)


def _render_interpretation_table(interps: list[dict[str, Any]]) -> str:
    if not interps:
        return "_No interpretations._\n"
    lines = [
        "| Signal | Classification | Confidence | Rationale | Alt. Explanation |",
        "|--------|---------------|------------|-----------|------------------|",
    ]
    for s in interps:
        sig = s.get("signal", "").replace("\n", " ")[:80]
        cls = s.get("classification", "")
        conf = s.get("confidence", "")
        rat = s.get("rationale", "").replace("\n", " ")[:120]
        alt = s.get("alternative_explanation", "").replace("\n", " ")[:100]
        lines.append(f"| {sig} | {cls} | {conf} | {rat} | {alt} |")
    lines.append("")
    # Filters
    for s in interps:
        filters = s.get("filters", [])
        if filters:
            lines.append(f"**{s.get('signal_id', '')} filters:** {', '.join(filters)}")
    lines.append("")
    return "\n".join(lines)


def _render_priority_table(matrix: list[dict[str, Any]]) -> str:
    if not matrix:
        return "_No priority matrix._\n"
    lines = [
        "| Signal | Impact | Speed | Score | Tier | Rationale |",
        "|--------|--------|-------|-------|------|-----------|",
    ]
    for p in matrix:
        sig = p.get("signal", "").replace("\n", " ")[:60]
        lines.append(
            f"| {sig} | {p.get('impact','')} | {p.get('speed','')} "
            f"| {p.get('score','')} | {p.get('tier','')} "
            f"| {p.get('rationale','').replace(chr(10),' ')[:100]} |"
        )
    lines.append("")
    return "\n".join(lines)


def _render_coverage_gaps(gaps: list[dict[str, str]]) -> str:
    if not gaps:
        return "_No coverage gaps identified._\n"
    lines = ["| Zone | Note |", "|------|------|"]
    for g in gaps:
        lines.append(f"| {g.get('zone','')} | {g.get('note','')} |")
    lines.append("")
    return "\n".join(lines)


def _render_experiment_cards(cards: list[dict[str, Any]]) -> str:
    """Render experiment card selections as a summary table + detail blocks."""
    if not cards:
        return "_No experiment cards._\n"
    # Summary table
    lines = [
        "| # | Assumption | Category | Strength | Card |",
        "|---|-----------|----------|----------|------|",
    ]
    for i, c in enumerate(cards, 1):
        assumption = c.get("assumption", "").replace("\n", " ")[:80]
        lines.append(
            f"| {i} | {assumption} | {c.get('category','')} "
            f"| {c.get('evidence_strength','')} | {c.get('card_name','')} |"
        )
    lines.append("")

    # Detail blocks
    for i, c in enumerate(cards, 1):
        lines.append(f"### Card {i}: {c.get('card_name','')} ({c.get('category','')})")
        lines.append("")
        lines.append(f"**Assumption:** {c.get('assumption','')}")
        lines.append(f"**What it tests:** {c.get('what_it_tests','')}")
        lines.append(f"**Best used when:** {c.get('best_used_when','')}")
        lines.append(f"**Test audience:** {c.get('test_audience','')}")
        lines.append(f"**Sample size:** {c.get('sample_size','')}")
        lines.append(f"**Timebox:** {c.get('timebox','')}")
        lines.append("")
        lines.append(f"**Primary metric:** {c.get('primary_metric','')}")
        lines.append(f"**Secondary metrics:** {c.get('secondary_metrics','')}")
        lines.append("")
        lines.append(f"- Success: {c.get('success_looks_like','')}")
        lines.append(f"- Failure: {c.get('failure_looks_like','')}")
        lines.append(f"- Ambiguous: {c.get('ambiguous_looks_like','')}")
        lines.append("")
        # Evidence path
        path = c.get("evidence_path", [])
        if path:
            lines.append("**Evidence path:**")
            lines.append("")
            lines.append("| Step | Card | Strength |")
            lines.append("|------|------|----------|")
            for p in path:
                lines.append(
                    f"| {p.get('step','')} | {p.get('card_name','')} "
                    f"| {p.get('evidence_strength','')} |"
                )
            lines.append("")
        lines.append(f"**Selection rationale:** {c.get('selection_rationale','')}")
        lines.append("")
        # Zone B evidence fields (populated after experiment execution)
        evidence_status = c.get("evidence_status")
        evidence_decision = c.get("evidence_decision")
        evidence_summary = c.get("evidence_summary")
        if evidence_status or evidence_decision or evidence_summary:
            lines.append("**Evidence Collection:**")
            lines.append("")
            if evidence_status:
                lines.append(f"- **Status:** {evidence_status}")
            if evidence_decision:
                lines.append(f"- **Evidence Decision:** {evidence_decision}")
            if evidence_summary:
                lines.append(f"- **Summary:** {evidence_summary}")
            lines.append("")
    return "\n".join(lines)


def _render_signal_recommendations(recs: list[dict[str, Any]]) -> str:
    if not recs:
        return ""
    lines = [
        "### Signal Recommendations",
        "",
        "| Signal | Tier | What We Know | Experiment Candidate |",
        "|--------|------|-------------|---------------------|",
    ]
    for r in recs:
        lines.append(
            f"| {r.get('signal_id','')} | {r.get('action_tier','')} "
            f"| {r.get('what_we_know','').replace(chr(10),' ')[:80]} "
            f"| {r.get('experiment_candidate','').replace(chr(10),' ')[:80]} |"
        )
    lines.append("")
    for r in recs:
        unknowns = r.get("what_we_dont_know", [])
        if unknowns:
            lines.append(f"**{r.get('signal_id','')} — what we don't know:**")
            for u in unknowns:
                lines.append(f"- {u}")
            lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main report builder
# ---------------------------------------------------------------------------

def build_report(run: WorkflowRun) -> str:
    """Build a full markdown report from a WorkflowRun record."""
    state: dict[str, Any] = run.state_json if isinstance(run.state_json, dict) else {}
    created = run.created_at.strftime("%Y-%m-%d %H:%M UTC") if run.created_at else "unknown"

    parts: list[str] = []

    # ── Header ──────────────────────────────────────────────────────────
    session_name = run.session_name or state.get("session_name") or "Untitled Session"
    parts.append(f"# BMI Workflow Report — {session_name}")
    parts.append("")
    parts.append("| Field | Value |")
    parts.append("|-------|-------|")
    parts.append(f"| Session ID | `{run.session_id}` |")
    parts.append(f"| Created | {created} |")
    parts.append(f"| Status | {run.status} |")
    parts.append(f"| Current Step | {run.current_step} |")
    parts.append(f"| LLM Backend | {run.llm_backend} |")
    parts.append(f"| Input Type | {run.input_type} |")
    parts.append("")
    parts.append("---")
    parts.append("")

    # ── Step 1: Signals ─────────────────────────────────────────────────
    parts.append("## Step 1 — Signal Scan (SOC Radar)")
    parts.append("")

    signals = state.get("signals", [])
    parts.append("### Detected Signals")
    parts.append("")
    parts.append(_render_signal_table(signals))

    interps = state.get("interpreted_signals", [])
    parts.append("### Interpreted Signals")
    parts.append("")
    parts.append(_render_interpretation_table(interps))

    matrix = state.get("priority_matrix", [])
    parts.append("### Priority Matrix")
    parts.append("")
    parts.append(_render_priority_table(matrix))

    gaps = state.get("coverage_gaps", [])
    parts.append("### Coverage Gaps")
    parts.append("")
    parts.append(_render_coverage_gaps(gaps))

    recs = state.get("signal_recommendations", [])
    if recs:
        parts.append(_render_signal_recommendations(recs))

    # ── Step 2: Pattern Selection ───────────────────────────────────────
    parts.append("## Step 2 — Pattern Selection")
    parts.append("")
    direction = state.get("pattern_direction", "")
    patterns = state.get("selected_patterns", [])
    rationale = state.get("pattern_rationale", "")
    rec_text = state.get("agent_recommendation", "")
    parts.append(f"**Direction:** {direction}")
    parts.append(f"**Selected Patterns:** {', '.join(patterns) if patterns else 'N/A'}")
    parts.append("")
    if rec_text:
        parts.append("### Agent Recommendation")
        parts.append("")
        parts.append(rec_text)
        parts.append("")
    parts.append("---")
    parts.append("")

    # ── Steps 3-8: rendered markdown fields ─────────────────────────────
    _RENDERED_FIELDS = [
        "customer_profile",
        "value_driver_tree",
        "actionable_insights",
        "value_proposition_canvas",
        "business_model_canvas",
        "fit_assessment",
        "assumptions",
        "experiment_selections",
        "experiment_plans",
        "experiment_worksheets",
    ]
    for field in _RENDERED_FIELDS:
        value = state.get(field)
        if not value:
            continue
        title = _STEP_TITLES.get(field, field.replace("_", " ").title())
        parts.append(f"## {title}")
        parts.append("")
        parts.append(str(value).strip())
        parts.append("")
        parts.append("---")
        parts.append("")

    # ── Experiment Cards (structured) ───────────────────────────────────
    cards = state.get("experiment_cards", [])
    if cards:
        parts.append("## Experiment Cards (Structured)")
        parts.append("")
        parts.append(_render_experiment_cards(cards))
        parts.append("---")
        parts.append("")

    # ── Footer ──────────────────────────────────────────────────────────
    parts.append("---")
    parts.append(f"*Report generated on {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}*")
    parts.append("")

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

cli_app = typer.Typer(help="Export a workflow session to a Markdown report.")


@cli_app.command()
def export_report(
    session_id: str | None = typer.Option(
        None, "--session-id", help="Session ID to export. Defaults to most recent completed run."
    ),
    output: Path | None = typer.Option(
        None, "--output", "-o", help="Output file path. Defaults to reports/<session_id>.md."
    ),
) -> None:
    """Export a BMI workflow session to a structured Markdown report."""
    sess = SessionLocal()
    try:
        if session_id:
            run = sess.query(WorkflowRun).filter_by(session_id=session_id).first()
            if not run:
                typer.echo(f"Error: session '{session_id}' not found.", err=True)
                raise typer.Exit(code=1)
        else:
            run = (
                sess.query(WorkflowRun)
                .filter_by(status="completed")
                .order_by(WorkflowRun.created_at.desc())
                .first()
            )
            if not run:
                run = sess.query(WorkflowRun).order_by(WorkflowRun.created_at.desc()).first()
            if not run:
                typer.echo("Error: no workflow runs found in the database.", err=True)
                raise typer.Exit(code=1)
            typer.echo(f"Using most recent session: {run.session_id}")

        report = build_report(run)

        if output is None:
            output = Path("reports") / f"{run.session_id}.md"

        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(report, encoding="utf-8")
        typer.echo(f"Report written to {output}")
    finally:
        sess.close()


if __name__ == "__main__":
    cli_app()
