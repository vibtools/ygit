from __future__ import annotations

import hashlib
import json
from math import ceil
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.engines.deployment_history_engine.errors import (
    DeploymentHistoryAccessDeniedError,
    DeploymentHistoryNotFoundError,
)
from backend.engines.deployment_history_engine.repository import DeploymentHistoryRepository
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
from backend.pipelines.deploy_pipeline.contract import DeployPipelineStage
from backend.pipelines.deploy_pipeline.schemas import HistoryWriteIntent


HISTORY_WRITE_KEYS_METADATA = "history_write_keys"
MAX_HISTORY_WRITE_KEYS = 64


class DeploymentHistoryInternalService:
    """Internal Deployment History Engine service.

    External modules must use deployment_history_engine.public only.
    """

    def __init__(self, repository: DeploymentHistoryRepository | None = None) -> None:
        self.repository = repository or DeploymentHistoryRepository()

    async def create_history_record(
        self,
        db: AsyncSession,
        input_data: DeploymentHistoryCreateInput,
    ) -> DeploymentHistoryRecord:
        record = await self.repository.create_history_record(
            db,
            deployment_id=input_data.deployment_id,
            project_id=input_data.project_id,
            status=input_data.status,
            provider=input_data.provider,
            metadata=input_data.metadata,
        )
        await db.commit()
        return record

    async def append_log(
        self,
        db: AsyncSession,
        *,
        deployment_id: str,
        input_data: DeploymentLogInput,
    ) -> DeploymentLogRecord:
        context = await self._require_deployment_context(db, deployment_id)
        log = await self.repository.append_log(
            db,
            deployment_id=deployment_id,
            project_id=context.project_id,
            level=input_data.level,
            message=input_data.message,
            metadata=input_data.metadata,
        )
        await db.commit()
        return log

    async def consume_history_write_intent(
        self,
        db: AsyncSession,
        intent: HistoryWriteIntent,
    ) -> HistoryWriteResult:
        context = await self._require_deployment_context(db, intent.deployment_id)
        existing = await self.repository.get_history_record(db, intent.deployment_id)
        intent_key = self._history_write_key(intent)
        processed_keys = self._history_write_keys(existing)

        if (
            existing is not None
            and intent_key in processed_keys
        ):
            return HistoryWriteResult(
                deployment_id=intent.deployment_id,
                status=existing.status,
                logs_written=0,
                provider_summary_written=False,
            )

        if existing is None:
            await self.repository.create_history_record(
                db,
                deployment_id=intent.deployment_id,
                project_id=context.project_id,
                status=intent.history_status,
                provider=None,
                metadata={"source_event": str(intent.event_name)},
            )

        provider_result = self._provider_result_from_intent(intent)
        metadata: dict[str, Any] = dict(intent.metadata or {})
        metadata["pipeline_stage"] = str(intent.stage.value if isinstance(intent.stage, DeployPipelineStage) else intent.stage)
        metadata["pipeline_event"] = str(intent.event_name)
        metadata[HISTORY_WRITE_KEYS_METADATA] = (
            [
                *processed_keys,
                intent_key,
            ][-MAX_HISTORY_WRITE_KEYS:]
        )

        await self.repository.update_history_status(
            db,
            deployment_id=intent.deployment_id,
            status=intent.history_status,
            provider_summary=provider_result.model_dump(mode="json") if provider_result else None,
            provider=provider_result.provider if provider_result else None,
            provider_project_id=provider_result.provider_project_id if provider_result else None,
            provider_deployment_id=provider_result.provider_deployment_id if provider_result else None,
            deployment_url=provider_result.deployment_url if provider_result else None,
            metadata=metadata,
        )

        for entry in intent.log_entries:
            await self.repository.append_log(
                db,
                deployment_id=intent.deployment_id,
                project_id=context.project_id,
                level=entry.level,
                message=entry.message,
                metadata=entry.metadata,
            )
        await db.commit()
        return HistoryWriteResult(
            deployment_id=intent.deployment_id,
            status=intent.history_status,
            logs_written=len(intent.log_entries),
            provider_summary_written=provider_result is not None,
        )

    async def get_runtime_record(
        self,
        db: AsyncSession,
        *,
        deployment_id: str,
    ) -> DeploymentHistoryRecord | None:
        await self._require_deployment_context(
            db,
            deployment_id,
        )
        return await self.repository.get_history_record(
            db,
            deployment_id,
        )

    async def mark_started(self, db: AsyncSession, *, deployment_id: str) -> DeploymentHistoryRecord:
        await self._ensure_history_exists(db, deployment_id)
        record = await self.repository.update_history_status(db, deployment_id=deployment_id, status="running")
        await db.commit()
        return record

    async def mark_completed(
        self,
        db: AsyncSession,
        *,
        deployment_id: str,
        result: ProviderResultSummary | None = None,
    ) -> DeploymentHistoryRecord:
        await self._ensure_history_exists(db, deployment_id)
        record = await self.repository.update_history_status(
            db,
            deployment_id=deployment_id,
            status="completed",
            provider_summary=result.model_dump(mode="json") if result else None,
            provider=result.provider if result else None,
            provider_project_id=result.provider_project_id if result else None,
            provider_deployment_id=result.provider_deployment_id if result else None,
            deployment_url=result.deployment_url if result else None,
        )
        await db.commit()
        return record

    async def mark_failed(
        self,
        db: AsyncSession,
        *,
        deployment_id: str,
        error_summary: str,
        failure_code: str | None = None,
    ) -> DeploymentHistoryRecord:
        await self._ensure_history_exists(db, deployment_id)
        record = await self.repository.update_history_status(
            db,
            deployment_id=deployment_id,
            status="failed",
            failure_code=failure_code,
            failure_summary=error_summary,
        )
        await db.commit()
        return record

    async def get_deployment_history(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        deployment_id: str,
    ) -> DeploymentHistoryDetail:
        context = await self._require_deployment_context(db, deployment_id)
        if context.user_id != user_id:
            raise DeploymentHistoryAccessDeniedError()
        history = await self.repository.get_history_record(db, deployment_id)
        if history is None:
            raise DeploymentHistoryNotFoundError()
        logs = await self.repository.list_logs(db, deployment_id=deployment_id)
        return DeploymentHistoryDetail(history=history, logs=logs)

    async def list_project_deployments(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        project_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> DeploymentHistoryPage:
        safe_page = max(1, page)
        safe_page_size = min(max(1, page_size), 100)
        items, total = await self.repository.list_project_deployments(
            db,
            project_id=project_id,
            page=safe_page,
            page_size=safe_page_size,
        )
        visible_items = []
        for item in items:
            context = await self.repository.get_deployment_context(db, item.deployment_id)
            if context and context.user_id == user_id:
                visible_items.append(item)
        total_pages = ceil(total / safe_page_size) if total else 0
        return DeploymentHistoryPage(
            items=visible_items,
            pagination={
                "page": safe_page,
                "page_size": safe_page_size,
                "total_items": total,
                "total_pages": total_pages,
            },
        )

    async def get_deployment_logs(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        deployment_id: str,
    ) -> DeploymentLogList:
        context = await self._require_deployment_context(db, deployment_id)
        if context.user_id != user_id:
            raise DeploymentHistoryAccessDeniedError()
        logs = await self.repository.list_logs(db, deployment_id=deployment_id)
        return DeploymentLogList(deployment_id=deployment_id, logs=logs)

    async def _ensure_history_exists(self, db: AsyncSession, deployment_id: str) -> None:
        context = await self._require_deployment_context(db, deployment_id)
        existing = await self.repository.get_history_record(db, deployment_id)
        if existing is None:
            await self.repository.create_history_record(
                db,
                deployment_id=deployment_id,
                project_id=context.project_id,
                status="created",
            )

    async def _require_deployment_context(self, db: AsyncSession, deployment_id: str):
        context = await self.repository.get_deployment_context(db, deployment_id)
        if context is None:
            raise DeploymentHistoryNotFoundError()
        return context

    @staticmethod
    def _history_write_key(
        intent: HistoryWriteIntent,
    ) -> str:
        payload = intent.model_dump(
            mode="json",
            exclude_none=False,
        )
        encoded = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8")
        return hashlib.sha256(
            encoded
        ).hexdigest()

    @staticmethod
    def _history_write_keys(
        record: DeploymentHistoryRecord | None,
    ) -> list[str]:
        if record is None:
            return []

        metadata = dict(
            getattr(record, "metadata", {})
            or {}
        )
        raw_keys = metadata.get(
            HISTORY_WRITE_KEYS_METADATA,
            [],
        )

        if not isinstance(raw_keys, list):
            return []

        keys = [
            value
            for value in raw_keys
            if isinstance(value, str)
            and value
        ]
        return keys[-MAX_HISTORY_WRITE_KEYS:]

    def _provider_result_from_intent(self, intent: HistoryWriteIntent) -> ProviderResultSummary | None:
        if intent.provider_summary is None:
            return None
        provider = intent.provider_summary.provider
        return ProviderResultSummary(
            provider=provider,
            provider_project_id=intent.provider_summary.provider_project_id,
            provider_deployment_id=intent.provider_summary.provider_deployment_id,
            deployment_url=intent.provider_summary.deployment_url,
            status=intent.provider_summary.status,
            action=intent.provider_summary.action,
            metadata=intent.provider_summary.metadata,
        )
