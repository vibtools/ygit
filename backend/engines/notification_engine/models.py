from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.shared.base.models import Base, TimestampMixin


class NotificationModel(TimestampMixin, Base):
    """In-app notification owned only by Notification Engine."""

    __tablename__ = "notifications"
    __table_args__ = (
        CheckConstraint(
            "type IN ('deployment_success', 'deployment_failure', 'connected_account_warning', 'platform_notice', 'system_notice')",
            name="ck_notifications_type",
        ),
        CheckConstraint("status IN ('unread', 'read', 'failed')", name="ck_notifications_status"),
        CheckConstraint("severity IN ('info', 'success', 'warning', 'error')", name="ck_notifications_severity"),
        CheckConstraint("channel = 'in_app'", name="ck_notifications_channel_mvp"),
        Index("idx_notifications_user_id", "user_id"),
        Index("idx_notifications_user_status_created_at", "user_id", "status", "created_at"),
        Index("idx_notifications_related_resource", "related_resource_type", "related_resource_id"),
        Index("idx_notifications_type", "type"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    type: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(32), nullable=False, default="info")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="unread")
    channel: Mapped[str] = mapped_column(String(32), nullable=False, default="in_app")
    delivery_status: Mapped[str] = mapped_column(String(32), nullable=False, default="delivered")
    related_resource_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    related_resource_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, default=dict, nullable=False)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failure_code: Mapped[str | None] = mapped_column(String(128), nullable=True)
