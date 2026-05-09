"""add active to checklist templates

Revision ID: 20260508_0004
Revises: 20260508_0003
Create Date: 2026-05-08
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260508_0004"
down_revision = "20260508_0003"
branch_labels = None
depends_on = None


def _column_names(table_name: str) -> set[str]:
    inspector = sa.inspect(op.get_bind())
    if not inspector.has_table(table_name):
        return set()
    return {column["name"] for column in inspector.get_columns(table_name)}


def upgrade() -> None:
    template_columns = _column_names("checklist_templates")
    if "active" not in template_columns:
        op.add_column(
            "checklist_templates",
            sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        )

    item_columns = _column_names("checklist_template_items")
    if "active" not in item_columns:
        op.add_column(
            "checklist_template_items",
            sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        )


def downgrade() -> None:
    if "active" in _column_names("checklist_template_items"):
        op.drop_column("checklist_template_items", "active")
    if "active" in _column_names("checklist_templates"):
        op.drop_column("checklist_templates", "active")
