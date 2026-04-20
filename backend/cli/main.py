import json
from pathlib import Path

import typer

from backend.app.db.session import DatabaseSchemaNotReadyError
from backend.app.workflow import get_run_state
from backend.app.workflow import resume_workflow
from backend.app.workflow import run_workflow_from_path


app = typer.Typer(help="BMI Consultant CLI")


@app.command()
def run(
    input: Path = typer.Option(..., "--input", exists=True, dir_okay=False, readable=True),
    backend: str = typer.Option("azure", "--backend"),
    session_id: str | None = typer.Option(None, "--session-id"),
    pause_at_checkpoints: bool = typer.Option(True, "--pause-at-checkpoints/--no-pause-at-checkpoints"),
) -> None:
    try:
        result = run_workflow_from_path(
            input,
            session_id=session_id,
            llm_backend=backend,
            pause_at_checkpoints=pause_at_checkpoints,
        )
    except DatabaseSchemaNotReadyError as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from error

    typer.echo(f"session_id={result['session_id']}")
    typer.echo(f"current_step={result['current_step']}")
    typer.echo(f"run_status={result.get('run_status', 'unknown')}")
    if result.get("pending_checkpoint"):
        typer.echo(f"pending_checkpoint={result['pending_checkpoint']}")
    for field in [
        "agent_recommendation",
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
    ]:
        value = result.get(field)
        if value:
            typer.echo("")
            typer.echo(f"## {field}")
            typer.echo(str(value))


@app.command()
def resume(
    session_id: str = typer.Option(..., "--session-id"),
    decision: str = typer.Option(..., "--decision"),
    edit_json: Path | None = typer.Option(None, "--edit-json", exists=True, dir_okay=False, readable=True),
) -> None:
    edit_state = None
    if edit_json is not None:
        edit_state = json.loads(edit_json.read_text(encoding="utf-8"))

    try:
        result = resume_workflow(session_id, decision=decision, edit_state=edit_state)
    except DatabaseSchemaNotReadyError as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from error
    typer.echo(f"session_id={result['session_id']}")
    typer.echo(f"current_step={result['current_step']}")
    typer.echo(f"run_status={result.get('run_status', 'unknown')}")
    if result.get("pending_checkpoint"):
        typer.echo(f"pending_checkpoint={result['pending_checkpoint']}")


@app.command()
def status(session_id: str = typer.Option(..., "--session-id")) -> None:
    try:
        result = get_run_state(session_id)
    except DatabaseSchemaNotReadyError as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from error
    typer.echo(f"session_id={result['session_id']}")
    typer.echo(f"current_step={result['current_step']}")
    typer.echo(f"run_status={result.get('run_status', 'unknown')}")
    if result.get("pending_checkpoint"):
        typer.echo(f"pending_checkpoint={result['pending_checkpoint']}")


@app.command(name="export-report")
def export_report_cmd(
    session_id: str | None = typer.Option(None, "--session-id"),
    output: Path | None = typer.Option(None, "--output", "-o"),
) -> None:
    """Export a workflow session to a structured Markdown report."""
    from backend.cli.export_report import export_report

    export_report(session_id=session_id, output=output)


@app.command(name="export-pptx")
def export_pptx_cmd(
    session_id: str | None = typer.Option(None, "--session-id"),
    output: str | None = typer.Option(None, "--output", "-o"),
    template: str = typer.Option(
        "hpe_dark_template.pptx",
        "--template",
    ),
) -> None:
    """Export a workflow session to an HPE-branded PowerPoint report."""
    from backend.app.db.models import WorkflowRun
    from backend.app.db.session import SessionLocal
    from backend.cli.generate_report_pptx import generate_report_pptx

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
                typer.echo("Error: no workflow runs found.", err=True)
                raise typer.Exit(code=1)
            typer.echo(f"Using most recent session: {run.session_id}")

        state = run.state_json if isinstance(run.state_json, dict) else {}
        meta = {
            "session_id": run.session_id,
            "session_name": run.session_name,
            "created": run.created_at.strftime("%Y-%m-%d %H:%M UTC") if run.created_at else "N/A",
            "status": run.status,
            "llm_backend": run.llm_backend,
            "input_type": run.input_type,
        }

        out = generate_report_pptx(state, meta, template_path=template, output_path=output)
        typer.echo(f"Report saved to {out}")
    finally:
        sess.close()


@app.command()
def step1(
    input: Path = typer.Option(..., "--input", exists=True, dir_okay=False, readable=True),
    backend: str = typer.Option("azure", "--backend"),
) -> None:
    """Run only Step 1 (SOC Radar signal scan) against real input using a real LLM.

    Prints the full structured JSON output — signals, interpretations,
    priorities, coverage gaps, and agent recommendation.
    """
    from backend.app.config import get_settings
    from backend.app.ingest.text import load_text
    from backend.app.ingest.csv import load_csv_rows, load_csv_rows_from_text
    from backend.app.llm.factory import get_chat_model
    from backend.app.nodes.step1_signal_llm import run_step1_llm
    from backend.app.state import BMIWorkflowState

    suffix = input.suffix.lower()
    if suffix == ".csv":
        rows = load_csv_rows(str(input))
        rendered_rows = []
        for idx, row in enumerate(rows, 1):
            cells = [f"{col}={val.strip()}" for col, val in row.items() if val and val.strip()]
            if cells:
                rendered_rows.append(f"Row {idx}: " + "; ".join(cells))
        voc_data = "\n".join(rendered_rows)
    else:
        voc_data = load_text(str(input))

    if not voc_data.strip():
        typer.echo("Error: Input file is empty.", err=True)
        raise typer.Exit(code=1)

    settings = get_settings()
    # Override backend if user provided a different one
    if backend != settings.llm_backend:
        settings.llm_backend = backend

    typer.echo(f"LLM backend: {settings.llm_backend}")
    typer.echo(f"Input file:  {input}")
    typer.echo(f"Input chars: {len(voc_data)}")
    typer.echo("Calling LLM for Step 1 signal scan...")
    typer.echo("")

    llm = get_chat_model(settings)
    state: BMIWorkflowState = {"voc_data": voc_data}
    result = run_step1_llm(state, llm)

    # Print the signal output as formatted JSON
    output = {
        "signals": result.get("signals", []),
        "interpreted_signals": result.get("interpreted_signals", []),
        "priority_matrix": result.get("priority_matrix", []),
        "coverage_gaps": result.get("coverage_gaps", []),
        "agent_recommendation": result.get("agent_recommendation", ""),
    }
    typer.echo(json.dumps(output, indent=2))


if __name__ == "__main__":
    app()
