from __future__ import annotations

from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.exceptions import YGITError
from backend.engines.deployment_history_engine.public import (
    DeploymentHistoryPublicService,
    deployment_history_service,
)
from backend.pipelines.deploy_pipeline.schemas import (
    DeploymentPipelineResult,
)


class RuntimeHistoryService(Protocol):
    async def get_runtime_record(
        self,
        db: AsyncSession,
        *,
        deployment_id: str,
    ):
        ...

    async def mark_started(
        self,
        db: AsyncSession,
        *,
        deployment_id: str,
    ):
        ...

    async def consume_history_write_intent(
        self,
        db: AsyncSession,
        intent,
    ):
        ...

    async def mark_failed(
        self,
        db: AsyncSession,
        *,
        deployment_id: str,
        error_summary: str,
        failure_code: str | None = None,
    ):
        ...


async def deployment_history_completed(
    db: AsyncSession,
    deployment_id: str,
    *,
    service: RuntimeHistoryService = (
        deployment_history_service
    ),
) -> bool:
    record = await service.get_runtime_record(
        db,
        deployment_id=deployment_id,
    )
    return (
        record is not None
        and str(record.status) == "completed"
    )


async def mark_deployment_started(
    db: AsyncSession,
    deployment_id: str,
    *,
    service: RuntimeHistoryService = (
        deployment_history_service
    ),
) -> None:
    await service.mark_started(
        db,
        deployment_id=deployment_id,
    )


async def persist_pipeline_result_history(
    db: AsyncSession,
    result: DeploymentPipelineResult | object,
    *,
    service: RuntimeHistoryService = (
        deployment_history_service
    ),
) -> int:
    intents = list(
        getattr(result, "history_writes", ())
        or ()
    )

    for intent in intents:
        await service.consume_history_write_intent(
            db,
            intent,
        )

    return len(intents)


def safe_failure_details(
    error: Exception,
) -> tuple[str, str]:
    if isinstance(error, YGITError):
        return error.code, error.message

    return (
        "JOB_EXECUTION_FAILED",
        "Deployment execution failed.",
    )


async def persist_deployment_failure_safely(
    db: AsyncSession,
    deployment_id: str,
    error: Exception,
    *,
    service: RuntimeHistoryService = (
        deployment_history_service
    ),
) -> bool:
    failure_code, error_summary = (
        safe_failure_details(error)
    )

    try:
        await db.rollback()
    except Exception:
        pass

    try:
        await service.mark_failed(
            db,
            deployment_id=deployment_id,
            error_summary=error_summary,
            failure_code=failure_code,
        )
    except Exception:
        return False

    return True
