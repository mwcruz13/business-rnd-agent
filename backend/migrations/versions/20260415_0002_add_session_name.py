"""add session_name to runs

Revision ID: 20260415_0002
Revises: 20260322_0001
Create Date: 2026-04-15 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = "20260415_0002"
down_revision = "20260322_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_columns = {col["name"] for col in inspector.get_columns("runs")}

    if "session_name" not in existing_columns:
        op.add_column("runs", sa.Column("session_name", sa.String(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_columns = {col["name"] for col in inspector.get_columns("runs")}

    if "session_name" in existing_columns:
        op.drop_column("runs", "session_name")
