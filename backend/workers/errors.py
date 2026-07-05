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
