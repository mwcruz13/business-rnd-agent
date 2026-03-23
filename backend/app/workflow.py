from __future__ import annotations

import copy
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy import select

from backend.app.checkpoints import CheckpointDecision
from backend.app.checkpoints import get_checkpoint_for_step
from backend.app.checkpoints import validate_checkpoint_state
from backend.app.checkpoints import validate_decision
from backend.app.config import get_settings
from backend.app.db.models import CheckpointRecord
from backend.app.db.models import StepOutput
from backend.app.db.models import WorkflowRun
from backend.app.db.session import DatabaseSchemaNotReadyError
from backend.app.db.session import ensure_database_schema
from backend.app.db.session import SessionLocal
from backend.app.graph import build_graph
from backend.app.graph import WORKFLOW_STEP_ORDER
from backend.app.graph import WORKFLOW_STEP_RUNNERS
from backend.app.ingest.csv import load_csv_rows
from backend.app.ingest.csv import load_csv_rows_from_text
from backend.app.ingest.text import load_text
from backend.app.state import BMIWorkflowState


def run_workflow_from_voc_data(
    voc_data: str,
    *,
    session_id: str | None = None,
    llm_backend: str | None = None,
    input_type: str = "text",
    pause_at_checkpoints: bool = False,
) -> BMIWorkflowState:
    normalized_voc_data = voc_data.strip()
    if not normalized_voc_data:
        raise ValueError("Workflow input cannot be empty")

    settings = get_settings()
    initial_state: BMIWorkflowState = {
        "session_id": session_id or str(uuid.uuid4()),
        "current_step": "ingest",
        "input_type": input_type,
        "llm_backend": llm_backend or settings.llm_backend,
        "voc_data": normalized_voc_data,
    }
    ensure_database_schema()
    if pause_at_checkpoints:
        return _start_checkpointed_run(initial_state)

    result = build_graph().invoke(initial_state)
    final_state = _decorate_state(result, run_status="completed", pending_checkpoint=None)
    _persist_completed_run(final_state)
    return final_state


def run_workflow_from_path(
    input_path: str | Path,
    *,
    session_id: str | None = None,
    llm_backend: str | None = None,
    pause_at_checkpoints: bool = False,
) -> BMIWorkflowState:
    path = Path(input_path)
    suffix = path.suffix.lower()

    if suffix == ".txt":
        return run_workflow_from_voc_data(
            load_text(str(path)),
            session_id=session_id,
            llm_backend=llm_backend,
            input_type="text",
            pause_at_checkpoints=pause_at_checkpoints,
        )
    if suffix == ".csv":
        return run_workflow_from_voc_data(
            _render_csv_rows_as_voc_data(load_csv_rows(str(path))),
            session_id=session_id,
            llm_backend=llm_backend,
            input_type="csv",
            pause_at_checkpoints=pause_at_checkpoints,
        )

    raise ValueError(f"Unsupported workflow input file type: {path.suffix or '<none>'}")


def run_workflow_from_csv_text(
    csv_text: str,
    *,
    session_id: str | None = None,
    llm_backend: str | None = None,
    pause_at_checkpoints: bool = False,
) -> BMIWorkflowState:
    return run_workflow_from_voc_data(
        _render_csv_rows_as_voc_data(load_csv_rows_from_text(csv_text)),
        session_id=session_id,
        llm_backend=llm_backend,
        input_type="csv",
        pause_at_checkpoints=pause_at_checkpoints,
    )


def get_run_state(session_id: str) -> BMIWorkflowState:
    ensure_database_schema()
    with SessionLocal() as session:
        run = session.get(WorkflowRun, session_id)
        if run is None:
            raise ValueError(f"Unknown workflow session: {session_id}")
        return BMIWorkflowState(run.state_json)


def resume_workflow(
    session_id: str,
    *,
    decision: str,
    edit_state: dict[str, Any] | None = None,
) -> BMIWorkflowState:
    ensure_database_schema()
    validated_decision = validate_decision(decision)

    with SessionLocal() as session:
        run = session.get(WorkflowRun, session_id)
        if run is None:
            raise ValueError(f"Unknown workflow session: {session_id}")
        if run.status != "paused" or not run.pending_checkpoint:
            raise ValueError(f"Workflow session {session_id} is not waiting on a checkpoint")

        checkpoint = session.scalar(
            select(CheckpointRecord)
            .where(
                CheckpointRecord.session_id == session_id,
                CheckpointRecord.checkpoint_name == run.pending_checkpoint,
                CheckpointRecord.decision.is_(None),
            )
            .order_by(CheckpointRecord.id.desc())
            .limit(1)
        )
        if checkpoint is None:
            raise ValueError(f"Workflow session {session_id} has no pending checkpoint record")

        checkpoint.decision = validated_decision
        checkpoint.edit_json = edit_state
        checkpoint.resolved_at = datetime.utcnow()

        if validated_decision == "retry":
            state_to_resume = BMIWorkflowState(copy.deepcopy(checkpoint.state_before_json))
            start_index = WORKFLOW_STEP_ORDER.index(checkpoint.after_step_name)
        else:
            state_to_resume = BMIWorkflowState(copy.deepcopy(checkpoint.state_after_json))
            if edit_state:
                for key, value in edit_state.items():
                    state_to_resume[key] = value
            validate_checkpoint_state(checkpoint.checkpoint_name, state_to_resume)
            start_index = WORKFLOW_STEP_ORDER.index(checkpoint.after_step_name) + 1

        session.commit()

    return _execute_from_index(session_id, state_to_resume, start_index, pause_at_checkpoints=True)


