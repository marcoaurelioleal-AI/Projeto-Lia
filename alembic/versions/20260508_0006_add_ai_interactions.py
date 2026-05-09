"""add ai interactions

Revision ID: 20260508_0006
Revises: 20260508_0005
Create Date: 2026-05-08
"""

from __future__ import annotations

from collections.abc import Callable

import sqlalchemy as sa
from alembic import op

revision = "20260508_0006"
down_revision = "20260508_0005"
branch_labels = None
depends_on = None


def _create_if_missing(table_name: str, create: Callable[[], None]) -> None:
    inspector = sa.inspect(op.get_bind())
    if not inspector.has_table(table_name):
        create()


def upgrade() -> None:
    _create_if_missing(
        "ai_interactions",
        lambda: op.create_table(
            "ai_interactions",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("question", sa.Text(), nullable=False),
            sa.Column("answer", sa.Text(), nullable=False),
            sa.Column("response_mode", sa.String(length=30), nullable=False),
            sa.Column("ai_mode", sa.String(length=30), nullable=False),
            sa.Column("sources_json", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("latency_ms", sa.Integer(), nullable=False),
        ),
    )
    op.create_index(op.f("ix_ai_interactions_user_id"), "ai_interactions", ["user_id"], unique=False, if_not_exists=True)
    op.create_index(
        op.f("ix_ai_interactions_response_mode"),
        "ai_interactions",
        ["response_mode"],
        unique=False,
        if_not_exists=True,
    )
    op.create_index(op.f("ix_ai_interactions_ai_mode"), "ai_interactions", ["ai_mode"], unique=False, if_not_exists=True)
    op.create_index(op.f("ix_ai_interactions_created_at"), "ai_interactions", ["created_at"], unique=False, if_not_exists=True)


def downgrade() -> None:
    op.drop_table("ai_interactions", if_exists=True)
