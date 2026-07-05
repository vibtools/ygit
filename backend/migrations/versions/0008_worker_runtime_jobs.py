"""worker runtime jobs

Revision ID: 0008_worker_runtime_jobs
Revises: 0007_deployment_history_engine
Create Date: 2026-07-04
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0008_worker_runtime_jobs"
down_revision = "0007_deployment_history_engine"
branch_labels = None
depends_on = None

JOB_STATUS_CHECK = "status IN ('queued', 'running', 'completed', 'failed', 'retry_waiting', 'cancelled')"
JOB_TYPE_CHECK = "job_type IN ('deploy_project', 'redeploy_project', 'repository_analysis_deep', 'webhook_event')"


def upgrade() -> None:
    op.create_table(
        "jobs",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("job_type", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="queued"),
        sa.Column("queue_name", sa.String(length=64), nullable=False, server_default="default"),
        sa.Column("payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column("error_code", sa.String(length=128), nullable=True),
        sa.Column("error_summary", sa.Text(), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("locked_by", sa.String(length=128), nullable=True),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(JOB_STATUS_CHECK, name="ck_jobs_status"),
        sa.CheckConstraint(JOB_TYPE_CHECK, name="ck_jobs_type"),
    )
    op.create_index("idx_jobs_job_type", "jobs", ["job_type"])
    op.create_index("idx_jobs_status", "jobs", ["status"])
    op.create_index("idx_jobs_queue_name", "jobs", ["queue_name"])
    op.create_index("idx_jobs_locked_by", "jobs", ["locked_by"])
    op.create_index("idx_jobs_available_at", "jobs", ["available_at"])
    op.create_index("idx_jobs_queue_status_available", "jobs", ["queue_name", "status", "available_at"])


def downgrade() -> None:
    op.drop_index("idx_jobs_queue_status_available", table_name="jobs")
    op.drop_index("idx_jobs_available_at", table_name="jobs")
    op.drop_index("idx_jobs_locked_by", table_name="jobs")
    op.drop_index("idx_jobs_queue_name", table_name="jobs")
    op.drop_index("idx_jobs_status", table_name="jobs")
    op.drop_index("idx_jobs_job_type", table_name="jobs")
    op.drop_table("jobs")
