"""create signal repository tables

Revision ID: 20260425_0003
Revises: 20260415_0002
Create Date: 2026-04-25 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = "20260425_0003"
down_revision = "20260415_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if "signal_reports" not in existing_tables:
        op.create_table(
            "signal_reports",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("bu", sa.String(), nullable=False),
            sa.Column("survey_source", sa.String(), nullable=False),
            sa.Column("title", sa.String(), nullable=False),
            sa.Column("report_date", sa.String(), nullable=True),
            sa.Column("input_stats", sa.JSON(), nullable=False),
            sa.Column("reinforcement_map", sa.JSON(), nullable=True),
            sa.Column("source_file", sa.String(), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("source_file"),
        )
        op.create_index("ix_signal_reports_bu", "signal_reports", ["bu"])
        op.create_index("ix_signal_reports_survey_source", "signal_reports", ["survey_source"])

    if "signal_records" not in existing_tables:
        op.create_table(
            "signal_records",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("report_id", sa.Integer(), nullable=False),
            sa.Column("signal_id", sa.String(), nullable=False),
            sa.Column("signal_title", sa.String(), nullable=False),
            sa.Column("bu", sa.String(), nullable=False),
            sa.Column("survey_source", sa.String(), nullable=False),
            sa.Column("signal_zone", sa.String(), nullable=False),
            sa.Column("classification", sa.String(), nullable=True),
            sa.Column("action_tier", sa.String(), nullable=True),
            sa.Column("priority_score", sa.Integer(), nullable=True),
            sa.Column("observable_behavior", sa.Text(), nullable=True),
            sa.Column("full_analysis", sa.JSON(), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(["report_id"], ["signal_reports.id"]),
            sa.UniqueConstraint("report_id", "signal_id", name="uq_signal_report_signal_id"),
        )
        op.create_index("ix_signal_records_report_id", "signal_records", ["report_id"])
        op.create_index("ix_signal_records_bu", "signal_records", ["bu"])
        op.create_index("ix_signal_records_survey_source", "signal_records", ["survey_source"])


def downgrade() -> None:
    op.drop_table("signal_records")
    op.drop_table("signal_reports")
