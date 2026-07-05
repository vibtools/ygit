from __future__ import annotations

from backend.core.exceptions import YGITError


class AuditEngineError(YGITError):
    """Base error for Audit Engine public API."""


class AuditLogWriteFailedError(AuditEngineError):
    def __init__(self) -> None:
        super().__init__(
            code="AUDIT_LOG_WRITE_FAILED",
            message="Audit log could not be written.",
            status_code=500,
        )


class AuditLogNotFoundError(AuditEngineError):
    def __init__(self) -> None:
        super().__init__(
            code="AUDIT_LOG_NOT_FOUND",
            message="Audit log was not found.",
            status_code=404,
        )


class AuditLogAccessDeniedError(AuditEngineError):
    def __init__(self) -> None:
        super().__init__(
            code="AUDIT_LOG_ACCESS_DENIED",
            message="Audit log access was denied.",
            status_code=403,
        )


class AuditEventInvalidError(AuditEngineError):
    def __init__(self) -> None:
        super().__init__(
            code="AUDIT_EVENT_INVALID",
            message="Audit event is invalid.",
            status_code=400,
        )


class AuditDeleteForbiddenError(AuditEngineError):
    def __init__(self) -> None:
        super().__init__(
            code="AUDIT_DELETE_FORBIDDEN",
            message="Audit logs are immutable and cannot be deleted.",
            status_code=403,
        )
