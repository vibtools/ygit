from backend.core.exceptions import YGITError


class AuthError(YGITError):
    """Auth Engine scoped error."""


class AuthRequiredError(AuthError):
    def __init__(self) -> None:
        super().__init__(
            code="AUTH_REQUIRED",
            message="Authentication is required.",
            status_code=401,
        )


class AuthSessionExpiredError(AuthError):
    def __init__(self) -> None:
        super().__init__(
            code="AUTH_SESSION_EXPIRED",
            message="Authentication session has expired.",
            status_code=401,
        )


class AuthInvalidSessionError(AuthError):
    def __init__(self) -> None:
        super().__init__(
            code="AUTH_INVALID_SESSION",
            message="Authentication session is invalid.",
            status_code=401,
        )


class AuthRoleRequiredError(AuthError):
    def __init__(self) -> None:
        super().__init__(
            code="AUTH_ROLE_REQUIRED",
            message="Required role is missing.",
            status_code=403,
        )


class AdminRoleRequiredError(AuthError):
    def __init__(self) -> None:
        super().__init__(
            code="ADMIN_ROLE_REQUIRED",
            message="Admin role is required.",
            status_code=403,
        )


class AuthOidcCallbackFailedError(AuthError):
    def __init__(self, message: str = "OIDC callback failed.") -> None:
        super().__init__(
            code="AUTH_OIDC_CALLBACK_FAILED",
            message=message,
            status_code=400,
        )


class AuthUserSyncFailedError(AuthError):
    def __init__(self) -> None:
        super().__init__(
            code="AUTH_USER_SYNC_FAILED",
            message="User identity could not be synchronized.",
            status_code=500,
        )


class AuthConfigurationError(AuthError):
    def __init__(self, message: str) -> None:
        super().__init__(
            code="AUTH_CONFIGURATION_INVALID",
            message=message,
            status_code=500,
        )


class AuthRedirectInvalidError(AuthError):
    def __init__(self) -> None:
        super().__init__(
            code="AUTH_REDIRECT_INVALID",
            message="Redirect target is invalid.",
            status_code=400,
        )
