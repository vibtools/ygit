from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Index, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.shared.base.models import Base, TimestampMixin


class RepositoryMetadataModel(TimestampMixin, Base):
    __tablename__ = "repository_metadata"
    __table_args__ = (
        Index("idx_repository_metadata_provider_owner_name", "provider", "owner", "name"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.id", ondelete="RESTRICT"), index=True, nullable=False)
    provider: Mapped[str] = mapped_column(String(32), default="github", index=True, nullable=False)
    repository_url: Mapped[str] = mapped_column(Text, index=True, nullable=False)
    owner: Mapped[str] = mapped_column(String(128), nullable=False)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    default_branch: Mapped[str | None] = mapped_column(String(256), nullable=True)
    visibility: Mapped[str] = mapped_column(String(32), default="unknown", nullable=False)
    latest_commit_sha: Mapped[str | None] = mapped_column(String(128), nullable=True)
    file_tree_snapshot: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    repository_metadata: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSON, nullable=True)
    fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
