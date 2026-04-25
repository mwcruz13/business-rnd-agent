import tempfile
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from backend.app.config import get_settings
from backend.app.db.session import DatabaseSchemaNotReadyError
from backend.app.routes.signals import router as signals_router
from backend.app.workflow import get_run_state
from backend.app.workflow import get_step_output
from backend.app.workflow import list_sessions
from backend.app.workflow import rename_session
from backend.app.workflow import restart_from_step
from backend.app.workflow import update_experiment_card
from backend.app.workflow import resume_workflow
from backend.app.workflow import run_workflow_from_csv_text
from backend.app.workflow import run_workflow_from_path, run_workflow_from_voc_data
from backend.app.workflow import run_workflow_from_signal
from backend.app.workflow import start_workflow_from_step


settings = get_settings()
app = FastAPI(title="BMI Consultant Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://localhost:8080"],
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["Content-Type"],
)

app.include_router(signals_router)


class RunWorkflowRequest(BaseModel):
    input_text: str | None = None
    input_path: str | None = None
    input_format: str | None = None
    session_id: str | None = None
    session_name: str | None = None
    llm_backend: str | None = None
    pause_at_checkpoints: bool = True


class ResumeWorkflowRequest(BaseModel):
    decision: str
    edit_state: dict[str, Any] | None = None


class RestartFromStepRequest(BaseModel):
    step_number: int
    edit_state: dict[str, Any] | None = None


class UpdateExperimentCardRequest(BaseModel):
    updates: dict[str, Any]


class StartFromStepRequest(BaseModel):
    step_number: int
    initial_state: dict[str, Any]
    session_id: str | None = None
    session_name: str | None = None
    llm_backend: str | None = None
    pause_at_checkpoints: bool = True


class RunFromSignalRequest(BaseModel):
    signal_id: int
    session_name: str | None = None
    llm_backend: str | None = None
    pause_at_checkpoints: bool = True


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "llm_backend": settings.llm_backend}


class RenameSessionRequest(BaseModel):
    session_name: str


@app.get("/sessions")
def list_all_sessions() -> list[dict[str, Any]]:
    try:
        return list_sessions()
    except DatabaseSchemaNotReadyError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@app.patch("/runs/{session_id}/name")
def rename_workflow_session(session_id: str, request: RenameSessionRequest) -> dict[str, Any]:
    try:
        return rename_session(session_id, request.session_name)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except DatabaseSchemaNotReadyError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@app.post("/runs")
def run_workflow(request: RunWorkflowRequest) -> dict[str, Any]:
    if bool(request.input_text) == bool(request.input_path):
        raise HTTPException(status_code=422, detail="Provide exactly one of input_text or input_path")

    try:
        if request.input_text is not None:
            if request.input_format == "csv":
                result = run_workflow_from_csv_text(
                    request.input_text,
                    session_id=request.session_id,
                    session_name=request.session_name,
                    llm_backend=request.llm_backend,
                    pause_at_checkpoints=request.pause_at_checkpoints,
                )
            else:
                result = run_workflow_from_voc_data(
                    request.input_text,
                    session_id=request.session_id,
                    session_name=request.session_name,
                    llm_backend=request.llm_backend,
                    input_type="text",
                    pause_at_checkpoints=request.pause_at_checkpoints,
                )
        else:
            result = run_workflow_from_path(
                request.input_path or "",
                session_id=request.session_id,
                session_name=request.session_name,
                llm_backend=request.llm_backend,
                pause_at_checkpoints=request.pause_at_checkpoints,
            )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except DatabaseSchemaNotReadyError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error

    return dict(result)


@app.get("/runs/{session_id}")
def get_workflow_run(session_id: str) -> dict[str, Any]:
    try:
        return dict(get_run_state(session_id))
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except DatabaseSchemaNotReadyError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@app.post("/runs/{session_id}/resume")
def resume_workflow_run(session_id: str, request: ResumeWorkflowRequest) -> dict[str, Any]:
    try:
        result = resume_workflow(session_id, decision=request.decision, edit_state=request.edit_state)
    except ValueError as error:
        message = str(error)
        if message.startswith("Unknown workflow session"):
            raise HTTPException(status_code=404, detail=message) from error
        raise HTTPException(status_code=422, detail=message) from error
    except DatabaseSchemaNotReadyError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    return dict(result)


