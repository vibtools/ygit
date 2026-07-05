from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from backend.engines.domain_engine.errors import DomainAlreadyAttachedError, DomainSlugUnavailableError
from backend.engines.domain_engine.internal.service import DomainInternalService
from backend.engines.domain_engine.schemas import DomainCheckInput, DomainRecord, DomainReserveInput


class FakeDB:
    def __init__(self) -> None:
        self.committed = False

    async def commit(self) -> None:
        self.committed = True


class FakeProjectPublic:
    async def validate_project_access(self, db, *, user_id: str, project_id: str):
        return SimpleNamespace(user_id=user_id, project_id=project_id, allowed=True)


class FakeRepository:
    def __init__(self) -> None:
        self.by_slug: dict[tuple[str, str], object] = {}
        self.by_project: dict[str, object] = {}

    async def get_active_by_slug_base(self, db, *, slug: str, base_domain: str):
        return self.by_slug.get((slug, base_domain))

    async def get_active_by_project(self, db, *, project_id: str):
        return self.by_project.get(project_id)

    async def reserve_domain(self, db, *, user_id: str, project_id: str, slug: str, base_domain: str, full_url: str):
        record = DomainRecord(
            id="domain_1",
            project_id=project_id,
            user_id=user_id,
            slug=slug,
            base_domain=base_domain,
            full_url=full_url,
            status="reserved",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            released_at=None,
        )
        model = SimpleNamespace(**record.model_dump())
        self.by_slug[(slug, base_domain)] = model
        self.by_project[project_id] = model
        return record

    async def release_domain(self, db, *, domain):
        domain.status = "released"
        domain.released_at = datetime.now(timezone.utc)
        return self.to_record(domain)

    def to_record(self, model) -> DomainRecord:
        return DomainRecord(**model.__dict__)


@pytest.mark.asyncio
async def test_check_slug_availability_returns_preview_url() -> None:
    service = DomainInternalService(repository=FakeRepository(), project_public=FakeProjectPublic())
    result = await service.check_slug_availability(FakeDB(), input_data=DomainCheckInput(slug="portfolio"))
    assert result.available is True
    assert result.preview_url == "https://portfolio.ygit.net"


@pytest.mark.asyncio
async def test_reserve_project_slug_writes_through_domain_repository() -> None:
    db = FakeDB()
    service = DomainInternalService(repository=FakeRepository(), project_public=FakeProjectPublic())
    result = await service.reserve_project_slug(
        db,
        user_id="user_1",
        project_id="proj_1",
        input_data=DomainReserveInput(slug="portfolio"),
    )
    assert result.full_url == "https://portfolio.ygit.net"
    assert result.status == "reserved"
    assert db.committed is True


@pytest.mark.asyncio
async def test_reserve_project_slug_rejects_unavailable_slug() -> None:
    repo = FakeRepository()
    repo.by_slug[("portfolio", "ygit.net")] = SimpleNamespace(user_id="other", project_id="proj_other", slug="portfolio", base_domain="ygit.net")
    service = DomainInternalService(repository=repo, project_public=FakeProjectPublic())
    with pytest.raises(DomainSlugUnavailableError):
        await service.reserve_project_slug(
            FakeDB(),
            user_id="user_1",
            project_id="proj_1",
            input_data=DomainReserveInput(slug="portfolio"),
        )


@pytest.mark.asyncio
async def test_reserve_project_slug_rejects_second_active_project_domain() -> None:
    repo = FakeRepository()
    existing = SimpleNamespace(user_id="user_1", project_id="proj_1", slug="old", base_domain="ygit.net", status="reserved")
    repo.by_project["proj_1"] = existing
    service = DomainInternalService(repository=repo, project_public=FakeProjectPublic())
    with pytest.raises(DomainAlreadyAttachedError):
        await service.reserve_project_slug(
            FakeDB(),
            user_id="user_1",
            project_id="proj_1",
            input_data=DomainReserveInput(slug="new-slug"),
        )
