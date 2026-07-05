from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from backend.engines.deploy_engine.internal.service import DeployInternalService
from backend.engines.deploy_engine.schemas import (
    DeployReadyResult,
    DeploymentCancelled,
    DeploymentDetail,
    DeploymentQueued,
    DeploymentRequestInput,
    RedeployRequestInput,
)


class DeployPublicService:
    """Public Deploy Engine API.

    API routes, worker job runners, and approved engines must use this boundary.
    Provider calls stay outside Deploy Engine and are handled by Deploy Pipeline.
    """

    def __init__(self, internal: DeployInternalService | None = None) -> None:
        self._internal = internal or DeployInternalService()

    async def validate_deploy_ready(self, db: AsyncSession, *, user_id: str, project_id: str) -> DeployReadyResult:
        return await self._internal.validate_deploy_ready(db, user_id=user_id, project_id=project_id)

    async def request_deployment(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        project_id: str,
        input_data: DeploymentRequestInput | None = None,
        trace_id: str | None = None,
    ) -> DeploymentQueued:
        return await self._internal.request_deployment(
            db,
            user_id=user_id,
            project_id=project_id,
            input_data=input_data,
            trace_id=trace_id,
        )

    async def request_redeploy(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        deployment_id: str,
        input_data: RedeployRequestInput | None = None,
        trace_id: str | None = None,
    ) -> DeploymentQueued:
        return await self._internal.request_redeploy(
            db,
            user_id=user_id,
            deployment_id=deployment_id,
            input_data=input_data,
            trace_id=trace_id,
        )

    async def cancel_deployment(self, db: AsyncSession, *, user_id: str, deployment_id: str) -> DeploymentCancelled:
        return await self._internal.cancel_deployment(db, user_id=user_id, deployment_id=deployment_id)

    async def get_deployment(self, db: AsyncSession, *, user_id: str, deployment_id: str) -> DeploymentDetail:
        return await self._internal.get_deployment(db, user_id=user_id, deployment_id=deployment_id)


deploy_service = DeployPublicService()
