"""deployment history engine

Revision ID: 0007_deployment_history_engine
Revises: 0006_deploy_engine_deployments
Create Date: 2026-07-04
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0007_deployment_history_engine"
down_revision = "0006_deploy_engine_deployments"
branch_labels = None
depends_on = None

HISTORY_STATUS_CHECK = "status IN ('created', 'running', 'completed', 'failed', 'cancelled')"
LOG_LEVEL_CHECK = "level IN ('debug', 'info', 'warning', 'error')"


def upgrade() -> None:
    op.create_table(
        "deployment_history",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("deployment_id", sa.String(length=64), nullable=False),
        sa.Column("project_id", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="created"),
        sa.Column("provider", sa.String(length=32), nullable=True),
        sa.Column("provider_project_id", sa.String(length=128), nullable=True),
        sa.Column("provider_deployment_id", sa.String(length=128), nullable=True),
        sa.Column("deployment_url", sa.Text(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("failure_code", sa.String(length=128), nullable=True),
        sa.Column("failure_summary", sa.Text(), nullable=True),
        sa.Column("provider_summary", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["deployment_id"], ["deployments.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("deployment_id", name="uq_deployment_history_deployment_id"),
        sa.CheckConstraint(HISTORY_STATUS_CHECK, name="ck_deployment_history_status"),
    )
    op.create_index("idx_deployment_history_deployment_id", "deployment_history", ["deployment_id"])
    op.create_index("idx_deployment_history_project_id", "deployment_history", ["project_id"])
    op.create_index("idx_deployment_history_status", "deployment_history", ["status"])
    op.create_index("idx_deployment_history_created_at", "deployment_history", ["created_at"])

    op.create_table(
        "deployment_logs",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("deployment_id", sa.String(length=64), nullable=False),
        sa.Column("project_id", sa.String(length=64), nullable=False),
        sa.Column("level", sa.String(length=16), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("sequence", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["deployment_id"], ["deployments.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("deployment_id", "sequence", name="uq_deployment_logs_deployment_sequence"),
        sa.CheckConstraint(LOG_LEVEL_CHECK, name="ck_deployment_logs_level"),
    )
    op.create_index("idx_deployment_logs_deployment_id_sequence", "deployment_logs", ["deployment_id", "sequence"])
    op.create_index("idx_deployment_logs_project_id", "deployment_logs", ["project_id"])
    op.create_index("idx_deployment_logs_level", "deployment_logs", ["level"])
    op.create_index("idx_deployment_logs_created_at", "deployment_logs", ["created_at"])


def downgrade() -> None:
    op.drop_index("idx_deployment_logs_created_at", table_name="deployment_logs")
    op.drop_index("idx_deployment_logs_level", table_name="deployment_logs")
    op.drop_index("idx_deployment_logs_project_id", table_name="deployment_logs")
    op.drop_index("idx_deployment_logs_deployment_id_sequence", table_name="deployment_logs")
    op.drop_table("deployment_logs")
    op.drop_index("idx_deployment_history_created_at", table_name="deployment_history")
    op.drop_index("idx_deployment_history_status", table_name="deployment_history")
    op.drop_index("idx_deployment_history_project_id", table_name="deployment_history")
    op.drop_index("idx_deployment_history_deployment_id", table_name="deployment_history")
    op.drop_table("deployment_history")
