from __future__ import annotations

from typing import Protocol

from backend.pipelines.deploy_pipeline.errors import DeployPipelineProviderExecutionNotEnabledError
from backend.pipelines.deploy_pipeline.schemas import DeploymentPipelineContext, PipelineProviderSummary


class DeployProviderGateway(Protocol):
    async def prepare_source(self, context: DeploymentPipelineContext) -> PipelineProviderSummary: ...
    async def deploy_to_cloudflare(self, context: DeploymentPipelineContext) -> PipelineProviderSummary: ...
    async def verify_deployment(self, context: DeploymentPipelineContext) -> PipelineProviderSummary: ...


class ContractSkeletonProviderGateway:
    """No-op provider gateway for v0.1.0 contract skeleton.

    This class intentionally does not call GitHub or Cloudflare. Real provider
    execution will be wired during Worker Runtime Integration after the
    Deployment History Engine consumes this contract.
    """

    async def prepare_source(self, context: DeploymentPipelineContext) -> PipelineProviderSummary:
        return PipelineProviderSummary(
            provider="github",
            action="prepare_source",
            status="skipped",
            metadata={
                "reason": "contract_skeleton",
                "deployment_id": context.deployment_id,
            },
        )

    async def deploy_to_cloudflare(self, context: DeploymentPipelineContext) -> PipelineProviderSummary:
        return PipelineProviderSummary(
            provider="cloudflare",
            action="deploy_pages",
            status="pending",
            metadata={
                "reason": "provider_execution_not_enabled_in_v0.1.0",
                "deployment_id": context.deployment_id,
            },
        )

    async def verify_deployment(self, context: DeploymentPipelineContext) -> PipelineProviderSummary:
        raise DeployPipelineProviderExecutionNotEnabledError(
            "Provider verification is intentionally disabled in Deploy Pipeline Skeleton v0.1.0."
        )
