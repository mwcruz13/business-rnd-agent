from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from backend.app.config import get_settings
from backend.app.db.session import DatabaseSchemaNotReadyError
from backend.app.workflow import get_run_state
from backend.app.workflow import resume_workflow
from backend.app.workflow import run_workflow_from_csv_text
from backend.app.workflow import run_workflow_from_path, run_workflow_from_voc_data


settings = get_settings()
app = FastAPI(title="BMI Consultant Backend", version="0.1.0")


class RunWorkflowRequest(BaseModel):
    input_text: str | None = None
    input_path: str | None = None
    input_format: str | None = None
    session_id: str | None = None
    llm_backend: str | None = None
    pause_at_checkpoints: bool = True


class ResumeWorkflowRequest(BaseModel):
    decision: str
    edit_state: dict[str, Any] | None = None


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "llm_backend": settings.llm_backend}


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
                    llm_backend=request.llm_backend,
                    pause_at_checkpoints=request.pause_at_checkpoints,
                )
            else:
                result = run_workflow_from_voc_data(
                    request.input_text,
                    session_id=request.session_id,
                    llm_backend=request.llm_backend,
                    input_type="text",
                    pause_at_checkpoints=request.pause_at_checkpoints,
                )
        else:
            result = run_workflow_from_path(
                request.input_path or "",
                session_id=request.session_id,
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
