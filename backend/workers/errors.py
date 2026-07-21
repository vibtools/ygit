from __future__ import annotations

from backend.core.exceptions import YGITError


class JobNotFoundError(YGITError):
    def __init__(self) -> None:
        super().__init__(
            code="JOB_NOT_FOUND",
            message="Job was not found.",
            status_code=404,
        )


class JobAccessDeniedError(YGITError):
    def __init__(self) -> None:
        super().__init__(
            code="JOB_ACCESS_DENIED",
            message="You do not have access to this job.",
            status_code=403,
        )


class JobLeaseFailedError(YGITError):
    def __init__(self) -> None:
        super().__init__(
            code="JOB_LEASE_FAILED",
            message="Worker could not lease the next job.",
            status_code=500,
        )


class JobTransitionInvalidError(YGITError):
    def __init__(self, message: str = "Job state transition is invalid.") -> None:
        super().__init__(
            code="JOB_STATUS_TRANSITION_INVALID",
            message=message,
            status_code=409,
        )


class WorkerBuildStageFailedError(YGITError):
    def __init__(
        self,
        *,
        deployment_id: str,
        build_status: str,
    ) -> None:
        super().__init__(
            code="DEPLOY_BUILD_STAGE_FAILED",
            message="Deployment build stage did not complete successfully.",
            status_code=500,
            metadata={
                "deployment_id": deployment_id,
                "build_status": build_status,
            },
        )


class WorkerDeploymentIncompleteError(YGITError):
    def __init__(
        self,
        *,
        deployment_id: str,
        pipeline_status: str,
        pipeline_stage: str | None = None,
        provider_calls_executed: bool | None = None,
    ) -> None:
        super().__init__(
            code="DEPLOY_PIPELINE_INCOMPLETE",
            message="Deployment pipeline did not prove provider deployment completion.",
            status_code=500,
            metadata={
                "deployment_id": deployment_id,
                "pipeline_status": pipeline_status,
                "pipeline_stage": pipeline_stage,
                "provider_calls_executed": provider_calls_executed,
            },
        )


class WorkerCloudflareCredentialAcquisitionBlockedError(
    YGITError
):
    def __init__(
        self,
        *,
        deployment_id: str,
        blockers: list[str],
    ) -> None:
        super().__init__(
            code=(
                "DEPLOY_CLOUDFLARE_CREDENTIAL_"
                "ACQUISITION_BLOCKED"
            ),
            message=(
                "Cloudflare deployment credential "
                "acquisition is not ready."
            ),
            status_code=409,
            metadata={
                "deployment_id": deployment_id,
                "blockers": list(blockers),
            },
        )
