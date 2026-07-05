from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from backend.shared.base.models import Base, TimestampMixin


class DomainModel(TimestampMixin, Base):
    """YGIT-generated project URL owned by Domain Engine."""

    __tablename__ = "domains"
    __table_args__ = (
        UniqueConstraint("slug", "base_domain", name="uq_domains_slug_base_domain"),
        UniqueConstraint("project_id", name="uq_domains_project_id"),
        Index("idx_domains_user_id", "user_id"),
        Index("idx_domains_project_id", "project_id"),
        Index("idx_domains_slug_base_domain", "slug", "base_domain"),
        Index("idx_domains_status", "status"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False)
    user_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    slug: Mapped[str] = mapped_column(String(64), nullable=False)
    base_domain: Mapped[str] = mapped_column(String(255), default="ygit.net", nullable=False)
    full_url: Mapped[str] = mapped_column(String(512), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="reserved", nullable=False)
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