@app.post("/runs/{session_id}/restart")
def restart_workflow_from_step(session_id: str, request: RestartFromStepRequest) -> dict[str, Any]:
    try:
        result = restart_from_step(
            session_id,
            request.step_number,
            edit_state=request.edit_state,
        )
    except ValueError as error:
        message = str(error)
        if message.startswith("Unknown workflow session"):
            raise HTTPException(status_code=404, detail=message) from error
        raise HTTPException(status_code=422, detail=message) from error
    except DatabaseSchemaNotReadyError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    return dict(result)


@app.patch("/runs/{session_id}/experiment-cards/{card_id}")
def patch_experiment_card(
    session_id: str, card_id: str, request: UpdateExperimentCardRequest,
) -> dict[str, Any]:
    try:
        return update_experiment_card(session_id, card_id, request.updates)
    except ValueError as error:
        message = str(error)
        if message.startswith("Unknown workflow session"):
            raise HTTPException(status_code=404, detail=message) from error
        if "not found" in message:
            raise HTTPException(status_code=404, detail=message) from error
        raise HTTPException(status_code=422, detail=message) from error
    except DatabaseSchemaNotReadyError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@app.post("/runs/start-from-step")
def start_from_step(request: StartFromStepRequest) -> dict[str, Any]:
    try:
        result = start_workflow_from_step(
            request.step_number,
            request.initial_state,
            session_id=request.session_id,
            session_name=request.session_name,
            llm_backend=request.llm_backend,
            pause_at_checkpoints=request.pause_at_checkpoints,
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except DatabaseSchemaNotReadyError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    return dict(result)


@app.post("/runs/from-signal")
def run_from_signal(request: RunFromSignalRequest) -> dict[str, Any]:
    try:
        result = run_workflow_from_signal(
            request.signal_id,
            session_name=request.session_name,
            llm_backend=request.llm_backend,
            pause_at_checkpoints=request.pause_at_checkpoints,
        )
    except ValueError as error:
        message = str(error)
        if "not found" in message:
            raise HTTPException(status_code=404, detail=message) from error
        raise HTTPException(status_code=422, detail=message) from error
    except DatabaseSchemaNotReadyError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    return dict(result)


@app.get("/runs/{session_id}/step/{step_number}")
def get_step(session_id: str, step_number: int) -> dict[str, Any]:
    try:
        return get_step_output(session_id, step_number)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except DatabaseSchemaNotReadyError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@app.get("/runs/{session_id}/export/md")
def export_markdown(session_id: str):
    """Download the workflow report as a Markdown file."""
    from backend.app.db.models import WorkflowRun
    from backend.app.db.session import SessionLocal
    from backend.cli.export_report import build_report

    sess = SessionLocal()
    try:
        run = sess.query(WorkflowRun).filter_by(session_id=session_id).first()
        if not run:
            raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")
        report = build_report(run)
        tmp = tempfile.NamedTemporaryFile(suffix=".md", delete=False, mode="w", encoding="utf-8")
        tmp.write(report)
        tmp.close()
        filename = f"{session_id[:12]}_report.md"
        return FileResponse(tmp.name, media_type="text/markdown", filename=filename)
    except DatabaseSchemaNotReadyError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    finally:
        sess.close()


@app.get("/runs/{session_id}/export/pptx")
def export_pptx(session_id: str):
    """Download the workflow report as a PowerPoint file."""
    from backend.app.db.models import WorkflowRun
    from backend.app.db.session import SessionLocal
    from backend.cli.generate_report_pptx import generate_report_pptx

    TEMPLATE = "hpe_dark_template.pptx"
    if not Path(TEMPLATE).exists():
        raise HTTPException(
            status_code=500,
            detail="PowerPoint template not found. Copy the HPE template to the container.",
        )

    sess = SessionLocal()
    try:
        run = sess.query(WorkflowRun).filter_by(session_id=session_id).first()
        if not run:
            raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")
        state = run.state_json if isinstance(run.state_json, dict) else {}
        meta = {
            "session_id": run.session_id,
            "session_name": run.session_name,
            "created": run.created_at.strftime("%Y-%m-%d %H:%M UTC") if run.created_at else "N/A",
            "status": run.status,
            "llm_backend": run.llm_backend,
            "input_type": run.input_type,
        }
        tmp = tempfile.NamedTemporaryFile(suffix=".pptx", delete=False)
        tmp.close()
        generate_report_pptx(state, meta, template_path=TEMPLATE, output_path=tmp.name)
        filename = f"{session_id[:12]}_report.pptx"
        return FileResponse(
            tmp.name,
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            filename=filename,
        )
    except DatabaseSchemaNotReadyError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    finally:
        sess.close()
