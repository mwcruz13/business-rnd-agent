import json
from pathlib import Path
from uuid import uuid4

from typer.testing import CliRunner

from backend.cli.main import app


def test_cli_run_executes_the_graph(tmp_path) -> None:
    runner = CliRunner()
    session_id = f"cli-run-test-{uuid4()}"
    input_path = tmp_path / "source.txt"
    input_path.write_text(
        "Customers report onboarding friction, too many manual steps, and delays before they reach value.",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "run",
            "--input",
            str(input_path),
            "--backend",
            "azure",
            "--session-id",
            session_id,
            "--no-pause-at-checkpoints",
        ],
    )

    assert result.exit_code == 0
    assert f"session_id={session_id}" in result.stdout
    assert "current_step=pdsa_plan" in result.stdout
    assert "## experiment_selections" in result.stdout


def test_cli_run_and_resume_support_checkpoint_flow(tmp_path) -> None:
    runner = CliRunner()
    session_id = f"cli-resume-test-{uuid4()}"
    input_path = tmp_path / "source.txt"
    input_path.write_text(
        "Customers report onboarding friction, too many manual steps, and delays before they reach value.",
        encoding="utf-8",
    )

    start = runner.invoke(
        app,
        ["run", "--input", str(input_path), "--session-id", session_id, "--pause-at-checkpoints"],
    )
    assert start.exit_code == 0
    assert "run_status=paused" in start.stdout
    assert "pending_checkpoint=checkpoint_1" in start.stdout

    resume_1 = runner.invoke(app, ["resume", "--session-id", session_id, "--decision", "approve"])
    assert resume_1.exit_code == 0
    assert "pending_checkpoint=checkpoint_2" in resume_1.stdout

    edit_json = tmp_path / "checkpoint-1-5.json"
    edit_json.write_text(
        json.dumps(
            {
                "pattern_direction": "shift",
                "selected_patterns": ["Cost Differentiators"],
                "pattern_rationale": "Consultant selected the incumbent-transformation path.",
            }
        ),
        encoding="utf-8",
    )
    resume_2 = runner.invoke(
        app,
        [
            "resume",
            "--session-id",
            session_id,
            "--decision",
            "edit",
            "--edit-json",
            str(edit_json),
        ],
    )
    assert resume_2.exit_code == 0
    assert "pending_checkpoint=checkpoint_3" in resume_2.stdout