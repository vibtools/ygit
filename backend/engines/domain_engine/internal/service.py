from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from backend.engines.domain_engine.errors import (
    DomainAccessDeniedError,
    DomainAlreadyAttachedError,
    DomainNotFoundError,
    DomainReleaseInvalidError,
    DomainSlugUnavailableError,
)
from backend.engines.domain_engine.internal.validators import build_full_url, validate_base_domain, validate_domain_slug
from backend.engines.domain_engine.repository import DomainRepository
from backend.engines.domain_engine.schemas import (
    DomainAvailability,
    DomainCheckInput,
    DomainDetail,
    DomainPreview,
    DomainRecord,
    DomainReleaseResult,
    DomainReserveInput,
)
from backend.engines.project_engine.public import project_service


class DomainInternalService:
    def __init__(self, repository: DomainRepository | None = None, project_public=project_service) -> None:
        self.repository = repository or DomainRepository()
        self.project_public = project_public

    async def check_slug_availability(self, db: AsyncSession, *, input_data: DomainCheckInput) -> DomainAvailability:
        slug = validate_domain_slug(input_data.slug)
        base_domain = validate_base_domain(input_data.base_domain)
        full_url = build_full_url(slug, base_domain)
        existing = await self.repository.get_active_by_slug_base(db, slug=slug, base_domain=base_domain)
        return DomainAvailability(
            slug=slug,
            base_domain=base_domain,
            available=existing is None,
            preview_url=full_url,
            reason=None if existing is None else "slug_unavailable",
        )

    async def reserve_project_slug(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        project_id: str,
        input_data: DomainReserveInput,
    ) -> DomainDetail:
        await self.project_public.validate_project_access(db, user_id=user_id, project_id=project_id)
        slug = validate_domain_slug(input_data.slug)
        base_domain = validate_base_domain(input_data.base_domain)
        full_url = build_full_url(slug, base_domain)

        existing_for_project = await self.repository.get_active_by_project(db, project_id=project_id)
        if existing_for_project is not None:
            if existing_for_project.user_id != user_id:
                raise DomainAccessDeniedError()
            if existing_for_project.slug == slug and existing_for_project.base_domain == base_domain:
                return self.to_detail(self.repository.to_record(existing_for_project))
            raise DomainAlreadyAttachedError()

        existing_for_slug = await self.repository.get_active_by_slug_base(db, slug=slug, base_domain=base_domain)
        if existing_for_slug is not None:
            raise DomainSlugUnavailableError()

        record = await self.repository.reserve_domain(
            db,
            user_id=user_id,
            project_id=project_id,
            slug=slug,
            base_domain=base_domain,
            full_url=full_url,
        )
        await db.commit()
        return self.to_detail(record)

    async def get_project_domain(self, db: AsyncSession, *, user_id: str, project_id: str) -> DomainDetail:
        await self.project_public.validate_project_access(db, user_id=user_id, project_id=project_id)
        domain = await self.repository.get_active_by_project(db, project_id=project_id)
        if domain is None:
            raise DomainNotFoundError()
        if domain.user_id != user_id:
            raise DomainAccessDeniedError()
        return self.to_detail(self.repository.to_record(domain))

    async def release_project_domain(self, db: AsyncSession, *, user_id: str, project_id: str) -> DomainReleaseResult:
        await self.project_public.validate_project_access(db, user_id=user_id, project_id=project_id)
        domain = await self.repository.get_active_by_project(db, project_id=project_id)
        if domain is None:
            raise DomainNotFoundError()
        if domain.user_id != user_id:
            raise DomainAccessDeniedError()
        if domain.status not in {"reserved", "attached"}:
            raise DomainReleaseInvalidError()
        record = await self.repository.release_domain(db, domain=domain)
        await db.commit()
        return DomainReleaseResult(
            released=True,
            domain_id=record.id,
            project_id=record.project_id,
            slug=record.slug,
            full_url=record.full_url,
        )

    def preview_domain(self, *, slug: str, base_domain: str = "ygit.net") -> DomainPreview:
        clean_slug = validate_domain_slug(slug)
        clean_base_domain = validate_base_domain(base_domain)
        return DomainPreview(
            slug=clean_slug,
            base_domain=clean_base_domain,
            full_url=build_full_url(clean_slug, clean_base_domain),
        )

    def to_detail(self, record: DomainRecord) -> DomainDetail:
        return DomainDetail(**record.model_dump())
