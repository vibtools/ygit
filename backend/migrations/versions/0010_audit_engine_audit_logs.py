"""audit engine audit logs

Revision ID: 0010_audit_engine_audit_logs
Revises: 0009_domain_engine_domains
Create Date: 2026-07-04
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0010_audit_engine_audit_logs"
down_revision = "0009_domain_engine_domains"
branch_labels = None
depends_on = None

ACTOR_TYPE_CHECK = "actor_type IN ('user', 'admin', 'system', 'worker')"


def upgrade() -> None:
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("event_name", sa.String(length=160), nullable=False),
        sa.Column("event_version", sa.String(length=32), nullable=False, server_default="1.0"),
        sa.Column("actor_user_id", sa.String(length=64), nullable=True),
        sa.Column("actor_type", sa.String(length=32), nullable=False, server_default="system"),
        sa.Column("target_type", sa.String(length=80), nullable=True),
        sa.Column("target_id", sa.String(length=128), nullable=True),
        sa.Column("ip_address", postgresql.INET(), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("trace_id", sa.String(length=128), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(ACTOR_TYPE_CHECK, name="ck_audit_logs_actor_type"),
    )
    op.create_index("idx_audit_logs_event_name", "audit_logs", ["event_name"])
    op.create_index("idx_audit_logs_actor_user_id", "audit_logs", ["actor_user_id"])
    op.create_index("idx_audit_logs_target", "audit_logs", ["target_type", "target_id"])
    op.create_index("idx_audit_logs_trace_id", "audit_logs", ["trace_id"])
    op.create_index("idx_audit_logs_created_at", "audit_logs", ["created_at"])
    op.execute(
        """
        CREATE OR REPLACE FUNCTION prevent_audit_logs_update_delete()
        RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'audit_logs are immutable';
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_prevent_audit_logs_update
        BEFORE UPDATE ON audit_logs
        FOR EACH ROW EXECUTE FUNCTION prevent_audit_logs_update_delete();
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_prevent_audit_logs_delete
        BEFORE DELETE ON audit_logs
        FOR EACH ROW EXECUTE FUNCTION prevent_audit_logs_update_delete();
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_prevent_audit_logs_delete ON audit_logs;")
    op.execute("DROP TRIGGER IF EXISTS trg_prevent_audit_logs_update ON audit_logs;")
    op.execute("DROP FUNCTION IF EXISTS prevent_audit_logs_update_delete();")
    op.drop_index("idx_audit_logs_created_at", table_name="audit_logs")
    op.drop_index("idx_audit_logs_trace_id", table_name="audit_logs")
    op.drop_index("idx_audit_logs_target", table_name="audit_logs")
    op.drop_index("idx_audit_logs_actor_user_id", table_name="audit_logs")
    op.drop_index("idx_audit_logs_event_name", table_name="audit_logs")
    op.drop_table("audit_logs")
