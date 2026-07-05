from __future__ import annotations

from backend.core.exceptions import YGITError


class DomainEngineError(YGITError):
    """Base error for Domain Engine public API."""


class DomainSlugInvalidError(DomainEngineError):
    def __init__(self, message: str = "Domain slug is invalid.") -> None:
        super().__init__(
            code="DOMAIN_SLUG_INVALID",
            message=message,
            status_code=422,
        )


class DomainSlugUnavailableError(DomainEngineError):
    def __init__(self) -> None:
        super().__init__(
            code="DOMAIN_SLUG_UNAVAILABLE",
            message="Domain slug is not available.",
            status_code=409,
        )


class DomainNotFoundError(DomainEngineError):
    def __init__(self) -> None:
        super().__init__(
            code="DOMAIN_NOT_FOUND",
            message="Domain record was not found.",
            status_code=404,
        )


class DomainAccessDeniedError(DomainEngineError):
    def __init__(self) -> None:
        super().__init__(
            code="DOMAIN_ACCESS_DENIED",
            message="You do not have access to this domain record.",
            status_code=403,
        )


class DomainAlreadyAttachedError(DomainEngineError):
    def __init__(self) -> None:
        super().__init__(
            code="DOMAIN_ALREADY_ATTACHED",
            message="Project already has an active YGIT domain attached.",
            status_code=409,
        )


class DomainReleaseInvalidError(DomainEngineError):
    def __init__(self) -> None:
        super().__init__(
            code="DOMAIN_RELEASE_INVALID",
            message="Domain cannot be released from its current state.",
            status_code=409,
        )
