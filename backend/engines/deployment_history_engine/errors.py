from __future__ import annotations

from backend.core.exceptions import YGITError


class DeploymentHistoryNotFoundError(YGITError):
    def __init__(self) -> None:
        super().__init__(
            code="DEPLOYMENT_HISTORY_NOT_FOUND",
            message="Deployment history was not found.",
            status_code=404,
        )


class DeploymentLogNotFoundError(YGITError):
    def __init__(self) -> None:
        super().__init__(
            code="DEPLOYMENT_LOG_NOT_FOUND",
            message="Deployment log was not found.",
            status_code=404,
        )


class DeploymentLogWriteFailedError(YGITError):
    def __init__(self) -> None:
        super().__init__(
            code="DEPLOYMENT_LOG_WRITE_FAILED",
            message="Deployment log could not be written.",
            status_code=500,
        )


class DeploymentHistoryAccessDeniedError(YGITError):
    def __init__(self) -> None:
        super().__init__(
            code="DEPLOYMENT_HISTORY_ACCESS_DENIED",
            message="Deployment history access was denied.",
            status_code=403,
        )


class DeploymentStatusTransitionInvalidError(YGITError):
    def __init__(self) -> None:
        super().__init__(
            code="DEPLOYMENT_STATUS_TRANSITION_INVALID",
            message="Deployment history status transition is invalid.",
            status_code=409,
        )


class DeploymentHistoryMetadataUnsafeError(YGITError):
    def __init__(self, key: str) -> None:
        super().__init__(
            code="DEPLOYMENT_HISTORY_METADATA_UNSAFE",
            message="Deployment history metadata contains a forbidden secret-bearing key.",
            status_code=400,
            metadata={"key": key},
        )
