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
from backend.app.checkpoints import validate_initial_state_for_step
from backend.app.config import get_settings
from backend.app.db.models import CheckpointRecord
from backend.app.db.models import StepOutput
from backend.app.db.models import WorkflowRun
from backend.app.db.session import DatabaseSchemaNotReadyError
from backend.app.db.session import ensure_database_schema
from backend.app.db.session import SessionLocal
from backend.app.graph import build_graph
from backend.app.graph import determine_next_step
from backend.app.graph import steps_completed_before
from backend.app.graph import WORKFLOW_STEP_ORDER
from backend.app.graph import WORKFLOW_STEP_RUNNERS
from backend.app.ingest.csv import load_csv_rows
from backend.app.ingest.csv import load_csv_rows_from_text
from backend.app.ingest.text import load_text


# ---------------------------------------------------------------------------
# Logical step-number → first registry-index mapping
# ---------------------------------------------------------------------------
# Workers declare a logical step_number (1-9).  Sub-steps like 5a/5b or
# 8a/8b/8c share the same logical number.  ``start_workflow_from_step``
# uses this map so that callers continue to specify step_number=1..9 while
# the internal registry may contain more entries.
def _build_logical_step_map() -> dict[int, int]:
    """Return {logical_step_number: first_registry_index}."""
    from backend.app.workers.registry import get_worker_registry
    registry = get_worker_registry()
    mapping: dict[int, int] = {}
    for idx, worker in enumerate(registry.get_all_workers()):
        if worker.step_number not in mapping:
            mapping[worker.step_number] = idx
    return mapping


_LOGICAL_STEP_MAP = _build_logical_step_map()
_MAX_LOGICAL_STEP = max(_LOGICAL_STEP_MAP) if _LOGICAL_STEP_MAP else 1
from backend.app.state import BMIWorkflowState


# ---------------------------------------------------------------------------
# Signal-to-workflow state mapping (Phase 3)
# ---------------------------------------------------------------------------

def _signal_to_workflow_state(
    signal_record: dict,
    sibling_records: list[dict],
    report: dict,
) -> BMIWorkflowState:
    """Translate a SignalRecord + siblings + report into a BMIWorkflowState.

    Pre-populates steps 1a (signal_scan) and 1b (signal_recommend) so that
    the orchestrator naturally starts execution at step 2 (pattern).
    """
    # Build signals list (phase 1 scan data from all siblings)
    signals = []
    for rec in sibling_records:
        fa = rec.get("full_analysis", {})
        p1 = fa.get("phase_1_scan", {})
        signals.append({
            "signal_id": rec.get("signal_id", p1.get("id", "")),
            "signal": rec.get("signal_title", p1.get("signal", "")),
            "zone": rec.get("signal_zone", p1.get("signal_zone", "")),
            "source_type": p1.get("source_type", "Internal VoC"),
            "observable_behavior": rec.get("observable_behavior", p1.get("observable_behavior", "")),
            "evidence": p1.get("evidence", []),
            "supporting_comments": p1.get("supporting_comments", []),
        })

    # Build interpreted_signals list (phase 2 interpret data)
    interpreted_signals = []
    for rec in sibling_records:
        fa = rec.get("full_analysis", {})
        p2 = fa.get("phase_2_interpret", {})
        interpreted_signals.append({
            "signal_id": rec.get("signal_id", p2.get("signal_id", "")),
            "signal": rec.get("signal_title", p2.get("signal", "")),
            "zone": rec.get("signal_zone", ""),
            "classification": rec.get("classification", p2.get("classification", "")),
            "confidence": p2.get("confidence", "Medium"),
            "litmus_test": p2.get("litmus_test", ""),
            "litmus_rationale": p2.get("litmus_rationale", ""),
            "filters": p2.get("filters", []),
            "filters_passed": p2.get("filters_passed", 0),
            "disruptive_potential": p2.get("disruptive_potential", ""),
            "value_network_insight": p2.get("value_network_insight", ""),
            "alternative_explanation": p2.get("alternative_explanation", ""),
            "key_evidence_gap": p2.get("key_evidence_gap", ""),
        })

    # Build priority_matrix (phase 3 prioritize data)
    priority_matrix = []
    for rec in sibling_records:
        fa = rec.get("full_analysis", {})
        p3 = fa.get("phase_3_prioritize", {})
        priority_matrix.append({
            "signal_id": rec.get("signal_id", p3.get("signal_id", "")),
            "signal": rec.get("signal_title", p3.get("signal", "")),
            "classification": rec.get("classification", p3.get("classification", "")),
            "impact": p3.get("impact", 1),
            "speed": p3.get("speed", 1),
            "score": rec.get("priority_score") or p3.get("priority_score", 1),
            "tier": rec.get("action_tier", p3.get("action_tier", "Monitor")),
            "rationale": p3.get("rationale", ""),
        })

    # Build signal_recommendations from phase 4
    signal_recommendations = []
    for rec in sibling_records:
        fa = rec.get("full_analysis", {})
        p4 = fa.get("phase_4_recommend", {})
        if p4:
            signal_recommendations.append({
                "signal_id": rec.get("signal_id"),
                "signal_title": rec.get("signal_title"),
                "action_tier": rec.get("action_tier", ""),
                **{k: v for k, v in p4.items() if k != "signal_id"},
            })

    # Construct voc_data from observable behaviors
    voc_lines = []
    for rec in sibling_records:
        behavior = rec.get("observable_behavior", "")
        if behavior:
            voc_lines.append(f"[{rec.get('signal_id', '')}] {behavior}")
    voc_data = "\n".join(voc_lines) if voc_lines else signal_record.get("signal_title", "")

    # Reinforcement map from the report
    reinforcement_map = report.get("reinforcement_map") or {}

    return BMIWorkflowState(
        current_step="from_signal",
        input_type="signal",
        voc_data=voc_data,
        signals=signals,
        interpreted_signals=interpreted_signals,
        priority_matrix=priority_matrix,
        signal_recommendations=signal_recommendations,
        reinforcement_map=reinforcement_map,
        completed_steps=steps_completed_before(2),  # step1a + step1b done
    )


