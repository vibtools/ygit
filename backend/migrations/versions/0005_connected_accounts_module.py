"""connected accounts module

Revision ID: 0005_connected_accounts_module
Revises: 0004_repository_analysis_engine
Create Date: 2026-07-04
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0005_connected_accounts_module"
down_revision = "0004_repository_analysis_engine"
branch_labels = None
depends_on = None

PROVIDER_CHECK = "provider IN ('github', 'cloudflare')"
STATUS_CHECK = "status IN ('connected', 'disconnected', 'error', 'reconnect_required')"


def upgrade() -> None:
    op.create_table(
        "connected_accounts",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="disconnected"),
        sa.Column("provider_account_id", sa.String(length=255), nullable=True),
        sa.Column("provider_account_name", sa.String(length=255), nullable=True),
        sa.Column("token_secret_ref", sa.Text(), nullable=True),
        sa.Column("token_ciphertext", sa.Text(), nullable=True),
        sa.Column("token_key_version", sa.String(length=64), nullable=True),
        sa.Column("scopes", sa.JSON(), nullable=True),
        sa.Column("last_error_code", sa.String(length=128), nullable=True),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("connected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("disconnected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "provider", name="uq_connected_accounts_user_provider"),
        sa.CheckConstraint(PROVIDER_CHECK, name="ck_connected_accounts_provider"),
        sa.CheckConstraint(STATUS_CHECK, name="ck_connected_accounts_status"),
    )
    op.create_index("idx_connected_accounts_user_id", "connected_accounts", ["user_id"])
    op.create_index("idx_connected_accounts_provider", "connected_accounts", ["provider"])
    op.create_index("idx_connected_accounts_status", "connected_accounts", ["status"])
    op.create_index("idx_connected_accounts_deleted_at", "connected_accounts", ["deleted_at"])


def downgrade() -> None:
    op.drop_index("idx_connected_accounts_deleted_at", table_name="connected_accounts")
    op.drop_index("idx_connected_accounts_status", table_name="connected_accounts")
    op.drop_index("idx_connected_accounts_provider", table_name="connected_accounts")
    op.drop_index("idx_connected_accounts_user_id", table_name="connected_accounts")
    op.drop_table("connected_accounts")
