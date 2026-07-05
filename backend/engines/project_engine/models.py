from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.shared.base.models import Base, TimestampMixin


class ProjectModel(TimestampMixin, Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.id", ondelete="RESTRICT"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="draft", index=True, nullable=False)
    repository_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    analysis_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    current_deployment_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)


class ProjectSettingsModel(TimestampMixin, Base):
    __tablename__ = "project_settings"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), ForeignKey("projects.id", ondelete="RESTRICT"), unique=True, index=True, nullable=False)
    build_command_override: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_directory_override: Mapped[str | None] = mapped_column(Text, nullable=True)
    environment_variables_enabled: Mapped[bool] = mapped_column(default=False, nullable=False)
    auto_deploy_enabled: Mapped[bool] = mapped_column(default=False, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
