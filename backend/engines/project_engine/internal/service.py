from __future__ import annotations

from math import ceil

from sqlalchemy.ext.asyncio import AsyncSession

from backend.engines.project_engine.errors import (
    ProjectAccessDeniedError,
    ProjectAlreadyDeletedError,
    ProjectNotFoundError,
    ProjectSlugUnavailableError,
)
from backend.engines.project_engine.internal.validators import validate_project_name, validate_project_slug
from backend.engines.project_engine.repository import ProjectRepository
from backend.engines.repository_analysis_engine.public import (
    RepositoryAnalysisPublicService,
    repository_analysis_service,
)
from backend.engines.repository_engine.public import RepositoryPublicService, repository_service
from backend.engines.repository_engine.schemas import RepositoryMetadataInput
from backend.engines.project_engine.schemas import (
    ProjectAccess,
    ProjectCreateInput,
    ProjectDeleteResult,
    ProjectDetail,
    ProjectListFilters,
    ProjectRecord,
    ProjectSummary,
    ProjectUpdateInput,
)
from backend.shared.schemas.pagination import Page, Pagination


class ProjectInternalService:
    def __init__(
        self,
        repository: ProjectRepository | None = None,
        *,
        repository_public_service: RepositoryPublicService | None = None,
        analysis_public_service: RepositoryAnalysisPublicService | None = None,
    ) -> None:
        self.repository = repository or ProjectRepository()
        self.repository_service = repository_public_service or repository_service
        self.analysis_service = analysis_public_service or repository_analysis_service

    async def create_project(self, db: AsyncSession, *, user_id: str, input_data: ProjectCreateInput) -> ProjectDetail:
        name = validate_project_name(input_data.name)
        slug = validate_project_slug(input_data.slug)
        existing = await self.repository.get_by_slug(db, slug)
        if existing is not None:
            raise ProjectSlugUnavailableError()

        record = await self.repository.create_project(db, user_id=user_id, name=name, slug=slug)
        if not input_data.repository_url:
            await db.commit()
            return self.to_detail(record)

        repository_detail = await self.repository_service.fetch_repository_metadata(
            db,
            user_id=user_id,
            input_data=RepositoryMetadataInput(repository_url=input_data.repository_url),
        )
        analysis_detail = await self.analysis_service.run_quick_analysis(
            db,
            user_id=user_id,
            repository_id=repository_detail.id,
            project_id=record.id,
        )

        project = await self.repository.get_active_by_id(db, record.id)
        if project is None:
            raise ProjectNotFoundError()

        updated_record = await self.repository.attach_repository_analysis(
            db,
            project=project,
            repository_id=repository_detail.id,
            analysis_id=analysis_detail.id,
            deploy_ready=analysis_detail.deploy_ready,
        )
        await db.commit()
        return self.to_detail(updated_record)

    async def list_projects(self, db: AsyncSession, *, user_id: str, filters: ProjectListFilters) -> Page:
        records, total = await self.repository.list_projects(db, user_id=user_id, filters=filters)
        items = [self.to_summary(record).model_dump(mode="json") for record in records]
        return Page(
            items=items,
            pagination=Pagination(
                page=filters.page,
                page_size=filters.page_size,
                total_items=total,
                total_pages=ceil(total / filters.page_size) if total else 0,
            ),
        )

    async def get_project(self, db: AsyncSession, *, user_id: str, project_id: str) -> ProjectDetail:
        project = await self.repository.get_active_by_id(db, project_id)
        if project is None:
            raise ProjectNotFoundError()
        if project.user_id != user_id:
            raise ProjectAccessDeniedError()
        return self.to_detail(self.repository.to_record(project))

    async def rename_project(self, db: AsyncSession, *, user_id: str, project_id: str, input_data: ProjectUpdateInput) -> ProjectDetail:
        project = await self.repository.get_active_by_id(db, project_id)
        if project is None:
            raise ProjectNotFoundError()
        if project.user_id != user_id:
            raise ProjectAccessDeniedError()
        if project.deleted_at is not None:
            raise ProjectAlreadyDeletedError()
        name = validate_project_name(input_data.name or project.name)
        record = await self.repository.rename_project(db, project=project, name=name)
        await db.commit()
        return self.to_detail(record)

    async def delete_project(self, db: AsyncSession, *, user_id: str, project_id: str) -> ProjectDeleteResult:
        project = await self.repository.get_active_by_id(db, project_id)
        if project is None:
            raise ProjectNotFoundError()
        if project.user_id != user_id:
            raise ProjectAccessDeniedError()
        await self.repository.soft_delete_project(db, project=project)
        await db.commit()
        return ProjectDeleteResult(deleted=True, project_id=project_id)

    async def validate_project_access(self, db: AsyncSession, *, user_id: str, project_id: str) -> ProjectAccess:
        project = await self.repository.get_active_by_id(db, project_id)
        if project is None:
            raise ProjectNotFoundError()
        if project.user_id != user_id:
            raise ProjectAccessDeniedError()
        return ProjectAccess(project_id=project_id, user_id=user_id, allowed=True)

    def to_summary(self, record: ProjectRecord) -> ProjectSummary:
        return ProjectSummary(**record.model_dump())

    def to_detail(self, record: ProjectRecord) -> ProjectDetail:
        return ProjectDetail(**record.model_dump())
