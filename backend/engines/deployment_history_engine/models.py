from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.shared.base.models import Base, TimestampMixin


class DeploymentHistoryModel(TimestampMixin, Base):
    __tablename__ = "deployment_history"
    __table_args__ = (
        Index("idx_deployment_history_deployment_id", "deployment_id"),
        Index("idx_deployment_history_project_id", "project_id"),
        Index("idx_deployment_history_status", "status"),
        Index("idx_deployment_history_created_at", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    deployment_id: Mapped[str] = mapped_column(String(64), ForeignKey("deployments.id", ondelete="RESTRICT"), unique=True, nullable=False)
    project_id: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="created", nullable=False)
    provider: Mapped[str | None] = mapped_column(String(32), nullable=True)
    provider_project_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    provider_deployment_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    deployment_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    failure_code: Mapped[str | None] = mapped_column(String(128), nullable=True)
    failure_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    provider_summary: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, default=dict, nullable=False)


class DeploymentLogModel(Base):
    __tablename__ = "deployment_logs"
    __table_args__ = (
        Index("idx_deployment_logs_deployment_id_sequence", "deployment_id", "sequence"),
        Index("idx_deployment_logs_project_id", "project_id"),
        Index("idx_deployment_logs_level", "level"),
        Index("idx_deployment_logs_created_at", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    deployment_id: Mapped[str] = mapped_column(String(64), ForeignKey("deployments.id", ondelete="RESTRICT"), nullable=False)
    project_id: Mapped[str] = mapped_column(String(64), nullable=False)
    level: Mapped[str] = mapped_column(String(16), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, default=dict, nullable=False)
    sequence: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
