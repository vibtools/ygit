"""Create Platform Engine platform_settings and feature_flags tables.

Revision ID: 0011_platform_engine
Revises: 0010_audit_engine_audit_logs
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0011_platform_engine"
down_revision = "0010_audit_engine_audit_logs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "platform_settings",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("key", sa.String(length=128), nullable=False),
        sa.Column("value", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_sensitive", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_editable", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("key", name="uq_platform_settings_key"),
    )
    op.create_index("idx_platform_settings_key", "platform_settings", ["key"])

    op.create_table(
        "feature_flags",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("key", sa.String(length=128), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("key", name="uq_feature_flags_key"),
    )
    op.create_index("idx_feature_flags_key", "feature_flags", ["key"])
    op.create_index("idx_feature_flags_enabled", "feature_flags", ["enabled"])


def downgrade() -> None:
    op.drop_index("idx_feature_flags_enabled", table_name="feature_flags")
    op.drop_index("idx_feature_flags_key", table_name="feature_flags")
    op.drop_table("feature_flags")
    op.drop_index("idx_platform_settings_key", table_name="platform_settings")
    op.drop_table("platform_settings")
