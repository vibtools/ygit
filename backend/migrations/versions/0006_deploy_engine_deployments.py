"""deploy engine deployments

Revision ID: 0006_deploy_engine_deployments
Revises: 0005_connected_accounts_module
Create Date: 2026-07-04
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0006_deploy_engine_deployments"
down_revision = "0005_connected_accounts_module"
branch_labels = None
depends_on = None

STATUS_CHECK = "status IN ('draft', 'queued', 'running', 'completed', 'failed', 'cancelled')"
REQUESTED_BY_CHECK = "requested_by IN ('user', 'admin', 'system')"


def upgrade() -> None:
    op.create_table(
        "deployments",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("project_id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("repository_id", sa.String(length=64), nullable=False),
        sa.Column("analysis_id", sa.String(length=64), nullable=False),
        sa.Column("domain_id", sa.String(length=64), nullable=True),
        sa.Column("job_id", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="queued"),
        sa.Column("requested_by", sa.String(length=32), nullable=False, server_default="user"),
        sa.Column("source_deployment_id", sa.String(length=64), nullable=True),
        sa.Column("queued_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failure_code", sa.String(length=128), nullable=True),
        sa.Column("failure_summary", sa.Text(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(STATUS_CHECK, name="ck_deployments_status"),
        sa.CheckConstraint(REQUESTED_BY_CHECK, name="ck_deployments_requested_by"),
    )
    op.create_index("idx_deployments_project_id", "deployments", ["project_id"])
    op.create_index("idx_deployments_user_id", "deployments", ["user_id"])
    op.create_index("idx_deployments_status", "deployments", ["status"])
    op.create_index("idx_deployments_job_id", "deployments", ["job_id"])
    op.create_index("idx_deployments_created_at", "deployments", ["created_at"])
    op.create_index("idx_deployments_project_status_created_at", "deployments", ["project_id", "status", "created_at"])


def downgrade() -> None:
    op.drop_index("idx_deployments_project_status_created_at", table_name="deployments")
    op.drop_index("idx_deployments_created_at", table_name="deployments")
    op.drop_index("idx_deployments_job_id", table_name="deployments")
    op.drop_index("idx_deployments_status", table_name="deployments")
    op.drop_index("idx_deployments_user_id", table_name="deployments")
    op.drop_index("idx_deployments_project_id", table_name="deployments")
    op.drop_table("deployments")
