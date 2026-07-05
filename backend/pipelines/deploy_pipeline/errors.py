from __future__ import annotations

from backend.pipelines.deploy_pipeline.contract import DeployPipelineErrorCode


class DeployPipelineError(Exception):
    code: DeployPipelineErrorCode = DeployPipelineErrorCode.CONTEXT_INVALID

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.code.value
        super().__init__(self.message)


class DeployPipelineContextInvalidError(DeployPipelineError):
    code = DeployPipelineErrorCode.CONTEXT_INVALID


class DeployPipelineProviderExecutionNotEnabledError(DeployPipelineError):
    code = DeployPipelineErrorCode.PROVIDER_EXECUTION_NOT_ENABLED
