from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.ids import new_id
from backend.engines.domain_engine.models import DomainModel
from backend.engines.domain_engine.schemas import DomainRecord

ACTIVE_STATUSES = {"reserved", "attached"}


class DomainRepository:
    """Database repository owned by Domain Engine only."""

    async def get_by_id(self, db: AsyncSession, domain_id: str) -> DomainModel | None:
        result = await db.execute(select(DomainModel).where(DomainModel.id == domain_id))
        return result.scalar_one_or_none()

    async def get_active_by_slug_base(self, db: AsyncSession, *, slug: str, base_domain: str) -> DomainModel | None:
        result = await db.execute(
            select(DomainModel).where(
                DomainModel.slug == slug,
                DomainModel.base_domain == base_domain,
                DomainModel.status.in_(ACTIVE_STATUSES),
            )
        )
        return result.scalar_one_or_none()

    async def get_active_by_project(self, db: AsyncSession, *, project_id: str) -> DomainModel | None:
        result = await db.execute(
            select(DomainModel).where(
                DomainModel.project_id == project_id,
                DomainModel.status.in_(ACTIVE_STATUSES),
            )
        )
        return result.scalar_one_or_none()

    async def reserve_domain(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        project_id: str,
        slug: str,
        base_domain: str,
        full_url: str,
    ) -> DomainRecord:
        model = DomainModel(
            id=new_id("domain"),
            user_id=user_id,
            project_id=project_id,
            slug=slug,
            base_domain=base_domain,
            full_url=full_url,
            status="reserved",
        )
        db.add(model)
        await db.flush()
        return self.to_record(model)

    async def release_domain(self, db: AsyncSession, *, domain: DomainModel) -> DomainRecord:
        domain.status = "released"
        domain.released_at = datetime.now(timezone.utc)
        await db.flush()
        return self.to_record(domain)

    def to_record(self, model: DomainModel) -> DomainRecord:
        return DomainRecord(
            id=model.id,
            project_id=model.project_id,
            user_id=model.user_id,
            slug=model.slug,
            base_domain=model.base_domain,
            full_url=model.full_url,
            status=model.status,  # type: ignore[arg-type]
            created_at=model.created_at,
            updated_at=model.updated_at,
            released_at=model.released_at,
        )
