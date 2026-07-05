from backend.core.exceptions import YGITError


class ProjectNotFoundError(YGITError):
    def __init__(self) -> None:
        super().__init__(code="PROJECT_NOT_FOUND", message="Project was not found.", status_code=404)


class ProjectAccessDeniedError(YGITError):
    def __init__(self) -> None:
        super().__init__(code="PROJECT_ACCESS_DENIED", message="Project access was denied.", status_code=403)


class ProjectNameInvalidError(YGITError):
    def __init__(self) -> None:
        super().__init__(code="PROJECT_NAME_INVALID", message="Project name is invalid.", status_code=422)


class ProjectSlugInvalidError(YGITError):
    def __init__(self) -> None:
        super().__init__(code="PROJECT_SLUG_INVALID", message="Project slug is invalid.", status_code=422)


class ProjectSlugUnavailableError(YGITError):
    def __init__(self) -> None:
        super().__init__(code="PROJECT_SLUG_UNAVAILABLE", message="Project slug is unavailable.", status_code=409)


class ProjectAlreadyDeletedError(YGITError):
    def __init__(self) -> None:
        super().__init__(code="PROJECT_ALREADY_DELETED", message="Project is already deleted.", status_code=409)


class ProjectRepositoryRequiredError(YGITError):
    def __init__(self) -> None:
        super().__init__(code="PROJECT_REPOSITORY_REQUIRED", message="Project repository is required.", status_code=422)
