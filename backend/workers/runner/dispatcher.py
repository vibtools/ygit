from __future__ import annotations

import inspect

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.exceptions import YGITError
from backend.workers.provider_execution_policy import (
    WorkerProviderExecutionPolicy,
)
from backend.workers.jobs import deploy_project, redeploy_project, repository_analysis_deep, webhook_event


def _accepts_keyword(
    handler: object,
    keyword: str,
) -> bool:
    """Return whether a handler accepts a trusted runtime keyword."""

    try:
        parameters = (
            inspect.signature(handler)
            .parameters
            .values()
        )
    except (TypeError, ValueError):
        return False

    return any(
        parameter.name == keyword
        or parameter.kind
        == inspect.Parameter.VAR_KEYWORD
        for parameter in parameters
    )


def _accepts_db_keyword(handler: object) -> bool:
    """Return whether a handler accepts worker-owned database context."""

    return _accepts_keyword(
        handler,
        "db",
    )


class JobDispatcher:
    def __init__(
        self,
        *,
        provider_execution_policy: (
            WorkerProviderExecutionPolicy | None
        ) = None,
    ) -> None:
        self.provider_execution_policy = (
            provider_execution_policy
        )
        self.handlers = {
            deploy_project.JOB_TYPE: deploy_project.run,
            redeploy_project.JOB_TYPE: redeploy_project.run,
            repository_analysis_deep.JOB_TYPE: repository_analysis_deep.run,
            webhook_event.JOB_TYPE: webhook_event.run,
        }

    async def dispatch(
        self,
        job_type: str,
        payload: dict[str, object],
        *,
        db: AsyncSession | None = None,
    ) -> None:
        handler = self.handlers.get(job_type)

        if handler is None:
            raise YGITError(
                code="JOB_TYPE_UNSUPPORTED",
                message=(
                    "Job type is not enabled in "
                    f"skeleton v0.1.0: {job_type}"
                ),
                status_code=501,
            )

        trusted_kwargs: dict[str, object] = {}

        if (
            db is not None
            and _accepts_db_keyword(handler)
        ):
            trusted_kwargs["db"] = db

        if (
            self.provider_execution_policy
            is not None
            and _accepts_keyword(
                handler,
                "provider_execution_policy",
            )
        ):
            trusted_kwargs[
                "provider_execution_policy"
            ] = self.provider_execution_policy

        await handler(
            payload,
            **trusted_kwargs,
        )
