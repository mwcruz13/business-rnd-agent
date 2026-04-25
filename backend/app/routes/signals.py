"""Signal repository API endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from backend.app.db.session import DatabaseSchemaNotReadyError
from backend.app.services import signal_repository as repo

router = APIRouter(prefix="/signals", tags=["signals"])


@router.get("/summary")
def signal_summary() -> list[dict[str, Any]]:
    try:
        return repo.get_bu_summary()
    except DatabaseSchemaNotReadyError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@router.get("/reports")
def list_signal_reports() -> list[dict[str, Any]]:
    try:
        return repo.list_reports()
    except DatabaseSchemaNotReadyError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@router.get("/reports/{report_id}")
def get_signal_report(report_id: int) -> dict[str, Any]:
    try:
        return repo.get_report(report_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except DatabaseSchemaNotReadyError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@router.get("")
def list_signals(
    bu: str | None = Query(None),
    survey_source: str | None = Query(None),
    classification: str | None = Query(None),
    action_tier: str | None = Query(None),
) -> list[dict[str, Any]]:
    try:
        return repo.list_signals(
            bu=bu,
            survey_source=survey_source,
            classification=classification,
            action_tier=action_tier,
        )
    except DatabaseSchemaNotReadyError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@router.get("/{record_id}")
def get_signal(record_id: int) -> dict[str, Any]:
    try:
        return repo.get_signal(record_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except DatabaseSchemaNotReadyError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
