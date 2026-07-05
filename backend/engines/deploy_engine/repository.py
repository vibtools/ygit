from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.ids import new_id
from backend.engines.deploy_engine.models import DeploymentModel
from backend.engines.deploy_engine.schemas import DeploymentRecord


class DeploymentRepository:
    """Database repository owned by Deploy Engine only."""

    async def create_queued_deployment(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        project_id: str,
        repository_id: str,
        analysis_id: str,
        domain_id: str | None = None,
        requested_by: str = "user",
        source_deployment_id: str | None = None,
    ) -> DeploymentRecord:
        now = datetime.now(timezone.utc)
        deployment = DeploymentModel(
            id=new_id("dep"),
            user_id=user_id,
            project_id=project_id,
            repository_id=repository_id,
            analysis_id=analysis_id,
            domain_id=domain_id,
            status="queued",
            requested_by=requested_by,
            source_deployment_id=source_deployment_id,
            queued_at=now,
            version=1,
        )
        db.add(deployment)
        await db.flush()
        return self.to_record(deployment)

    async def attach_job_id(self, db: AsyncSession, *, deployment_id: str, job_id: str) -> DeploymentRecord:
        deployment = await self.get_by_id(db, deployment_id)
        if deployment is None:
            raise ValueError("Deployment not found after creation.")
        deployment.job_id = job_id
        deployment.version += 1
        await db.flush()
        return self.to_record(deployment)

    async def get_by_id(self, db: AsyncSession, deployment_id: str) -> DeploymentModel | None:
        result = await db.execute(select(DeploymentModel).where(DeploymentModel.id == deployment_id))
        return result.scalar_one_or_none()

    async def mark_cancelled(self, db: AsyncSession, *, deployment: DeploymentModel) -> DeploymentRecord:
        deployment.status = "cancelled"
        deployment.cancelled_at = datetime.now(timezone.utc)
        deployment.version += 1
        await db.flush()
        return self.to_record(deployment)

    def to_record(self, deployment: DeploymentModel) -> DeploymentRecord:
        return DeploymentRecord(
            id=deployment.id,
            project_id=deployment.project_id,
            user_id=deployment.user_id,
            repository_id=deployment.repository_id,
            analysis_id=deployment.analysis_id,
            domain_id=deployment.domain_id,
            job_id=deployment.job_id,
            status=deployment.status,  # type: ignore[arg-type]
            requested_by=deployment.requested_by,  # type: ignore[arg-type]
            source_deployment_id=deployment.source_deployment_id,
            queued_at=deployment.queued_at,
            started_at=deployment.started_at,
            completed_at=deployment.completed_at,
            cancelled_at=deployment.cancelled_at,
            failure_code=deployment.failure_code,
            failure_summary=deployment.failure_summary,
            created_at=deployment.created_at,
            updated_at=deployment.updated_at,
            version=deployment.version,
        )
