from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from backend.engines.repository_analysis_engine.internal.service import RepositoryAnalysisInternalService
from backend.engines.repository_analysis_engine.schemas import AnalysisDetail, AnalysisJobRef


class RepositoryAnalysisPublicService:
    """Public Repository Analysis Engine API. Other layers must not import internal services directly."""

    def __init__(self, internal: RepositoryAnalysisInternalService | None = None) -> None:
        self._internal = internal or RepositoryAnalysisInternalService()

    async def run_quick_analysis(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        repository_id: str,
        project_id: str | None = None,
    ) -> AnalysisDetail:
        return await self._internal.run_quick_analysis(
            db,
            user_id=user_id,
            repository_id=repository_id,
            project_id=project_id,
        )

    async def queue_deep_analysis(self, db: AsyncSession, *, user_id: str, repository_id: str) -> AnalysisJobRef:
        return await self._internal.queue_deep_analysis(db, user_id=user_id, repository_id=repository_id)

    async def get_analysis_result(self, db: AsyncSession, *, user_id: str, analysis_id: str) -> AnalysisDetail:
        return await self._internal.get_analysis_result(db, user_id=user_id, analysis_id=analysis_id)

    async def recalculate_analysis(self, db: AsyncSession, *, user_id: str, analysis_id: str) -> AnalysisDetail:
        return await self._internal.recalculate_analysis(db, user_id=user_id, analysis_id=analysis_id)


repository_analysis_service = RepositoryAnalysisPublicService()
