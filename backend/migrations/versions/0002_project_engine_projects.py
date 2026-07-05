"""project engine projects and project settings

Revision ID: 0002_project_engine
Revises: 0001_auth_engine
Create Date: 2026-07-04
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0002_project_engine"
down_revision = "0001_auth_engine"
branch_labels = None
depends_on = None

PROJECT_STATUS = "status IN ('draft', 'repository_attached', 'analysis_ready', 'deploy_ready', 'deployed', 'failed', 'deleted')"


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("slug", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="draft"),
        sa.Column("repository_id", sa.String(length=64), nullable=True),
        sa.Column("analysis_id", sa.String(length=64), nullable=True),
        sa.Column("current_deployment_id", sa.String(length=64), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug", name="uq_projects_slug"),
        sa.CheckConstraint(PROJECT_STATUS, name="ck_projects_status"),
    )
    op.create_index("idx_projects_user_id", "projects", ["user_id"])
    op.create_index("idx_projects_status", "projects", ["status"])
    op.create_index("idx_projects_slug", "projects", ["slug"])
    op.create_index("idx_projects_created_at", "projects", ["created_at"])
    op.create_index("idx_projects_deleted_at", "projects", ["deleted_at"])
    op.create_index("idx_projects_repository_id", "projects", ["repository_id"])
    op.create_index("idx_projects_analysis_id", "projects", ["analysis_id"])
    op.create_index("idx_projects_current_deployment_id", "projects", ["current_deployment_id"])

    op.create_table(
        "project_settings",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("project_id", sa.String(length=64), nullable=False),
        sa.Column("build_command_override", sa.Text(), nullable=True),
        sa.Column("output_directory_override", sa.Text(), nullable=True),
        sa.Column("environment_variables_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("auto_deploy_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", name="uq_project_settings_project_id"),
    )
    op.create_index("idx_project_settings_project_id", "project_settings", ["project_id"])


def downgrade() -> None:
    op.drop_index("idx_project_settings_project_id", table_name="project_settings")
    op.drop_table("project_settings")
    op.drop_index("idx_projects_current_deployment_id", table_name="projects")
    op.drop_index("idx_projects_analysis_id", table_name="projects")
    op.drop_index("idx_projects_repository_id", table_name="projects")
    op.drop_index("idx_projects_deleted_at", table_name="projects")
    op.drop_index("idx_projects_created_at", table_name="projects")
    op.drop_index("idx_projects_slug", table_name="projects")
    op.drop_index("idx_projects_status", table_name="projects")
    op.drop_index("idx_projects_user_id", table_name="projects")
    op.drop_table("projects")
