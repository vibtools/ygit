"""repository engine repository metadata

Revision ID: 0003_repository_engine
Revises: 0002_project_engine
Create Date: 2026-07-04
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0003_repository_engine"
down_revision = "0002_project_engine"
branch_labels = None
depends_on = None

REPOSITORY_PROVIDER = "provider IN ('github')"
REPOSITORY_VISIBILITY = "visibility IN ('public', 'private', 'internal', 'unknown')"


def upgrade() -> None:
    op.create_table(
        "repository_metadata",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False, server_default="github"),
        sa.Column("repository_url", sa.Text(), nullable=False),
        sa.Column("owner", sa.String(length=128), nullable=False),
        sa.Column("name", sa.String(length=256), nullable=False),
        sa.Column("default_branch", sa.String(length=256), nullable=True),
        sa.Column("visibility", sa.String(length=32), nullable=False, server_default="unknown"),
        sa.Column("latest_commit_sha", sa.String(length=128), nullable=True),
        sa.Column("file_tree_snapshot", sa.JSON(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(REPOSITORY_PROVIDER, name="ck_repository_metadata_provider"),
        sa.CheckConstraint(REPOSITORY_VISIBILITY, name="ck_repository_metadata_visibility"),
    )
    op.create_index("idx_repository_metadata_user_id", "repository_metadata", ["user_id"])
    op.create_index("idx_repository_metadata_provider", "repository_metadata", ["provider"])
    op.create_index("idx_repository_metadata_provider_owner_name", "repository_metadata", ["provider", "owner", "name"])
    op.create_index("idx_repository_metadata_repository_url", "repository_metadata", ["repository_url"])
    op.create_index("idx_repository_metadata_fetched_at", "repository_metadata", ["fetched_at"])
    op.create_index("idx_repository_metadata_deleted_at", "repository_metadata", ["deleted_at"])


def downgrade() -> None:
    op.drop_index("idx_repository_metadata_deleted_at", table_name="repository_metadata")
    op.drop_index("idx_repository_metadata_fetched_at", table_name="repository_metadata")
    op.drop_index("idx_repository_metadata_repository_url", table_name="repository_metadata")
    op.drop_index("idx_repository_metadata_provider_owner_name", table_name="repository_metadata")
    op.drop_index("idx_repository_metadata_provider", table_name="repository_metadata")
    op.drop_index("idx_repository_metadata_user_id", table_name="repository_metadata")
    op.drop_table("repository_metadata")
