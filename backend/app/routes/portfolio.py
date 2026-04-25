"""Portfolio API endpoints for the Executive Dashboard."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.app.db.session import DatabaseSchemaNotReadyError, SessionLocal
from backend.app.services import portfolio_service

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


class UpdatePortfolioRequest(BaseModel):
    initiative_name: str | None = None
    expected_revenue: str | None = None
    testing_cost: str | None = None
    risk_score_override: float | None = None
    return_score_override: float | None = None
    notes: str | None = None


@router.get("")
def list_portfolio() -> list[dict[str, Any]]:
    """Return all portfolio entries with computed risk/return scores."""
    try:
        with SessionLocal() as db:
            return portfolio_service.get_portfolio_entries(db)
    except DatabaseSchemaNotReadyError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@router.get("/{session_id}/detail")
def get_portfolio_detail(session_id: str) -> dict[str, Any]:
    """Return deep detail for a single initiative (hypothesis log, experiments, etc.)."""
    try:
        with SessionLocal() as db:
            detail = portfolio_service.get_portfolio_detail(db, session_id)
            if detail is None:
                raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
            return detail
    except DatabaseSchemaNotReadyError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@router.patch("/{session_id}")
def update_portfolio(session_id: str, body: UpdatePortfolioRequest) -> dict[str, str]:
    """Update portfolio metadata for a session (initiative name, revenue, cost, overrides)."""
    try:
        with SessionLocal() as db:
            from backend.app.db.models import WorkflowRun
            from sqlalchemy import select

            run = db.scalar(
                select(WorkflowRun).where(WorkflowRun.session_id == session_id)
            )
            if not run:
                raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

            existing = run.portfolio_json or {}
            updates = body.model_dump(exclude_none=True)
            existing.update(updates)
            run.portfolio_json = existing

            # SQLAlchemy needs to detect the JSON mutation
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(run, "portfolio_json")

            db.commit()
            return {"status": "ok", "session_id": session_id}
    except DatabaseSchemaNotReadyError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
