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


@app.command()
def export(run_id: str) -> None:
    typer.echo(f"Scaffolded export command for run_id={run_id}")


if __name__ == "__main__":
    app()
