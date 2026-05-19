"""add audit logs

Revision ID: 20260519_0010
Revises: 20260519_0009
Create Date: 2026-05-19
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260519_0010"
down_revision = "20260519_0009"
branch_labels = None
depends_on = None


def _has_table(table_name: str) -> bool:
    return sa.inspect(op.get_bind()).has_table(table_name)


def upgrade() -> None:
    if not _has_table("audit_logs"):
        op.create_table(
            "audit_logs",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("action", sa.String(length=120), nullable=False),
            sa.Column("actor_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("actor_username", sa.String(length=80), nullable=True),
            sa.Column("actor_role", sa.String(length=30), nullable=True),
            sa.Column("entity_type", sa.String(length=80), nullable=True),
            sa.Column("entity_id", sa.String(length=80), nullable=True),
            sa.Column("store", sa.String(length=80), nullable=True),
            sa.Column("status", sa.String(length=30), nullable=False),
            sa.Column("request_id", sa.String(length=64), nullable=True),
            sa.Column("ip_address", sa.String(length=80), nullable=True),
            sa.Column("user_agent", sa.String(length=255), nullable=True),
            sa.Column("details", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
        )
    op.create_index(op.f("ix_audit_logs_action"), "audit_logs", ["action"], unique=False, if_not_exists=True)
    op.create_index(op.f("ix_audit_logs_actor_user_id"), "audit_logs", ["actor_user_id"], unique=False, if_not_exists=True)
    op.create_index(op.f("ix_audit_logs_actor_username"), "audit_logs", ["actor_username"], unique=False, if_not_exists=True)
    op.create_index(op.f("ix_audit_logs_entity_type"), "audit_logs", ["entity_type"], unique=False, if_not_exists=True)
    op.create_index(op.f("ix_audit_logs_entity_id"), "audit_logs", ["entity_id"], unique=False, if_not_exists=True)
    op.create_index(op.f("ix_audit_logs_store"), "audit_logs", ["store"], unique=False, if_not_exists=True)
    op.create_index(op.f("ix_audit_logs_status"), "audit_logs", ["status"], unique=False, if_not_exists=True)
    op.create_index(op.f("ix_audit_logs_request_id"), "audit_logs", ["request_id"], unique=False, if_not_exists=True)
    op.create_index(op.f("ix_audit_logs_created_at"), "audit_logs", ["created_at"], unique=False, if_not_exists=True)


def downgrade() -> None:
    op.drop_table("audit_logs", if_exists=True)