def run_workflow_from_signal(
    record_id: int,
    *,
    session_id: str | None = None,
    session_name: str | None = None,
    llm_backend: str | None = None,
    pause_at_checkpoints: bool = True,
) -> BMIWorkflowState:
    """Start a CXIF workflow seeded from a stored signal record.

    Loads the signal, its report, and all sibling signals from the same
    report. Maps them into workflow state with steps 1a/1b pre-completed,
    so the graph starts at step 2 (pattern direction).
    """
    from backend.app.services import signal_repository as repo

    ensure_database_schema()
    settings = get_settings()

    # Load the selected signal and its report
    signal_record = repo.get_signal(record_id)
    report = repo.get_report(signal_record["report_id"])

    # Load all sibling signals from the same report
    siblings = repo.list_signals(
        bu=signal_record["bu"],
        survey_source=signal_record["survey_source"],
    )

    # Build pre-populated state
    state = _signal_to_workflow_state(signal_record, siblings, report)
    state["session_id"] = session_id or str(uuid.uuid4())
    state["llm_backend"] = llm_backend or settings.llm_backend
    if session_name:
        state["session_name"] = session_name

    # Persist and execute
    sid = str(state["session_id"])
    with SessionLocal() as session:
        if session.get(WorkflowRun, sid) is not None:
            raise ValueError(f"Workflow session already exists: {sid}")
        session.add(
            WorkflowRun(
                session_id=sid,
                session_name=session_name,
                input_type="signal",
                status="in_progress",
                llm_backend=str(state["llm_backend"]),
                current_step="from_signal",
                pending_checkpoint=None,
                voc_data=str(state.get("voc_data", "")),
                state_json=dict(state),
            )
        )
        session.commit()

    return _execute_orchestrated(sid, state, pause_at_checkpoints=pause_at_checkpoints)


