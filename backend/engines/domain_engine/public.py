from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from backend.engines.domain_engine.internal.service import DomainInternalService
from backend.engines.domain_engine.schemas import (
    DomainAvailability,
    DomainCheckInput,
    DomainDetail,
    DomainPreview,
    DomainReleaseResult,
    DomainReserveInput,
)


class DomainPublicService:
    """Public Domain Engine API. External consumers must not import internals."""

    def __init__(self, internal: DomainInternalService | None = None) -> None:
        self._internal = internal or DomainInternalService()

    async def check_slug_availability(self, db: AsyncSession, *, input_data: DomainCheckInput) -> DomainAvailability:
        return await self._internal.check_slug_availability(db, input_data=input_data)

    async def reserve_project_slug(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        project_id: str,
        input_data: DomainReserveInput,
    ) -> DomainDetail:
        return await self._internal.reserve_project_slug(
            db,
            user_id=user_id,
            project_id=project_id,
            input_data=input_data,
        )

    async def get_project_domain(self, db: AsyncSession, *, user_id: str, project_id: str) -> DomainDetail:
        return await self._internal.get_project_domain(db, user_id=user_id, project_id=project_id)

    async def release_project_domain(self, db: AsyncSession, *, user_id: str, project_id: str) -> DomainReleaseResult:
        return await self._internal.release_project_domain(db, user_id=user_id, project_id=project_id)

    def preview_domain(self, *, slug: str, base_domain: str = "ygit.net") -> DomainPreview:
        return self._internal.preview_domain(slug=slug, base_domain=base_domain)


domain_service = DomainPublicService()
