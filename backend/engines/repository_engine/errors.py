from __future__ import annotations

from backend.core.exceptions import YGITError


class RepositoryError(YGITError):
    """Base Repository Engine error."""


class RepositoryUrlInvalidError(RepositoryError):
    def __init__(self) -> None:
        super().__init__(
            code="REPOSITORY_URL_INVALID",
            message="Repository URL is invalid.",
            status_code=422,
        )


class RepositoryProviderUnsupportedError(RepositoryError):
    def __init__(self) -> None:
        super().__init__(
            code="REPOSITORY_PROVIDER_UNSUPPORTED",
            message="Repository provider is not supported.",
            status_code=422,
        )


class RepositoryNotFoundError(RepositoryError):
    def __init__(self) -> None:
        super().__init__(
            code="REPOSITORY_NOT_FOUND",
            message="Repository metadata was not found.",
            status_code=404,
        )


class RepositoryAccessDeniedError(RepositoryError):
    def __init__(self) -> None:
        super().__init__(
            code="REPOSITORY_ACCESS_DENIED",
            message="Repository metadata is not accessible for this user.",
            status_code=403,
        )


class RepositoryMetadataFetchFailedError(RepositoryError):
    def __init__(self, message: str = "Repository metadata fetch failed.") -> None:
        super().__init__(
            code="REPOSITORY_METADATA_FETCH_FAILED",
            message=message,
            status_code=502,
        )


class RepositoryDefaultBranchMissingError(RepositoryError):
    def __init__(self) -> None:
        super().__init__(
            code="REPOSITORY_DEFAULT_BRANCH_MISSING",
            message="Repository default branch is missing.",
            status_code=422,
        )
