"""create checkpoint runtime tables

Revision ID: 20260322_0001
Revises: None
Create Date: 2026-03-22 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = "20260322_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if "runs" not in existing_tables:
        op.create_table(
            "runs",
            sa.Column("session_id", sa.String(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("input_type", sa.String(), nullable=False),
            sa.Column("status", sa.String(), nullable=False),
            sa.Column("llm_backend", sa.String(), nullable=False),
            sa.Column("current_step", sa.String(), nullable=False),
            sa.Column("pending_checkpoint", sa.String(), nullable=True),
            sa.Column("voc_data", sa.Text(), nullable=False),
            sa.Column("state_json", sa.JSON(), nullable=False),
            sa.PrimaryKeyConstraint("session_id"),
        )

    if "step_outputs" not in existing_tables:
        op.create_table(
            "step_outputs",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("session_id", sa.String(), nullable=False),
            sa.Column("step_number", sa.Integer(), nullable=False),
            sa.Column("step_name", sa.String(), nullable=False),
            sa.Column("input_json", sa.JSON(), nullable=False),
            sa.Column("output_json", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(["session_id"], ["runs.session_id"]),
            sa.PrimaryKeyConstraint("id"),
        )

    if "checkpoints" not in existing_tables:
        op.create_table(
            "checkpoints",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("session_id", sa.String(), nullable=False),
            sa.Column("checkpoint_name", sa.String(), nullable=False),
            sa.Column("after_step_name", sa.String(), nullable=False),
            sa.Column("step_number", sa.Integer(), nullable=False),
            sa.Column("decision", sa.String(), nullable=True),
            sa.Column("edit_json", sa.JSON(), nullable=True),
            sa.Column("state_before_json", sa.JSON(), nullable=False),
            sa.Column("state_after_json", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["session_id"], ["runs.session_id"]),
            sa.PrimaryKeyConstraint("id"),
        )

    if "step_outputs" in inspector.get_table_names():
        step_output_indexes = {index["name"] for index in inspector.get_indexes("step_outputs")}
        if "ix_step_outputs_session_id" not in step_output_indexes:
            op.create_index("ix_step_outputs_session_id", "step_outputs", ["session_id"], unique=False)

    if "checkpoints" in inspector.get_table_names():
        checkpoint_indexes = {index["name"] for index in inspector.get_indexes("checkpoints")}
        if "ix_checkpoints_session_id" not in checkpoint_indexes:
            op.create_index("ix_checkpoints_session_id", "checkpoints", ["session_id"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if "checkpoints" in existing_tables:
        checkpoint_indexes = {index["name"] for index in inspector.get_indexes("checkpoints")}
        if "ix_checkpoints_session_id" in checkpoint_indexes:
            op.drop_index("ix_checkpoints_session_id", table_name="checkpoints")
        op.drop_table("checkpoints")

    if "step_outputs" in existing_tables:
        step_output_indexes = {index["name"] for index in inspector.get_indexes("step_outputs")}
        if "ix_step_outputs_session_id" in step_output_indexes:
            op.drop_index("ix_step_outputs_session_id", table_name="step_outputs")
        op.drop_table("step_outputs")

    if "runs" in existing_tables:
        op.drop_table("runs")