from __future__ import annotations

from backend.core.exceptions import YGITError


class AnalysisNotFoundError(YGITError):
    def __init__(self) -> None:
        super().__init__(code="ANALYSIS_NOT_FOUND", message="Repository analysis result was not found.", status_code=404)


class AnalysisAccessDeniedError(YGITError):
    def __init__(self) -> None:
        super().__init__(code="ANALYSIS_ACCESS_DENIED", message="Repository analysis access was denied.", status_code=403)


class AnalysisRepositoryNotReadyError(YGITError):
    def __init__(self) -> None:
        super().__init__(code="ANALYSIS_REPOSITORY_NOT_READY", message="Repository metadata is required before analysis.", status_code=409)


class AnalysisAlreadyRunningError(YGITError):
    def __init__(self) -> None:
        super().__init__(code="ANALYSIS_ALREADY_RUNNING", message="Repository analysis is already running.", status_code=409)


class AnalysisDeepJobFailedError(YGITError):
    def __init__(self) -> None:
        super().__init__(code="ANALYSIS_DEEP_JOB_FAILED", message="Deep repository analysis job failed.", status_code=500)
