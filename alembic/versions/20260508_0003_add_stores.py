"""add stores

Revision ID: 20260508_0003
Revises: 20260508_0002
Create Date: 2026-05-08
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

import sqlalchemy as sa
from alembic import op

revision = "20260508_0003"
down_revision = "20260508_0002"
branch_labels = None
depends_on = None


def _create_if_missing(table_name: str, create: Callable[[], None]) -> bool:
    inspector = sa.inspect(op.get_bind())
    if not inspector.has_table(table_name):
        create()
        return True
    return False


def upgrade() -> None:
    created = _create_if_missing(
        "stores",
        lambda: op.create_table(
            "stores",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.String(length=80), nullable=False),
            sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.UniqueConstraint("name"),
        ),
    )
    op.create_index(op.f("ix_stores_name"), "stores", ["name"], unique=True, if_not_exists=True)

    if created:
        stores = sa.table(
            "stores",
            sa.column("name", sa.String),
            sa.column("active", sa.Boolean),
            sa.column("created_at", sa.DateTime),
        )
        now = datetime.utcnow()
        op.bulk_insert(
            stores,
            [
                {"name": "Grupo Lia", "active": True, "created_at": now},
                {"name": "Lia Burguer", "active": True, "created_at": now},
                {"name": "Lia Pizza", "active": True, "created_at": now},
                {"name": "Lia Salgados", "active": True, "created_at": now},
            ],
        )


def downgrade() -> None:
    op.drop_table("stores", if_exists=True)
