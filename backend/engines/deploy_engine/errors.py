from __future__ import annotations

from backend.core.exceptions import YGITError


class DeploymentNotFoundError(YGITError):
    def __init__(self) -> None:
        super().__init__(code="DEPLOYMENT_NOT_FOUND", message="Deployment was not found.", status_code=404)


class DeploymentAccessDeniedError(YGITError):
    def __init__(self) -> None:
        super().__init__(code="DEPLOYMENT_ACCESS_DENIED", message="Deployment access was denied.", status_code=403)


class DeploymentAlreadyRunningError(YGITError):
    def __init__(self) -> None:
        super().__init__(code="DEPLOYMENT_ALREADY_RUNNING", message="Deployment is already queued or running.", status_code=409)


class DeploymentProjectNotReadyError(YGITError):
    def __init__(self, message: str = "Project is not ready for deployment.") -> None:
        super().__init__(code="DEPLOYMENT_PROJECT_NOT_READY", message=message, status_code=409)


class DeploymentAnalysisRequiredError(YGITError):
    def __init__(self) -> None:
        super().__init__(code="DEPLOYMENT_ANALYSIS_REQUIRED", message="Deploy-ready repository analysis is required before deployment.", status_code=409)


class DeploymentGithubNotConnectedError(YGITError):
    def __init__(self) -> None:
        super().__init__(code="DEPLOYMENT_GITHUB_NOT_CONNECTED", message="GitHub account must be connected before deployment.", status_code=409)


class DeploymentCloudflareNotConnectedError(YGITError):
    def __init__(self) -> None:
        super().__init__(code="DEPLOYMENT_CLOUDFLARE_NOT_CONNECTED", message="Cloudflare account must be connected before deployment.", status_code=409)


class DeploymentDomainNotReadyError(YGITError):
    def __init__(self) -> None:
        super().__init__(code="DEPLOYMENT_DOMAIN_NOT_READY", message="Project domain is not ready for deployment.", status_code=409)


class DeploymentQueueFailedError(YGITError):
    def __init__(self) -> None:
        super().__init__(code="DEPLOYMENT_QUEUE_FAILED", message="Deployment job could not be queued.", status_code=500)


class DeploymentStatusTransitionInvalidError(YGITError):
    def __init__(self) -> None:
        super().__init__(code="DEPLOYMENT_STATUS_TRANSITION_INVALID", message="Deployment status transition is invalid.", status_code=409)
