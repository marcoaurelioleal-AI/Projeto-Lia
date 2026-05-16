"""add user store id

Revision ID: 20260516_0008
Revises: 20260516_0007
Create Date: 2026-05-16
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260516_0008"
down_revision = "20260516_0007"
branch_labels = None
depends_on = None


def _has_column(table_name: str, column_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return any(column["name"] == column_name for column in inspector.get_columns(table_name))


def upgrade() -> None:
    if not _has_column("users", "store_id"):
        with op.batch_alter_table("users") as batch:
            batch.add_column(sa.Column("store_id", sa.Integer(), nullable=True))
            batch.create_foreign_key("fk_users_store_id_stores", "stores", ["store_id"], ["id"])
            batch.create_index("ix_users_store_id", ["store_id"], unique=False)


def downgrade() -> None:
    if _has_column("users", "store_id"):
        with op.batch_alter_table("users") as batch:
            batch.drop_index("ix_users_store_id")
            batch.drop_constraint("fk_users_store_id_stores", type_="foreignkey")
            batch.drop_column("store_id")
