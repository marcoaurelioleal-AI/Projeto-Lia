"""add operational incidents and evidences

Revision ID: 20260508_0002
Revises: 20260508_0001
Create Date: 2026-05-08
"""

from __future__ import annotations

from collections.abc import Callable

import sqlalchemy as sa
from alembic import op

revision = "20260508_0002"
down_revision = "20260508_0001"
branch_labels = None
depends_on = None


def _create_if_missing(table_name: str, create: Callable[[], None]) -> None:
    inspector = sa.inspect(op.get_bind())
    if not inspector.has_table(table_name):
        create()


def upgrade() -> None:
    _create_if_missing(
        "operational_incidents",
        lambda: op.create_table(
            "operational_incidents",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("store", sa.String(length=80), nullable=False, server_default="Grupo Lia"),
            sa.Column("category", sa.String(length=30), nullable=False),
            sa.Column("severity", sa.String(length=30), nullable=False),
            sa.Column("description", sa.Text(), nullable=False),
            sa.Column("status", sa.String(length=30), nullable=False, server_default="aberta"),
            sa.Column("created_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("resolved_at", sa.DateTime(), nullable=True),
            sa.Column("resolved_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        ),
    )
    op.create_index(
        op.f("ix_operational_incidents_store"),
        "operational_incidents",
        ["store"],
        unique=False,
        if_not_exists=True,
    )
    op.create_index(
        op.f("ix_operational_incidents_category"),
        "operational_incidents",
        ["category"],
        unique=False,
        if_not_exists=True,
    )
    op.create_index(
        op.f("ix_operational_incidents_severity"),
        "operational_incidents",
        ["severity"],
        unique=False,
        if_not_exists=True,
    )
    op.create_index(
        op.f("ix_operational_incidents_status"),
        "operational_incidents",
        ["status"],
        unique=False,
        if_not_exists=True,
    )

    _create_if_missing(
        "checklist_evidences",
        lambda: op.create_table(
            "checklist_evidences",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("checklist_run_item_id", sa.Integer(), sa.ForeignKey("checklist_run_items.id"), nullable=False),
            sa.Column("uploaded_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("storage_provider", sa.String(length=30), nullable=False, server_default="local"),
            sa.Column("file_url", sa.String(length=500), nullable=True),
            sa.Column("file_path", sa.String(length=500), nullable=False),
            sa.Column("original_filename", sa.String(length=255), nullable=False),
            sa.Column("content_type", sa.String(length=120), nullable=False),
            sa.Column("file_size", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
        ),
    )
    op.create_index(
        op.f("ix_checklist_evidences_checklist_run_item_id"),
        "checklist_evidences",
        ["checklist_run_item_id"],
        unique=False,
        if_not_exists=True,
    )
    op.create_index(
        op.f("ix_checklist_evidences_uploaded_by_user_id"),
        "checklist_evidences",
        ["uploaded_by_user_id"],
        unique=False,
        if_not_exists=True,
    )


def downgrade() -> None:
    op.drop_table("checklist_evidences", if_exists=True)
    op.drop_table("operational_incidents", if_exists=True)
