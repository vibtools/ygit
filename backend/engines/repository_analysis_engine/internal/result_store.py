from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from backend.engines.repository_analysis_engine.repository import AnalysisResultRepository
from backend.engines.repository_analysis_engine.schemas import AnalysisDetail, QuickAnalysisResult


class AnalysisResultStore:
    def __init__(self, repository: AnalysisResultRepository | None = None) -> None:
        self.repository = repository or AnalysisResultRepository()

    async def store_quick_result(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        repository_id: str,
        project_id: str | None,
        commit_sha: str | None,
        result: QuickAnalysisResult,
    ) -> AnalysisDetail:
        record = await self.repository.create_quick_result(
            db,
            user_id=user_id,
            repository_id=repository_id,
            project_id=project_id,
            commit_sha=commit_sha,
            result=result,
        )
        await db.commit()
        return self.repository.to_detail(record)