def run_workflow_from_voc_data(
    voc_data: str,
    *,
    session_id: str | None = None,
    session_name: str | None = None,
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
    if session_name:
        initial_state["session_name"] = session_name
    ensure_database_schema()
    if pause_at_checkpoints:
        return _start_checkpointed_run(initial_state)

    result = build_graph().invoke(initial_state, {"recursion_limit": 64})
    final_state = _decorate_state(result, run_status="completed", pending_checkpoint=None)
    _persist_completed_run(final_state)
    return final_state


def run_workflow_from_path(
    input_path: str | Path,
    *,
    session_id: str | None = None,
    session_name: str | None = None,
    llm_backend: str | None = None,
    pause_at_checkpoints: bool = False,
) -> BMIWorkflowState:
    path = Path(input_path)
    suffix = path.suffix.lower()

    if suffix == ".txt":
        return run_workflow_from_voc_data(
            load_text(str(path)),
            session_id=session_id,
            session_name=session_name,
            llm_backend=llm_backend,
            input_type="text",
            pause_at_checkpoints=pause_at_checkpoints,
        )
    if suffix == ".csv":
        return run_workflow_from_voc_data(
            _render_csv_rows_as_voc_data(load_csv_rows(str(path))),
            session_id=session_id,
            session_name=session_name,
            llm_backend=llm_backend,
            input_type="csv",
            pause_at_checkpoints=pause_at_checkpoints,
        )

    raise ValueError(f"Unsupported workflow input file type: {path.suffix or '<none>'}")


def run_workflow_from_csv_text(
    csv_text: str,
    *,
    session_id: str | None = None,
    session_name: str | None = None,
    llm_backend: str | None = None,
    pause_at_checkpoints: bool = False,
) -> BMIWorkflowState:
    return run_workflow_from_voc_data(
        _render_csv_rows_as_voc_data(load_csv_rows_from_text(csv_text)),
        session_id=session_id,
        session_name=session_name,
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
        state = BMIWorkflowState(run.state_json)
        if run.session_name:
            state["session_name"] = run.session_name
        return state


def list_sessions() -> list[dict[str, Any]]:
    """Return a summary list of all workflow sessions, most recent first."""
    ensure_database_schema()
    with SessionLocal() as session:
        runs = session.scalars(
            select(WorkflowRun).order_by(WorkflowRun.created_at.desc())
        ).all()
        return [
            {
                "session_id": r.session_id,
                "session_name": r.session_name,
                "status": r.status,
                "current_step": r.current_step,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "updated_at": r.updated_at.isoformat() if r.updated_at else None,
            }
            for r in runs
        ]


def rename_session(session_id: str, session_name: str) -> dict[str, Any]:
    """Update the session_name for an existing run."""
    ensure_database_schema()
    with SessionLocal() as session:
        run = session.get(WorkflowRun, session_id)
        if run is None:
            raise ValueError(f"Unknown workflow session: {session_id}")
        run.session_name = session_name.strip() or None
        session.commit()
        return {
            "session_id": run.session_id,
            "session_name": run.session_name,
        }


def get_step_output(session_id: str, step_number: int) -> dict[str, Any]:
    """Return the persisted output for a specific step of an existing run."""
    ensure_database_schema()
    with SessionLocal() as session:
        record = session.scalar(
            select(StepOutput)
            .where(StepOutput.session_id == session_id, StepOutput.step_number == step_number)
            .limit(1)
        )
        if record is None:
            raise ValueError(
                f"No output for step {step_number} in session {session_id}"
            )
        return {"step_number": record.step_number, "step_name": record.step_name, "output": record.output_json}


def update_experiment_card(
    session_id: str,
    card_id: str,
    updates: dict[str, Any],
) -> dict[str, Any]:
    """Apply Zone B evidence updates to a single experiment card and persist."""
    from backend.app.nodes.step8_pdsa import update_experiment_card_evidence

    ensure_database_schema()
    with SessionLocal() as session:
        run = session.get(WorkflowRun, session_id)
        if run is None:
            raise ValueError(f"Unknown workflow session: {session_id}")

        state = dict(run.state_json)
        cards = state.get("experiment_cards")
        if not cards or not isinstance(cards, list):
            raise ValueError("Session has no experiment cards")

        card_index = None
        for idx, card in enumerate(cards):
            if card.get("id") == card_id:
                card_index = idx
                break

        if card_index is None:
            raise ValueError(f"Experiment card '{card_id}' not found in session {session_id}")

        cards[card_index] = update_experiment_card_evidence(cards[card_index], updates)
        state["experiment_cards"] = cards

        run.state_json = state
        session.commit()

        return cards[card_index]


def start_workflow_from_step(
    step_number: int,
    initial_state: dict[str, Any],
    *,
    session_id: str | None = None,
    session_name: str | None = None,
    llm_backend: str | None = None,
    pause_at_checkpoints: bool = True,
) -> BMIWorkflowState:
    """Begin execution at an arbitrary step, given pre-filled upstream state."""
    if step_number < 1 or step_number > _MAX_LOGICAL_STEP:
        raise ValueError(f"step_number must be between 1 and {_MAX_LOGICAL_STEP}")

    step_index = _LOGICAL_STEP_MAP[step_number]
    step_name = WORKFLOW_STEP_ORDER[step_index]
    settings = get_settings()

    state = BMIWorkflowState(
        session_id=session_id or str(uuid.uuid4()),
        current_step="start_from_step",
        input_type=initial_state.get("input_type", "text"),
        llm_backend=llm_backend or settings.llm_backend,
        **{k: v for k, v in initial_state.items() if k not in ("session_id", "current_step", "input_type", "llm_backend")},
    )
    if session_name:
        state["session_name"] = session_name

    validate_initial_state_for_step(step_name, state)
    ensure_database_schema()

    # Tell the orchestrator which steps are already done
    state["completed_steps"] = steps_completed_before(step_index)

    sid = str(state["session_id"])
    with SessionLocal() as session:
        if session.get(WorkflowRun, sid) is not None:
            raise ValueError(f"Workflow session already exists: {sid}")
        session.add(
            WorkflowRun(
                session_id=sid,
                session_name=session_name,
                input_type=str(state.get("input_type", "text")),
                status="in_progress",
                llm_backend=str(state["llm_backend"]),
                current_step=str(state["current_step"]),
                pending_checkpoint=None,
                voc_data=str(state.get("voc_data", "")),
                state_json=dict(state),
            )
        )
        session.commit()

    return _execute_orchestrated(sid, state, pause_at_checkpoints=pause_at_checkpoints)


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
            # Retry: re-execute the same step (completed_steps excludes it)
            retry_index = WORKFLOW_STEP_ORDER.index(checkpoint.after_step_name)
            state_to_resume["completed_steps"] = steps_completed_before(retry_index)
        else:
            state_to_resume = BMIWorkflowState(copy.deepcopy(checkpoint.state_after_json))
            if edit_state:
                for key, value in edit_state.items():
                    state_to_resume[key] = value
            validate_checkpoint_state(checkpoint.checkpoint_name, state_to_resume)
            # Approve/edit: advance past the checkpointed step
            advance_index = WORKFLOW_STEP_ORDER.index(checkpoint.after_step_name) + 1
            state_to_resume["completed_steps"] = steps_completed_before(advance_index)

        # Execute next steps within the same transaction so that checkpoint
        # resolution is rolled back if execution fails (atomicity fix).
        return _execute_orchestrated(
            session_id, state_to_resume, pause_at_checkpoints=True, db_session=session,
        )


def restart_from_step(
    session_id: str,
    step_number: int,
    *,
    edit_state: dict[str, Any] | None = None,
) -> BMIWorkflowState:
    """Rewind an existing session to *step_number* and re-execute from there.

    The caller may optionally supply *edit_state* to override fields before
    re-execution (e.g. the user edited the Business Model Canvas).
    """
    ensure_database_schema()
    if step_number < 1 or step_number > _MAX_LOGICAL_STEP:
        raise ValueError(f"step_number must be between 1 and {_MAX_LOGICAL_STEP}")

    step_index = _LOGICAL_STEP_MAP[step_number]

    with SessionLocal() as session:
        run = session.get(WorkflowRun, session_id)
        if run is None:
            raise ValueError(f"Unknown workflow session: {session_id}")

        # Build the state to resume from the persisted run state.
        current = BMIWorkflowState(copy.deepcopy(run.state_json))

        # Apply user edits if provided.
        if edit_state:
            for key, value in edit_state.items():
                current[key] = value

        # Rewind completed_steps so that the target step and all later steps
        # will be re-executed.
        current["completed_steps"] = steps_completed_before(step_index)

        # Invalidate any pending checkpoint so the run can proceed.
        run.status = "in_progress"
        run.pending_checkpoint = None

        return _execute_orchestrated(
            session_id, current, pause_at_checkpoints=True, db_session=session,
        )


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
                session_name=initial_state.get("session_name"),
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

    return _execute_orchestrated(session_id, initial_state, pause_at_checkpoints=True)


def _execute_orchestrated(
    session_id: str,
    state: BMIWorkflowState,
    *,
    pause_at_checkpoints: bool,
    db_session=None,
) -> BMIWorkflowState:
    """Run the workflow loop, optionally reusing a caller-provided DB session.

    When *db_session* is supplied the caller owns the transaction boundary,
    which lets ``resume_workflow`` and ``restart_from_step`` keep checkpoint
    resolution and step execution in a single atomic commit.
    """
    current_state = BMIWorkflowState(copy.deepcopy(state))
    if "completed_steps" not in current_state:
        current_state["completed_steps"] = []

    def _run_within(session):
        nonlocal current_state
        run = session.get(WorkflowRun, session_id)
        if run is None:
            raise ValueError(f"Unknown workflow session: {session_id}")

        while True:
            step_name = determine_next_step(current_state)
            if step_name == "__end__":
                break

            step_runner = WORKFLOW_STEP_RUNNERS[step_name]
            state_before = BMIWorkflowState(copy.deepcopy(current_state))
            current_state = step_runner(BMIWorkflowState(copy.deepcopy(current_state)))
            current_state["completed_steps"] = list(state_before.get("completed_steps", [])) + [step_name]

            step_number = WORKFLOW_STEP_ORDER.index(step_name) + 1
            session.add(
                StepOutput(
                    session_id=session_id,
                    step_number=step_number,
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

    if db_session is not None:
        return _run_within(db_session)

    with SessionLocal() as session:
        return _run_within(session)


def _persist_completed_run(final_state: BMIWorkflowState) -> None:
    session_id = str(final_state["session_id"])
    with SessionLocal() as session:
        existing_run = session.get(WorkflowRun, session_id)
        if existing_run is not None:
            raise ValueError(f"Workflow session already exists: {session_id}")
        session.add(
            WorkflowRun(
                session_id=session_id,
                session_name=final_state.get("session_name"),
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