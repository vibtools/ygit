from __future__ import annotations

from backend.core.exceptions import YGITError
from backend.workers.jobs import deploy_project, redeploy_project, repository_analysis_deep, webhook_event


class JobDispatcher:
    def __init__(self) -> None:
        self.handlers = {
            deploy_project.JOB_TYPE: deploy_project.run,
            redeploy_project.JOB_TYPE: redeploy_project.run,
            repository_analysis_deep.JOB_TYPE: repository_analysis_deep.run,
            webhook_event.JOB_TYPE: webhook_event.run,
        }

    async def dispatch(self, job_type: str, payload: dict[str, object]) -> None:
        handler = self.handlers.get(job_type)
        if handler is None:
            raise YGITError(
                code="JOB_TYPE_UNSUPPORTED",
                message=f"Job type is not enabled in skeleton v0.1.0: {job_type}",
                status_code=501,
            )
        await handler(payload)
