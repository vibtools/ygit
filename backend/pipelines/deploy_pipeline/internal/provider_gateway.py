from __future__ import annotations

from typing import Protocol

from backend.pipelines.deploy_pipeline.contract import (
    CLOUDFLARE_PROVIDER_OPERATION_ORDER,
)
from backend.pipelines.deploy_pipeline.errors import (
    DeployPipelineContextInvalidError,
    DeployPipelineProviderExecutionNotEnabledError,
)
from backend.pipelines.deploy_pipeline.schemas import (
    CloudflareProviderExecutionPlan,
    CloudflareProviderPlanBlocker,
    DeploymentPipelineContext,
    PipelineProviderSummary,
)



def _required_context_value(
    value: str | None,
    *,
    label: str,
) -> str | None:
    normalized = str(value or "").strip()

    if not normalized:
        return None

    if any(
        character in normalized
        for character in (
            "\x00",
            "\r",
            "\n",
        )
    ):
        raise DeployPipelineContextInvalidError(
            f"Deploy Pipeline {label} is invalid."
        )

    return normalized


def build_cloudflare_provider_execution_plan(
    context: DeploymentPipelineContext,
) -> CloudflareProviderExecutionPlan:
    deployment_id = _required_context_value(
        context.deployment_id,
        label="deployment ID",
    )

    if deployment_id is None:
        raise DeployPipelineContextInvalidError(
            "Deploy Pipeline deployment ID is missing."
        )

    blockers: list[
        CloudflareProviderPlanBlocker
    ] = []

    if (
        _required_context_value(
            context.user_id,
            label="user ID",
        )
        is None
    ):
        blockers.append(
            "user_context_missing"
        )

    if (
        _required_context_value(
            context.project_id,
            label="project ID",
        )
        is None
    ):
        blockers.append(
            "project_context_missing"
        )

    if (
        _required_context_value(
            context.artifact_path,
            label="artifact path",
        )
        is None
    ):
        blockers.append(
            "artifact_context_missing"
        )

    if (
        _required_context_value(
            context.branch,
            label="branch",
        )
        is None
    ):
        blockers.append(
            "branch_context_missing"
        )

    reference = context.cloudflare_token_ref

    if reference is None:
        blockers.append(
            "cloudflare_reference_missing"
        )
    elif reference.provider != "cloudflare":
        raise DeployPipelineContextInvalidError(
            "Deploy Pipeline Cloudflare reference "
            "provider is invalid."
        )
    elif (
        _required_context_value(
            reference.token_secret_ref,
            label="Cloudflare reference",
        )
        is None
    ):
        blockers.append(
            "cloudflare_reference_missing"
        )

    if context.execution_mode != "provider_enabled":
        blockers.append(
            "provider_execution_disabled"
        )

    plan_fields = {
        "deployment_id": deployment_id,
        "execution_mode": context.execution_mode,
        "operations": list(
            CLOUDFLARE_PROVIDER_OPERATION_ORDER
        ),
        "ready_to_execute": not blockers,
        "blockers": blockers,
    }
    return CloudflareProviderExecutionPlan(
        **plan_fields
    )


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
