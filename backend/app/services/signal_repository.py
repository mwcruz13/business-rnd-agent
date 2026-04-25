"""Signal repository service — query and upsert signal reports and records."""

from __future__ import annotations

from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.db.models import SignalRecord, SignalReport
from backend.app.db.session import SessionLocal


def _get_session() -> Session:
    return SessionLocal()


# ---------------------------------------------------------------------------
# Report operations
# ---------------------------------------------------------------------------


def upsert_report(
    bu: str,
    survey_source: str,
    title: str,
    input_stats: dict[str, Any],
    source_file: str,
    report_date: str | None = None,
    reinforcement_map: dict[str, Any] | None = None,
) -> SignalReport:
    sess = _get_session()
    try:
        existing = sess.query(SignalReport).filter_by(source_file=source_file).first()
        if existing:
            existing.bu = bu
            existing.survey_source = survey_source
            existing.title = title
            existing.report_date = report_date
            existing.input_stats = input_stats
            existing.reinforcement_map = reinforcement_map
            sess.commit()
            sess.refresh(existing)
            return existing
        report = SignalReport(
            bu=bu,
            survey_source=survey_source,
            title=title,
            report_date=report_date,
            input_stats=input_stats,
            reinforcement_map=reinforcement_map,
            source_file=source_file,
        )
        sess.add(report)
        sess.commit()
        sess.refresh(report)
        return report
    finally:
        sess.close()


def get_report(report_id: int) -> dict[str, Any]:
    sess = _get_session()
    try:
        report = sess.query(SignalReport).filter_by(id=report_id).first()
        if not report:
            raise ValueError(f"Signal report {report_id} not found")
        return _report_to_dict(report)
    finally:
        sess.close()


def list_reports() -> list[dict[str, Any]]:
    sess = _get_session()
    try:
        reports = sess.query(SignalReport).order_by(SignalReport.bu, SignalReport.survey_source).all()
        return [_report_to_dict(r) for r in reports]
    finally:
        sess.close()


# ---------------------------------------------------------------------------
# Signal record operations
# ---------------------------------------------------------------------------


def upsert_signal(
    report_id: int,
    signal_id: int | str,
    signal_title: str,
    bu: str,
    survey_source: str,
    signal_zone: str,
    full_analysis: dict[str, Any],
    classification: str | None = None,
    action_tier: str | None = None,
    priority_score: int | None = None,
    observable_behavior: str | None = None,
) -> SignalRecord:
    sess = _get_session()
    try:
        existing = (
            sess.query(SignalRecord)
            .filter_by(bu=bu, survey_source=survey_source, signal_id=signal_id)
            .first()
        )
        if existing:
            existing.report_id = report_id
            existing.signal_title = signal_title
            existing.signal_zone = signal_zone
            existing.classification = classification
            existing.action_tier = action_tier
            existing.priority_score = priority_score
            existing.observable_behavior = observable_behavior
            existing.full_analysis = full_analysis
            sess.commit()
            sess.refresh(existing)
            return existing
        record = SignalRecord(
            report_id=report_id,
            signal_id=signal_id,
            signal_title=signal_title,
            bu=bu,
            survey_source=survey_source,
            signal_zone=signal_zone,
            classification=classification,
            action_tier=action_tier,
            priority_score=priority_score,
            observable_behavior=observable_behavior,
            full_analysis=full_analysis,
        )
        sess.add(record)
        sess.commit()
        sess.refresh(record)
        return record
    finally:
        sess.close()


def get_signal(record_id: int) -> dict[str, Any]:
    sess = _get_session()
    try:
        record = sess.query(SignalRecord).filter_by(id=record_id).first()
        if not record:
            raise ValueError(f"Signal record {record_id} not found")
        return _record_to_dict(record)
    finally:
        sess.close()


def list_signals(
    bu: str | None = None,
    survey_source: str | None = None,
    classification: str | None = None,
    action_tier: str | None = None,
) -> list[dict[str, Any]]:
    sess = _get_session()
    try:
        query = sess.query(SignalRecord)
        if bu:
            query = query.filter(SignalRecord.bu == bu)
        if survey_source:
            query = query.filter(SignalRecord.survey_source == survey_source)
        if classification:
            query = query.filter(SignalRecord.classification == classification)
        if action_tier:
            query = query.filter(SignalRecord.action_tier == action_tier)
        records = query.order_by(SignalRecord.bu, SignalRecord.signal_id).all()
        return [_record_to_dict(r) for r in records]
    finally:
        sess.close()


def get_bu_summary() -> list[dict[str, Any]]:
    sess = _get_session()
    try:
        rows = (
            sess.query(
                SignalRecord.bu,
                SignalRecord.survey_source,
                func.count(SignalRecord.id).label("signal_count"),
            )
            .group_by(SignalRecord.bu, SignalRecord.survey_source)
            .order_by(SignalRecord.bu, SignalRecord.survey_source)
            .all()
        )
        return [
            {"bu": row.bu, "survey_source": row.survey_source, "signal_count": row.signal_count}
            for row in rows
        ]
    finally:
        sess.close()


# ---------------------------------------------------------------------------
# Serialisation helpers
# ---------------------------------------------------------------------------


def _report_to_dict(report: SignalReport) -> dict[str, Any]:
    return {
        "id": report.id,
        "bu": report.bu,
        "survey_source": report.survey_source,
        "title": report.title,
        "report_date": report.report_date,
        "input_stats": report.input_stats,
        "reinforcement_map": report.reinforcement_map,
        "source_file": report.source_file,
        "created_at": report.created_at.isoformat() if report.created_at else None,
    }


def _record_to_dict(record: SignalRecord) -> dict[str, Any]:
    return {
        "id": record.id,
        "report_id": record.report_id,
        "signal_id": record.signal_id,
        "signal_title": record.signal_title,
        "bu": record.bu,
        "survey_source": record.survey_source,
        "signal_zone": record.signal_zone,
        "classification": record.classification,
        "action_tier": record.action_tier,
        "priority_score": record.priority_score,
        "observable_behavior": record.observable_behavior,
        "full_analysis": record.full_analysis,
        "created_at": record.created_at.isoformat() if record.created_at else None,
    }
