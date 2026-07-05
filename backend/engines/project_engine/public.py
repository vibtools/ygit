from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from backend.engines.project_engine.internal.service import ProjectInternalService
from backend.engines.project_engine.schemas import ProjectAccess, ProjectCreateInput, ProjectDeleteResult, ProjectDetail, ProjectListFilters, ProjectUpdateInput
from backend.shared.schemas.pagination import Page


class ProjectPublicService:
    """Public Project Engine API. Other layers must not import internal services directly."""

    def __init__(self, internal: ProjectInternalService | None = None) -> None:
        self._internal = internal or ProjectInternalService()

    async def create_project(self, db: AsyncSession, *, user_id: str, input_data: ProjectCreateInput) -> ProjectDetail:
        return await self._internal.create_project(db, user_id=user_id, input_data=input_data)

    async def list_projects(self, db: AsyncSession, *, user_id: str, filters: ProjectListFilters) -> Page:
        return await self._internal.list_projects(db, user_id=user_id, filters=filters)

    async def get_project(self, db: AsyncSession, *, user_id: str, project_id: str) -> ProjectDetail:
        return await self._internal.get_project(db, user_id=user_id, project_id=project_id)

    async def rename_project(self, db: AsyncSession, *, user_id: str, project_id: str, input_data: ProjectUpdateInput) -> ProjectDetail:
        return await self._internal.rename_project(db, user_id=user_id, project_id=project_id, input_data=input_data)

    async def delete_project(self, db: AsyncSession, *, user_id: str, project_id: str) -> ProjectDeleteResult:
        return await self._internal.delete_project(db, user_id=user_id, project_id=project_id)

    async def validate_project_access(self, db: AsyncSession, *, user_id: str, project_id: str) -> ProjectAccess:
        return await self._internal.validate_project_access(db, user_id=user_id, project_id=project_id)


project_service = ProjectPublicService()