def _render_csv_rows_as_voc_data(rows: list[dict[str, str]]) -> str:
    rendered_rows: list[str] = []
    for index, row in enumerate(rows, start=1):
        non_empty_cells = [f"{column}={value.strip()}" for column, value in row.items() if value and value.strip()]
        if non_empty_cells:
            rendered_rows.append(f"Row {index}: " + "; ".join(non_empty_cells))

    if not rendered_rows:
        raise ValueError("CSV workflow input does not contain any non-empty survey content")
    return "\n".join(rendered_rows)


def _start_checkpointed_run(initial_state: BMIWorkflowState) -> BMIWorkflowState:
    session_id = str(initial_state["session_id"])
    with SessionLocal() as session:
        if session.get(WorkflowRun, session_id) is not None:
            raise ValueError(f"Workflow session already exists: {session_id}")
        session.add(
            WorkflowRun(
                session_id=session_id,
                input_type=str(initial_state["input_type"]),
                status="in_progress",
                llm_backend=str(initial_state["llm_backend"]),
                current_step=str(initial_state["current_step"]),
                pending_checkpoint=None,
                voc_data=str(initial_state["voc_data"]),
                state_json=dict(initial_state),
            )
        )
        session.commit()

    return _execute_from_index(session_id, initial_state, 0, pause_at_checkpoints=True)


def _execute_from_index(
    session_id: str,
    state: BMIWorkflowState,
    start_index: int,
    *,
    pause_at_checkpoints: bool,
) -> BMIWorkflowState:
    current_state = BMIWorkflowState(copy.deepcopy(state))

    with SessionLocal() as session:
        run = session.get(WorkflowRun, session_id)
        if run is None:
            raise ValueError(f"Unknown workflow session: {session_id}")

        for step_index in range(start_index, len(WORKFLOW_STEP_ORDER)):
            step_name = WORKFLOW_STEP_ORDER[step_index]
            step_runner = WORKFLOW_STEP_RUNNERS[step_name]
            state_before = BMIWorkflowState(copy.deepcopy(current_state))
            current_state = step_runner(BMIWorkflowState(copy.deepcopy(current_state)))

            session.add(
                StepOutput(
                    session_id=session_id,
                    step_number=step_index + 1,
                    step_name=step_name,
                    input_json=dict(state_before),
                    output_json=dict(current_state),
                )
            )

            checkpoint = get_checkpoint_for_step(step_name)
            if checkpoint and pause_at_checkpoints:
                paused_state = _decorate_state(current_state, run_status="paused", pending_checkpoint=checkpoint.name)
                session.add(
                    CheckpointRecord(
                        session_id=session_id,
                        checkpoint_name=checkpoint.name,
                        after_step_name=checkpoint.after_step_name,
                        step_number=checkpoint.step_number,
                        decision=None,
                        edit_json=None,
                        state_before_json=dict(state_before),
                        state_after_json=dict(current_state),
                    )
                )
                run.status = "paused"
                run.current_step = str(current_state["current_step"])
                run.pending_checkpoint = checkpoint.name
                run.state_json = dict(paused_state)
                session.commit()
                return paused_state

        completed_state = _decorate_state(current_state, run_status="completed", pending_checkpoint=None)
        run.status = "completed"
        run.current_step = str(current_state["current_step"])
        run.pending_checkpoint = None
        run.state_json = dict(completed_state)
        session.commit()
        return completed_state


def _persist_completed_run(final_state: BMIWorkflowState) -> None:
    session_id = str(final_state["session_id"])
    with SessionLocal() as session:
        existing_run = session.get(WorkflowRun, session_id)
        if existing_run is not None:
            raise ValueError(f"Workflow session already exists: {session_id}")
        session.add(
            WorkflowRun(
                session_id=session_id,
                input_type=str(final_state["input_type"]),
                status="completed",
                llm_backend=str(final_state["llm_backend"]),
                current_step=str(final_state["current_step"]),
                pending_checkpoint=None,
                voc_data=str(final_state["voc_data"]),
                state_json=dict(final_state),
            )
        )
        session.commit()


def _decorate_state(
    state: BMIWorkflowState,
    *,
    run_status: str,
    pending_checkpoint: str | None,
) -> BMIWorkflowState:
    decorated_state = BMIWorkflowState(copy.deepcopy(state))
    decorated_state["run_status"] = run_status
    if pending_checkpoint is None:
        decorated_state.pop("pending_checkpoint", None)
    else:
        decorated_state["pending_checkpoint"] = pending_checkpoint
    return decorated_state