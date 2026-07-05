"""domain engine domains

Revision ID: 0009_domain_engine_domains
Revises: 0008_worker_runtime_jobs
Create Date: 2026-07-04
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0009_domain_engine_domains"
down_revision = "0008_worker_runtime_jobs"
branch_labels = None
depends_on = None

DOMAIN_STATUS = "status IN ('reserved', 'attached', 'released')"


def upgrade() -> None:
    op.create_table(
        "domains",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("project_id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("slug", sa.String(length=64), nullable=False),
        sa.Column("base_domain", sa.String(length=255), nullable=False, server_default="ygit.net"),
        sa.Column("full_url", sa.String(length=512), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="reserved"),
        sa.Column("released_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug", "base_domain", name="uq_domains_slug_base_domain"),
        sa.UniqueConstraint("project_id", name="uq_domains_project_id"),
        sa.CheckConstraint(DOMAIN_STATUS, name="ck_domains_status"),
    )
    op.create_index("idx_domains_user_id", "domains", ["user_id"])
    op.create_index("idx_domains_project_id", "domains", ["project_id"])
    op.create_index("idx_domains_slug_base_domain", "domains", ["slug", "base_domain"])
    op.create_index("idx_domains_status", "domains", ["status"])


def downgrade() -> None:
    op.drop_index("idx_domains_status", table_name="domains")
    op.drop_index("idx_domains_slug_base_domain", table_name="domains")
    op.drop_index("idx_domains_project_id", table_name="domains")
    op.drop_index("idx_domains_user_id", table_name="domains")
    op.drop_table("domains")
