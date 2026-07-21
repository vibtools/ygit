from __future__ import annotations

import inspect

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.exceptions import YGITError
from backend.workers.jobs import deploy_project, redeploy_project, repository_analysis_deep, webhook_event


def _accepts_db_keyword(handler: object) -> bool:
    """Return whether a job handler accepts worker-owned database context."""

    try:
        parameters = inspect.signature(handler).parameters.values()
    except (TypeError, ValueError):
        return False

    return any(
        parameter.name == "db"
        or parameter.kind == inspect.Parameter.VAR_KEYWORD
        for parameter in parameters
    )


class JobDispatcher:
    def __init__(self) -> None:
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

        if db is not None and _accepts_db_keyword(handler):
            await handler(
                payload,
                db=db,
            )
            return

        await handler(payload)
