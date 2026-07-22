from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from backend.engines.deployment_history_engine.internal.service import DeploymentHistoryInternalService
from backend.engines.deployment_history_engine.schemas import (
    DeploymentHistoryCreateInput,
    DeploymentHistoryDetail,
    DeploymentHistoryPage,
    DeploymentHistoryRecord,
    DeploymentLogInput,
    DeploymentLogList,
    DeploymentLogRecord,
    HistoryWriteResult,
    ProviderResultSummary,
)
from backend.pipelines.deploy_pipeline.schemas import HistoryWriteIntent


class DeploymentHistoryPublicService:
    """Public Deployment History Engine API.

    Consumers must use this boundary. Direct database/table writes are forbidden.
    Deployment History Engine does not call GitHub or Cloudflare providers.
    """

    def __init__(self, internal: DeploymentHistoryInternalService | None = None) -> None:
        self._internal = internal or DeploymentHistoryInternalService()

    async def create_history_record(
        self,
        db: AsyncSession,
        input_data: DeploymentHistoryCreateInput,
    ) -> DeploymentHistoryRecord:
        return await self._internal.create_history_record(db, input_data)

    async def append_log(
        self,
        db: AsyncSession,
        *,
        deployment_id: str,
        input_data: DeploymentLogInput,
    ) -> DeploymentLogRecord:
        return await self._internal.append_log(db, deployment_id=deployment_id, input_data=input_data)

    async def consume_history_write_intent(
        self,
        db: AsyncSession,
        intent: HistoryWriteIntent,
    ) -> HistoryWriteResult:
        return await self._internal.consume_history_write_intent(db, intent)

    async def get_runtime_record(
        self,
        db: AsyncSession,
        *,
        deployment_id: str,
    ) -> DeploymentHistoryRecord | None:
        return await self._internal.get_runtime_record(
            db,
            deployment_id=deployment_id,
        )

    async def mark_started(self, db: AsyncSession, *, deployment_id: str) -> DeploymentHistoryRecord:
        return await self._internal.mark_started(db, deployment_id=deployment_id)

    async def mark_completed(
        self,
        db: AsyncSession,
        *,
        deployment_id: str,
        result: ProviderResultSummary | None = None,
    ) -> DeploymentHistoryRecord:
        return await self._internal.mark_completed(db, deployment_id=deployment_id, result=result)

    async def mark_failed(
        self,
        db: AsyncSession,
        *,
        deployment_id: str,
        error_summary: str,
        failure_code: str | None = None,
    ) -> DeploymentHistoryRecord:
        return await self._internal.mark_failed(
            db,
            deployment_id=deployment_id,
            error_summary=error_summary,
            failure_code=failure_code,
        )

    async def get_deployment_history(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        deployment_id: str,
    ) -> DeploymentHistoryDetail:
        return await self._internal.get_deployment_history(
            db,
            user_id=user_id,
            deployment_id=deployment_id,
        )

    async def list_project_deployments(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        project_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> DeploymentHistoryPage:
        return await self._internal.list_project_deployments(
            db,
            user_id=user_id,
            project_id=project_id,
            page=page,
            page_size=page_size,
        )

    async def get_deployment_logs(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        deployment_id: str,
    ) -> DeploymentLogList:
        return await self._internal.get_deployment_logs(
            db,
            user_id=user_id,
            deployment_id=deployment_id,
        )


deployment_history_service = DeploymentHistoryPublicService()
