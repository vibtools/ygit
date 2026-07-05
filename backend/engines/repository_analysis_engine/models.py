from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.shared.base.models import Base, TimestampMixin


class AnalysisResultModel(TimestampMixin, Base):
    __tablename__ = "analysis_results"
    __table_args__ = (
        Index("idx_analysis_results_repository_id", "repository_id"),
        Index("idx_analysis_results_project_id", "project_id"),
        Index("idx_analysis_results_status", "status"),
        Index("idx_analysis_results_is_latest", "is_latest"),
        Index("idx_analysis_results_created_at", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    repository_id: Mapped[str] = mapped_column(String(64), ForeignKey("repository_metadata.id", ondelete="RESTRICT"), nullable=False)
    user_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.id", ondelete="RESTRICT"), index=True, nullable=False)
    project_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    stage: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    framework: Mapped[str | None] = mapped_column(String(64), nullable=True)
    package_manager: Mapped[str | None] = mapped_column(String(32), nullable=True)
    build_command: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_directory: Mapped[str | None] = mapped_column(String(256), nullable=True)
    deploy_ready: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    explanation: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    warnings: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    errors: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    recommendations: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    commit_sha: Mapped[str | None] = mapped_column(String(128), nullable=True)
    is_latest: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
