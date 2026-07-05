from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.ids import new_id
from backend.engines.deploy_engine.models import DeploymentModel
from backend.engines.deployment_history_engine.errors import (
    DeploymentHistoryNotFoundError,
    DeploymentLogWriteFailedError,
)
from backend.engines.deployment_history_engine.models import (
    DeploymentHistoryModel,
    DeploymentLogModel,
)
from backend.engines.deployment_history_engine.schemas import (
    DeploymentHistoryRecord,
    DeploymentLogRecord,
    DeploymentSummary,
    HistoryStatus,
)


class DeploymentHistoryRepository:
    """Database repository owned by Deployment History Engine only."""

    async def get_deployment_context(
        self,
        db: AsyncSession,
        deployment_id: str,
    ) -> DeploymentModel | None:
        result = await db.execute(select(DeploymentModel).where(DeploymentModel.id == deployment_id))
        return result.scalar_one_or_none()

    async def create_history_record(
        self,
        db: AsyncSession,
        *,
        deployment_id: str,
        project_id: str,
        status: HistoryStatus = "created",
        provider: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> DeploymentHistoryRecord:
        existing = await self.get_history_model(db, deployment_id)
        if existing is not None:
            return self.to_history_record(existing)
        history = DeploymentHistoryModel(
            id=new_id("hist"),
            deployment_id=deployment_id,
            project_id=project_id,
            status=status,
            provider=provider,
            metadata_json=metadata or {},
            provider_summary={},
        )
        db.add(history)
        await db.flush()
        return self.to_history_record(history)

    async def get_history_model(
        self,
        db: AsyncSession,
        deployment_id: str,
    ) -> DeploymentHistoryModel | None:
        result = await db.execute(
            select(DeploymentHistoryModel).where(DeploymentHistoryModel.deployment_id == deployment_id)
        )
        return result.scalar_one_or_none()

    async def get_history_record(
        self,
        db: AsyncSession,
        deployment_id: str,
    ) -> DeploymentHistoryRecord | None:
        model = await self.get_history_model(db, deployment_id)
        return self.to_history_record(model) if model else None

    async def update_history_status(
        self,
        db: AsyncSession,
        *,
        deployment_id: str,
        status: HistoryStatus,
        provider_summary: dict[str, Any] | None = None,
        provider: str | None = None,
        provider_project_id: str | None = None,
        provider_deployment_id: str | None = None,
        deployment_url: str | None = None,
        failure_code: str | None = None,
        failure_summary: str | None = None,
        duration_ms: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> DeploymentHistoryRecord:
        model = await self.get_history_model(db, deployment_id)
        if model is None:
            raise DeploymentHistoryNotFoundError()
        model.status = status
        if provider is not None:
            model.provider = provider
        if provider_project_id is not None:
            model.provider_project_id = provider_project_id
        if provider_deployment_id is not None:
            model.provider_deployment_id = provider_deployment_id
        if deployment_url is not None:
            model.deployment_url = deployment_url
        if failure_code is not None:
            model.failure_code = failure_code
        if failure_summary is not None:
            model.failure_summary = failure_summary
        if duration_ms is not None:
            model.duration_ms = duration_ms
        if provider_summary is not None:
            model.provider_summary = provider_summary
        if metadata:
            merged = dict(model.metadata_json or {})
            merged.update(metadata)
            model.metadata_json = merged
        await db.flush()
        return self.to_history_record(model)

    async def next_log_sequence(self, db: AsyncSession, deployment_id: str) -> int:
        result = await db.execute(
            select(func.max(DeploymentLogModel.sequence)).where(
                DeploymentLogModel.deployment_id == deployment_id
            )
        )
        value = result.scalar_one_or_none()
        return int(value or 0) + 1

    async def append_log(
        self,
        db: AsyncSession,
        *,
        deployment_id: str,
        project_id: str,
        level: str,
        message: str,
        metadata: dict[str, Any] | None = None,
    ) -> DeploymentLogRecord:
        try:
            sequence = await self.next_log_sequence(db, deployment_id)
            log = DeploymentLogModel(
                id=new_id("log"),
                deployment_id=deployment_id,
                project_id=project_id,
                level=level,
                message=message,
                metadata_json=metadata or {},
                sequence=sequence,
                created_at=datetime.now(timezone.utc),
            )
            db.add(log)
            await db.flush()
            return self.to_log_record(log)
        except Exception as exc:  # pragma: no cover - defensive DB wrapper
            raise DeploymentLogWriteFailedError() from exc

    async def list_logs(
        self,
        db: AsyncSession,
        *,
        deployment_id: str,
    ) -> list[DeploymentLogRecord]:
        result = await db.execute(
            select(DeploymentLogModel)
            .where(DeploymentLogModel.deployment_id == deployment_id)
            .order_by(DeploymentLogModel.sequence.asc())
        )
        return [self.to_log_record(row) for row in result.scalars().all()]

    async def list_project_deployments(
        self,
        db: AsyncSession,
        *,
        project_id: str,
        page: int,
        page_size: int,
    ) -> tuple[list[DeploymentSummary], int]:
        total_result = await db.execute(
            select(func.count()).select_from(DeploymentHistoryModel).where(
                DeploymentHistoryModel.project_id == project_id
            )
        )
        total = int(total_result.scalar_one() or 0)
        result = await db.execute(
            select(DeploymentHistoryModel)
            .where(DeploymentHistoryModel.project_id == project_id)
            .order_by(desc(DeploymentHistoryModel.created_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = [self.to_summary(row) for row in result.scalars().all()]
        return items, total

    def to_history_record(self, model: DeploymentHistoryModel) -> DeploymentHistoryRecord:
        return DeploymentHistoryRecord(
            id=model.id,
            deployment_id=model.deployment_id,
            project_id=model.project_id,
            status=model.status,  # type: ignore[arg-type]
            provider=model.provider,
            provider_project_id=model.provider_project_id,
            provider_deployment_id=model.provider_deployment_id,
            deployment_url=model.deployment_url,
            duration_ms=model.duration_ms,
            failure_code=model.failure_code,
            failure_summary=model.failure_summary,
            provider_summary=dict(model.provider_summary or {}),
            metadata=dict(model.metadata_json or {}),
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def to_log_record(self, model: DeploymentLogModel) -> DeploymentLogRecord:
        return DeploymentLogRecord(
            id=model.id,
            deployment_id=model.deployment_id,
            project_id=model.project_id,
            level=model.level,  # type: ignore[arg-type]
            message=model.message,
            metadata=dict(model.metadata_json or {}),
            sequence=int(model.sequence),
            created_at=model.created_at,
        )

    def to_summary(self, model: DeploymentHistoryModel) -> DeploymentSummary:
        return DeploymentSummary(
            deployment_id=model.deployment_id,
            project_id=model.project_id,
            status=model.status,  # type: ignore[arg-type]
            deployment_url=model.deployment_url,
            duration_ms=model.duration_ms,
            failure_code=model.failure_code,
            failure_summary=model.failure_summary,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
