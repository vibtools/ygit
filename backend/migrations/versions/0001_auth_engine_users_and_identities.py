"""auth engine users and identities

Revision ID: 0001_auth_engine
Revises:
Create Date: 2026-07-04
"""
from __future__ import annotations


import sqlalchemy as sa
from alembic import op

revision = "0001_auth_engine"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("avatar_url", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("email_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email", name="uq_users_email"),
        sa.CheckConstraint("status IN ('active', 'disabled', 'deleted')", name="ck_users_status"),
    )
    op.create_index("idx_users_email", "users", ["email"])
    op.create_index("idx_users_status", "users", ["status"])
    op.create_index("idx_users_created_at", "users", ["created_at"])

    op.create_table(
        "user_identities",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False, server_default="keycloak"),
        sa.Column("provider_subject", sa.String(length=255), nullable=False),
        sa.Column("provider_realm", sa.String(length=128), nullable=False, server_default="vib"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "provider",
            "provider_realm",
            "provider_subject",
            name="uq_user_identities_provider_subject",
        ),
    )
    op.create_index("idx_user_identities_user_id", "user_identities", ["user_id"])
    op.create_index(
        "idx_user_identities_provider_subject",
        "user_identities",
        ["provider", "provider_realm", "provider_subject"],
    )


def downgrade() -> None:
    op.drop_index("idx_user_identities_provider_subject", table_name="user_identities")
    op.drop_index("idx_user_identities_user_id", table_name="user_identities")
    op.drop_table("user_identities")
    op.drop_index("idx_users_created_at", table_name="users")
    op.drop_index("idx_users_status", table_name="users")
    op.drop_index("idx_users_email", table_name="users")
    op.drop_table("users")
