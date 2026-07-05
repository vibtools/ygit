from __future__ import annotations

from backend.core.exceptions import YGITError


class ConnectedAccountsError(YGITError):
    """Base Connected Accounts Module error."""


class ProviderNotSupportedError(ConnectedAccountsError):
    def __init__(self) -> None:
        super().__init__(
            code="PROVIDER_NOT_SUPPORTED",
            message="Provider is not supported by Connected Accounts Module.",
            status_code=422,
        )


class ConnectedAccountNotFoundError(ConnectedAccountsError):
    def __init__(self) -> None:
        super().__init__(
            code="CONNECTED_ACCOUNT_NOT_FOUND",
            message="Connected account was not found.",
            status_code=404,
        )


class ProviderAlreadyConnectedError(ConnectedAccountsError):
    def __init__(self) -> None:
        super().__init__(
            code="PROVIDER_ALREADY_CONNECTED",
            message="Provider is already connected.",
            status_code=409,
        )


class ProviderNotConnectedError(ConnectedAccountsError):
    def __init__(self) -> None:
        super().__init__(
            code="PROVIDER_NOT_CONNECTED",
            message="Provider is not connected.",
            status_code=409,
        )


class ProviderOAuthFailedError(ConnectedAccountsError):
    def __init__(self, message: str = "Provider OAuth flow failed.") -> None:
        super().__init__(
            code="PROVIDER_OAUTH_FAILED",
            message=message,
            status_code=400,
        )


class ProviderTokenInvalidError(ConnectedAccountsError):
    def __init__(self) -> None:
        super().__init__(
            code="PROVIDER_TOKEN_INVALID",
            message="Provider token reference is invalid.",
            status_code=401,
        )


class ProviderConnectionFailedError(ConnectedAccountsError):
    def __init__(self, message: str = "Provider connection validation failed.") -> None:
        super().__init__(
            code="PROVIDER_CONNECTION_FAILED",
            message=message,
            status_code=502,
        )
