from __future__ import annotations

from backend.core.exceptions import YGITError


class NotificationEngineError(YGITError):
    """Base error for Notification Engine public API."""


class NotificationNotFoundError(NotificationEngineError):
    def __init__(self) -> None:
        super().__init__(
            code="NOTIFICATION_NOT_FOUND",
            message="Notification was not found.",
            status_code=404,
        )


class NotificationAccessDeniedError(NotificationEngineError):
    def __init__(self) -> None:
        super().__init__(
            code="NOTIFICATION_ACCESS_DENIED",
            message="Notification access was denied.",
            status_code=403,
        )


class NotificationCreateFailedError(NotificationEngineError):
    def __init__(self, message: str = "Notification could not be created.") -> None:
        super().__init__(
            code="NOTIFICATION_CREATE_FAILED",
            message=message,
            status_code=500,
        )


class NotificationChannelUnsupportedError(NotificationEngineError):
    def __init__(self) -> None:
        super().__init__(
            code="NOTIFICATION_CHANNEL_UNSUPPORTED",
            message="Notification channel is not supported in MVP.",
            status_code=422,
        )
