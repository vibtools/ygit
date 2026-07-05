"""notification engine notifications

Revision ID: 0012_notification_engine
Revises: 0011_platform_engine
Create Date: 2026-07-04
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0012_notification_engine"
down_revision = "0011_platform_engine"
branch_labels = None
depends_on = None

NOTIFICATION_TYPE = "type IN ('deployment_success', 'deployment_failure', 'connected_account_warning', 'platform_notice', 'system_notice')"
NOTIFICATION_STATUS = "status IN ('unread', 'read', 'failed')"
NOTIFICATION_SEVERITY = "severity IN ('info', 'success', 'warning', 'error')"
NOTIFICATION_CHANNEL = "channel = 'in_app'"


def upgrade() -> None:
    op.create_table(
        "notifications",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("type", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(length=32), nullable=False, server_default="info"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="unread"),
        sa.Column("channel", sa.String(length=32), nullable=False, server_default="in_app"),
        sa.Column("delivery_status", sa.String(length=32), nullable=False, server_default="delivered"),
        sa.Column("related_resource_type", sa.String(length=80), nullable=True),
        sa.Column("related_resource_id", sa.String(length=128), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failure_code", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(NOTIFICATION_TYPE, name="ck_notifications_type"),
        sa.CheckConstraint(NOTIFICATION_STATUS, name="ck_notifications_status"),
        sa.CheckConstraint(NOTIFICATION_SEVERITY, name="ck_notifications_severity"),
        sa.CheckConstraint(NOTIFICATION_CHANNEL, name="ck_notifications_channel_mvp"),
    )
    op.create_index("idx_notifications_user_id", "notifications", ["user_id"])
    op.create_index("idx_notifications_user_status_created_at", "notifications", ["user_id", "status", "created_at"])
    op.create_index("idx_notifications_related_resource", "notifications", ["related_resource_type", "related_resource_id"])
    op.create_index("idx_notifications_type", "notifications", ["type"])


def downgrade() -> None:
    op.drop_index("idx_notifications_type", table_name="notifications")
    op.drop_index("idx_notifications_related_resource", table_name="notifications")
    op.drop_index("idx_notifications_user_status_created_at", table_name="notifications")
    op.drop_index("idx_notifications_user_id", table_name="notifications")
    op.drop_table("notifications")
