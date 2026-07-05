from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from backend.engines.repository_analysis_engine.errors import AnalysisAccessDeniedError, AnalysisNotFoundError
from backend.engines.repository_analysis_engine.internal.deep_analysis import DeepAnalysisQueue
from backend.engines.repository_analysis_engine.internal.quick_analysis import QuickAnalysisRunner
from backend.engines.repository_analysis_engine.internal.result_store import AnalysisResultStore
from backend.engines.repository_analysis_engine.repository import AnalysisResultRepository
from backend.engines.repository_analysis_engine.schemas import AnalysisDetail, AnalysisJobRef
from backend.engines.repository_engine.public import RepositoryPublicService, repository_service


class RepositoryAnalysisInternalService:
    def __init__(
        self,
        *,
        repository_public_service: RepositoryPublicService | None = None,
        quick_runner: QuickAnalysisRunner | None = None,
        result_store: AnalysisResultStore | None = None,
        deep_queue: DeepAnalysisQueue | None = None,
        analysis_repository: AnalysisResultRepository | None = None,
    ) -> None:
        self.repository_service = repository_public_service or repository_service
        self.quick_runner = quick_runner or QuickAnalysisRunner()
        self.result_store = result_store or AnalysisResultStore()
        self.deep_queue = deep_queue or DeepAnalysisQueue()
        self.analysis_repository = analysis_repository or AnalysisResultRepository()

    async def run_quick_analysis(self, db: AsyncSession, *, user_id: str, repository_id: str) -> AnalysisDetail:
        repository_input = await self.repository_service.prepare_analysis_input(db, user_id=user_id, repository_id=repository_id)
        quick_result = self.quick_runner.run(repository_input)
        return await self.result_store.store_quick_result(
            db,
            user_id=user_id,
            repository_id=repository_id,
            project_id=None,
            commit_sha=repository_input.latest_commit_sha,
            result=quick_result,
        )

    async def queue_deep_analysis(self, db: AsyncSession, *, user_id: str, repository_id: str) -> AnalysisJobRef:
        await self.repository_service.prepare_analysis_input(db, user_id=user_id, repository_id=repository_id)
        return await self.deep_queue.queue(repository_id=repository_id, user_id=user_id, db=db)

    async def get_analysis_result(self, db: AsyncSession, *, user_id: str, analysis_id: str) -> AnalysisDetail:
        model = await self.analysis_repository.get_active_by_id(db, analysis_id)
        if model is None:
            raise AnalysisNotFoundError()
        if model.user_id != user_id:
            raise AnalysisAccessDeniedError()
        return self.analysis_repository.to_detail(model)

    async def recalculate_analysis(self, db: AsyncSession, *, user_id: str, analysis_id: str) -> AnalysisDetail:
        existing = await self.get_analysis_result(db, user_id=user_id, analysis_id=analysis_id)
        return await self.run_quick_analysis(db, user_id=user_id, repository_id=existing.repository_id)
