"""initial schema

Revision ID: 20260508_0001
Revises:
Create Date: 2026-05-08
"""

from __future__ import annotations

from collections.abc import Callable

import sqlalchemy as sa
from alembic import op

revision = "20260508_0001"
down_revision = None
branch_labels = None
depends_on = None


def _create_if_missing(table_name: str, create: Callable[[], None]) -> None:
    inspector = sa.inspect(op.get_bind())
    if not inspector.has_table(table_name):
        create()


def upgrade() -> None:
    _create_if_missing(
        "users",
        lambda: op.create_table(
            "users",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("username", sa.String(length=80), nullable=False),
            sa.Column("name", sa.String(length=120), nullable=False),
            sa.Column("role", sa.String(length=30), nullable=False),
            sa.Column("password_hash", sa.String(length=255), nullable=False),
            sa.Column("active", sa.Boolean(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.UniqueConstraint("username"),
        ),
    )
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True, if_not_exists=True)

    _create_if_missing(
        "manuals",
        lambda: op.create_table(
            "manuals",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("unit", sa.String(length=80), nullable=False),
            sa.Column("title", sa.String(length=180), nullable=False),
            sa.Column("temperature", sa.String(length=120), nullable=False),
            sa.Column("time_standard", sa.String(length=120), nullable=False),
            sa.Column("critical_point", sa.String(length=180), nullable=False),
            sa.Column("tip", sa.Text(), nullable=False),
            sa.UniqueConstraint("unit"),
        ),
    )
    op.create_index(op.f("ix_manuals_unit"), "manuals", ["unit"], unique=True, if_not_exists=True)

    _create_if_missing(
        "manual_sections",
        lambda: op.create_table(
            "manual_sections",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("manual_id", sa.Integer(), sa.ForeignKey("manuals.id"), nullable=False),
            sa.Column("title", sa.String(length=160), nullable=False),
            sa.Column("position", sa.Integer(), nullable=False),
        ),
    )

    _create_if_missing(
        "manual_steps",
        lambda: op.create_table(
            "manual_steps",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("section_id", sa.Integer(), sa.ForeignKey("manual_sections.id"), nullable=False),
            sa.Column("text", sa.Text(), nullable=False),
            sa.Column("position", sa.Integer(), nullable=False),
        ),
    )

    _create_if_missing(
        "checklist_templates",
        lambda: op.create_table(
            "checklist_templates",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("title", sa.String(length=160), nullable=False),
            sa.Column("category", sa.String(length=80), nullable=False),
            sa.Column("store", sa.String(length=80), nullable=False),
            sa.UniqueConstraint("title"),
        ),
    )

    _create_if_missing(
        "checklist_template_items",
        lambda: op.create_table(
            "checklist_template_items",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("template_id", sa.Integer(), sa.ForeignKey("checklist_templates.id"), nullable=False),
            sa.Column("section", sa.String(length=120), nullable=False),
            sa.Column("text", sa.Text(), nullable=False),
            sa.Column("position", sa.Integer(), nullable=False),
        ),
    )

    _create_if_missing(
        "checklist_runs",
        lambda: op.create_table(
            "checklist_runs",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("template_id", sa.Integer(), sa.ForeignKey("checklist_templates.id"), nullable=False),
            sa.Column("run_date", sa.Date(), nullable=False),
            sa.Column("store", sa.String(length=80), nullable=False),
            sa.Column("assigned_to_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("closing_note", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.UniqueConstraint("template_id", "run_date", "store", name="uq_template_date_store"),
        ),
    )
    op.create_index(op.f("ix_checklist_runs_run_date"), "checklist_runs", ["run_date"], unique=False, if_not_exists=True)

    _create_if_missing(
        "checklist_run_items",
        lambda: op.create_table(
            "checklist_run_items",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("run_id", sa.Integer(), sa.ForeignKey("checklist_runs.id"), nullable=False),
            sa.Column("template_item_id", sa.Integer(), sa.ForeignKey("checklist_template_items.id"), nullable=False),
            sa.Column("done", sa.Boolean(), nullable=False),
            sa.Column("completed_at", sa.DateTime(), nullable=True),
            sa.Column("completed_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        ),
    )

    _create_if_missing(
        "ai_chat_sessions",
        lambda: op.create_table(
            "ai_chat_sessions",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("store", sa.String(length=80), nullable=False),
            sa.Column("unit", sa.String(length=80), nullable=True),
            sa.Column("title", sa.String(length=160), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
        ),
    )
    op.create_index(op.f("ix_ai_chat_sessions_user_id"), "ai_chat_sessions", ["user_id"], unique=False, if_not_exists=True)

    _create_if_missing(
        "ai_chat_logs",
        lambda: op.create_table(
            "ai_chat_logs",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("session_id", sa.Integer(), sa.ForeignKey("ai_chat_sessions.id"), nullable=False),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("question", sa.Text(), nullable=False),
            sa.Column("answer_summary", sa.Text(), nullable=False),
            sa.Column("sources", sa.JSON(), nullable=False),
            sa.Column("mode", sa.String(length=30), nullable=False),
            sa.Column("needs_manager_confirmation", sa.Boolean(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
        ),
    )
    op.create_index(op.f("ix_ai_chat_logs_session_id"), "ai_chat_logs", ["session_id"], unique=False, if_not_exists=True)
    op.create_index(op.f("ix_ai_chat_logs_user_id"), "ai_chat_logs", ["user_id"], unique=False, if_not_exists=True)


def downgrade() -> None:
    op.drop_table("ai_chat_logs", if_exists=True)
    op.drop_table("ai_chat_sessions", if_exists=True)
    op.drop_table("checklist_run_items", if_exists=True)
    op.drop_table("checklist_runs", if_exists=True)
    op.drop_table("checklist_template_items", if_exists=True)
    op.drop_table("checklist_templates", if_exists=True)
    op.drop_table("manual_steps", if_exists=True)
    op.drop_table("manual_sections", if_exists=True)
    op.drop_table("manuals", if_exists=True)
    op.drop_table("users", if_exists=True)
