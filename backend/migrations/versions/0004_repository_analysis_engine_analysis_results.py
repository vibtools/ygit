"""repository analysis engine analysis results

Revision ID: 0004_repository_analysis_engine
Revises: 0003_repository_engine
Create Date: 2026-07-04
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0004_repository_analysis_engine"
down_revision = "0003_repository_engine"
branch_labels = None
depends_on = None

ANALYSIS_STAGE = "stage IN ('quick', 'deep')"
ANALYSIS_STATUS = "status IN ('not_started', 'quick_running', 'quick_completed', 'deep_queued', 'deep_running', 'deep_completed', 'failed')"
ANALYSIS_SCORE = "score IS NULL OR (score >= 0 AND score <= 100)"


def upgrade() -> None:
    op.create_table(
        "analysis_results",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("repository_id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("project_id", sa.String(length=64), nullable=True),
        sa.Column("stage", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("framework", sa.String(length=64), nullable=True),
        sa.Column("package_manager", sa.String(length=32), nullable=True),
        sa.Column("build_command", sa.Text(), nullable=True),
        sa.Column("output_directory", sa.String(length=256), nullable=True),
        sa.Column("deploy_ready", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("explanation", sa.JSON(), nullable=True),
        sa.Column("warnings", sa.JSON(), nullable=True),
        sa.Column("errors", sa.JSON(), nullable=True),
        sa.Column("recommendations", sa.JSON(), nullable=True),
        sa.Column("commit_sha", sa.String(length=128), nullable=True),
        sa.Column("is_latest", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["repository_id"], ["repository_metadata.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(ANALYSIS_STAGE, name="ck_analysis_results_stage"),
        sa.CheckConstraint(ANALYSIS_STATUS, name="ck_analysis_results_status"),
        sa.CheckConstraint(ANALYSIS_SCORE, name="ck_analysis_results_score"),
    )
    op.create_index("idx_analysis_results_repository_id", "analysis_results", ["repository_id"])
    op.create_index("idx_analysis_results_user_id", "analysis_results", ["user_id"])
    op.create_index("idx_analysis_results_project_id", "analysis_results", ["project_id"])
    op.create_index("idx_analysis_results_status", "analysis_results", ["status"])
    op.create_index("idx_analysis_results_is_latest", "analysis_results", ["is_latest"])
    op.create_index("idx_analysis_results_created_at", "analysis_results", ["created_at"])
    op.create_index("idx_analysis_results_deleted_at", "analysis_results", ["deleted_at"])


def downgrade() -> None:
    op.drop_index("idx_analysis_results_deleted_at", table_name="analysis_results")
    op.drop_index("idx_analysis_results_created_at", table_name="analysis_results")
    op.drop_index("idx_analysis_results_is_latest", table_name="analysis_results")
    op.drop_index("idx_analysis_results_status", table_name="analysis_results")
    op.drop_index("idx_analysis_results_project_id", table_name="analysis_results")
    op.drop_index("idx_analysis_results_user_id", table_name="analysis_results")
    op.drop_index("idx_analysis_results_repository_id", table_name="analysis_results")
    op.drop_table("analysis_results")
