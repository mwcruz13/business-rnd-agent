from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import func
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column


class Base(DeclarativeBase):
    pass


class WorkflowRun(Base):
    __tablename__ = "runs"

    session_id: Mapped[str] = mapped_column(String, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    input_type: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    llm_backend: Mapped[str] = mapped_column(String, nullable=False)
    current_step: Mapped[str] = mapped_column(String, nullable=False)
    pending_checkpoint: Mapped[str | None] = mapped_column(String, nullable=True)
    voc_data: Mapped[str] = mapped_column(Text, nullable=False)
    state_json: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)


class StepOutput(Base):
    __tablename__ = "step_outputs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("runs.session_id"), nullable=False, index=True)
    step_number: Mapped[int] = mapped_column(Integer, nullable=False)
    step_name: Mapped[str] = mapped_column(String, nullable=False)
    input_json: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    output_json: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CheckpointRecord(Base):
    __tablename__ = "checkpoints"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("runs.session_id"), nullable=False, index=True)
    checkpoint_name: Mapped[str] = mapped_column(String, nullable=False)
    after_step_name: Mapped[str] = mapped_column(String, nullable=False)
    step_number: Mapped[int] = mapped_column(Integer, nullable=False)
    decision: Mapped[str | None] = mapped_column(String, nullable=True)
    edit_json: Mapped[dict[str, object] | None] = mapped_column(JSON, nullable=True)
    state_before_json: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    state_after_json: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
