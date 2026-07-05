from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.ids import new_id
from backend.engines.project_engine.models import ProjectModel, ProjectSettingsModel
from backend.engines.project_engine.schemas import ProjectListFilters, ProjectRecord


class ProjectRepository:
    """Database repository owned by Project Engine only."""

    async def get_by_id(self, db: AsyncSession, project_id: str) -> ProjectModel | None:
        result = await db.execute(select(ProjectModel).where(ProjectModel.id == project_id))
        return result.scalar_one_or_none()

    async def get_active_by_id(self, db: AsyncSession, project_id: str) -> ProjectModel | None:
        result = await db.execute(
            select(ProjectModel).where(ProjectModel.id == project_id, ProjectModel.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def get_by_slug(self, db: AsyncSession, slug: str) -> ProjectModel | None:
        result = await db.execute(select(ProjectModel).where(ProjectModel.slug == slug, ProjectModel.deleted_at.is_(None)))
        return result.scalar_one_or_none()

    async def create_project(self, db: AsyncSession, *, user_id: str, name: str, slug: str) -> ProjectRecord:
        project = ProjectModel(id=new_id("proj"), user_id=user_id, name=name, slug=slug, status="draft", version=1)
        db.add(project)
        await db.flush()
        db.add(ProjectSettingsModel(id=new_id("setting"), project_id=project.id))
        await db.flush()
        return self.to_record(project)

    async def list_projects(self, db: AsyncSession, *, user_id: str, filters: ProjectListFilters) -> tuple[list[ProjectRecord], int]:
        conditions = [ProjectModel.user_id == user_id, ProjectModel.deleted_at.is_(None)]
        if filters.status is not None:
            conditions.append(ProjectModel.status == filters.status)
        if filters.search:
            like = f"%{filters.search.strip()}%"
            conditions.append(or_(ProjectModel.name.ilike(like), ProjectModel.slug.ilike(like)))

        count_result = await db.execute(select(func.count()).select_from(ProjectModel).where(*conditions))
        total = int(count_result.scalar_one())
        result = await db.execute(
            select(ProjectModel)
            .where(*conditions)
            .order_by(ProjectModel.created_at.desc())
            .offset((filters.page - 1) * filters.page_size)
            .limit(filters.page_size)
        )
        return [self.to_record(row) for row in result.scalars().all()], total

    async def rename_project(self, db: AsyncSession, *, project: ProjectModel, name: str) -> ProjectRecord:
        project.name = name
        project.version += 1
        await db.flush()
        return self.to_record(project)

    async def soft_delete_project(self, db: AsyncSession, *, project: ProjectModel) -> ProjectRecord:
        project.status = "deleted"
        project.deleted_at = datetime.now(timezone.utc)
        project.version += 1
        await db.flush()
        return self.to_record(project)

    def to_record(self, project: ProjectModel) -> ProjectRecord:
        return ProjectRecord(
            id=project.id,
            user_id=project.user_id,
            name=project.name,
            slug=project.slug,
            status=project.status,  # type: ignore[arg-type]
            repository_id=project.repository_id,
            analysis_id=project.analysis_id,
            current_deployment_id=project.current_deployment_id,
            created_at=project.created_at,
            updated_at=project.updated_at,
            deleted_at=project.deleted_at,
            version=project.version,
        )
