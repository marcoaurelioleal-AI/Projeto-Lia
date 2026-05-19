"""add ai knowledge chunks and feedback

Revision ID: 20260519_0009
Revises: 20260516_0008
Create Date: 2026-05-19
"""

from __future__ import annotations

from collections.abc import Callable

import sqlalchemy as sa
from alembic import op

revision = "20260519_0009"
down_revision = "20260516_0008"
branch_labels = None
depends_on = None


def _create_if_missing(table_name: str, create: Callable[[], None]) -> None:
    inspector = sa.inspect(op.get_bind())
    if not inspector.has_table(table_name):
        create()


def _has_column(table_name: str, column_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    if not inspector.has_table(table_name):
        return False
    return any(column["name"] == column_name for column in inspector.get_columns(table_name))


def _add_column_if_missing(table_name: str, column: sa.Column) -> None:
    if not _has_column(table_name, column.name):
        op.add_column(table_name, column)


def upgrade() -> None:
    _create_if_missing(
        "ai_knowledge_chunks",
        lambda: op.create_table(
            "ai_knowledge_chunks",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("chunk_key", sa.String(length=160), nullable=False),
            sa.Column("source_type", sa.String(length=30), nullable=False),
            sa.Column("manual_id", sa.Integer(), sa.ForeignKey("manuals.id"), nullable=False),
            sa.Column("section_id", sa.Integer(), sa.ForeignKey("manual_sections.id"), nullable=True),
            sa.Column("unit", sa.String(length=80), nullable=False),
            sa.Column("title", sa.String(length=180), nullable=False),
            sa.Column("section_title", sa.String(length=160), nullable=True),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("content_hash", sa.String(length=64), nullable=False),
            sa.Column("embedding_json", sa.JSON(), nullable=False),
            sa.Column("active", sa.Boolean(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.UniqueConstraint("chunk_key", name="uq_ai_knowledge_chunks_key"),
        ),
    )
    op.create_index(op.f("ix_ai_knowledge_chunks_chunk_key"), "ai_knowledge_chunks", ["chunk_key"], unique=True, if_not_exists=True)
    op.create_index(op.f("ix_ai_knowledge_chunks_source_type"), "ai_knowledge_chunks", ["source_type"], unique=False, if_not_exists=True)
    op.create_index(op.f("ix_ai_knowledge_chunks_manual_id"), "ai_knowledge_chunks", ["manual_id"], unique=False, if_not_exists=True)
    op.create_index(op.f("ix_ai_knowledge_chunks_section_id"), "ai_knowledge_chunks", ["section_id"], unique=False, if_not_exists=True)
    op.create_index(op.f("ix_ai_knowledge_chunks_unit"), "ai_knowledge_chunks", ["unit"], unique=False, if_not_exists=True)
    op.create_index(op.f("ix_ai_knowledge_chunks_content_hash"), "ai_knowledge_chunks", ["content_hash"], unique=False, if_not_exists=True)
    op.create_index(op.f("ix_ai_knowledge_chunks_active"), "ai_knowledge_chunks", ["active"], unique=False, if_not_exists=True)

    _add_column_if_missing(
        "ai_interactions",
        sa.Column("needs_manager_confirmation", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    _add_column_if_missing("ai_interactions", sa.Column("feedback_rating", sa.String(length=20), nullable=True))
    _add_column_if_missing("ai_interactions", sa.Column("feedback_comment", sa.Text(), nullable=True))
    _add_column_if_missing("ai_interactions", sa.Column("feedback_created_at", sa.DateTime(), nullable=True))
    op.create_index(
        op.f("ix_ai_interactions_needs_manager_confirmation"),
        "ai_interactions",
        ["needs_manager_confirmation"],
        unique=False,
        if_not_exists=True,
    )
    op.create_index(
        op.f("ix_ai_interactions_feedback_rating"),
        "ai_interactions",
        ["feedback_rating"],
        unique=False,
        if_not_exists=True,
    )


def downgrade() -> None:
    op.drop_table("ai_knowledge_chunks", if_exists=True)
    for column_name in (
        "feedback_created_at",
        "feedback_comment",
        "feedback_rating",
        "needs_manager_confirmation",
    ):
        if _has_column("ai_interactions", column_name):
            op.drop_column("ai_interactions", column_name)
