from __future__ import annotations

from typing import Protocol

from pydantic import SecretStr

from backend.providers.cloudflare_provider.artifacts import (
    CloudflarePagesArtifactBuilder,
)
from backend.providers.cloudflare_provider.client import (
    CloudflareProviderClient,
)
from backend.providers.cloudflare_provider.errors import (
    CloudflareProviderError,
)
from backend.providers.cloudflare_provider.schemas import (
    CloudflarePagesUploadToken,
)
from backend.pipelines.deploy_pipeline.contract import (
    CLOUDFLARE_PROVIDER_OPERATION_ORDER,
)
from backend.pipelines.deploy_pipeline.errors import (
    DeployPipelineCloudflareExecutionError,
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

    if (
        context.execution_mode == "provider_enabled"
        and _required_context_value(
            context.cloudflare_project_name,
            label="Cloudflare project name",
        )
        is None
    ):
        blockers.append(
            "cloudflare_project_name_missing"
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
    elif (
        context.execution_mode == "provider_enabled"
        and _required_context_value(
            reference.account_id,
            label="Cloudflare account ID",
        )
        is None
    ):
        blockers.append(
            "cloudflare_account_context_missing"
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


class CloudflarePagesProviderGateway:
    """Concrete Cloudflare Pages orchestration behind explicit runtime wiring."""

    def __init__(
        self,
        *,
        bearer_value: SecretStr,
        client: CloudflareProviderClient | None = None,
        artifact_builder: (
            CloudflarePagesArtifactBuilder | None
        ) = None,
    ) -> None:
        if not isinstance(bearer_value, SecretStr):
            raise DeployPipelineContextInvalidError(
                "Cloudflare runtime credential must remain secret-wrapped."
            )

        normalized = bearer_value.get_secret_value().strip()

        if (
            not normalized
            or any(
                character in normalized
                for character in (
                    "\x00",
                    "\r",
                    "\n",
                )
            )
        ):
            raise DeployPipelineContextInvalidError(
                "Cloudflare runtime credential is invalid."
            )

        self._bearer_value = bearer_value
        self.client = client or CloudflareProviderClient()
        self.artifact_builder = (
            artifact_builder
            or CloudflarePagesArtifactBuilder()
        )

    @staticmethod
    def _ready_value(
        value: str | None,
        *,
        label: str,
    ) -> str:
        normalized = _required_context_value(
            value,
            label=label,
        )

        if normalized is None:
            raise DeployPipelineContextInvalidError(
                f"Deploy Pipeline {label} is missing."
            )

        return normalized

    async def prepare_source(
        self,
        context: DeploymentPipelineContext,
    ) -> PipelineProviderSummary:
        return PipelineProviderSummary(
            provider="github",
            action="prepare_source",
            status="skipped",
            metadata={
                "reason": "source_prepared_by_worker",
                "deployment_id": context.deployment_id,
            },
        )

    async def deploy_to_cloudflare(
        self,
        context: DeploymentPipelineContext,
    ) -> PipelineProviderSummary:
        plan = build_cloudflare_provider_execution_plan(
            context
        )

        if not plan.ready_to_execute:
            blocker_list = ", ".join(
                str(blocker)
                for blocker in plan.blockers
            )
            raise (
                DeployPipelineProviderExecutionNotEnabledError(
                    "Cloudflare provider execution is blocked"
                    + (
                        f": {blocker_list}"
                        if blocker_list
                        else "."
                    )
                )
            )

        reference = context.cloudflare_token_ref

        if reference is None:
            raise DeployPipelineContextInvalidError(
                "Deploy Pipeline Cloudflare reference is missing."
            )

        account_id = self._ready_value(
            reference.account_id,
            label="Cloudflare account ID",
        )
        project_name = self._ready_value(
            context.cloudflare_project_name,
            label="Cloudflare project name",
        )
        branch = self._ready_value(
            context.branch,
            label="branch",
        )
        artifact_path = self._ready_value(
            context.artifact_path,
            label="artifact path",
        )
        bearer_value = (
            self._bearer_value
            .get_secret_value()
        )

        try:
            project = (
                await self.client.ensure_pages_project(
                    account_id=account_id,
                    project_name=project_name,
                    production_branch=branch,
                    bearer_value=bearer_value,
                )
            )
            manifest = self.artifact_builder.build(
                artifact_path
            )
            content_hashes = sorted(
                set(manifest.manifest.values())
            )
            upload_plan = (
                await self.client
                .prepare_pages_asset_upload(
                    account_id=account_id,
                    project_name=project_name,
                    bearer_value=bearer_value,
                    content_hashes=content_hashes,
                )
            )
            upload_session = CloudflarePagesUploadToken(
                upload_token=upload_plan.upload_token
            )
            uploaded_hashes: list[str] = []
            uploaded_bytes = 0

            if upload_plan.missing_hashes:
                for batch in (
                    self.artifact_builder
                    .iter_upload_batches(
                        output_directory=artifact_path,
                        manifest=manifest,
                        missing_hashes=(
                            upload_plan.missing_hashes
                        ),
                    )
                ):
                    batch_result = (
                        await self.client
                        .upload_pages_asset_batch(
                            upload_session=upload_session,
                            batch=batch,
                        )
                    )
                    uploaded_hashes.extend(
                        batch_result.uploaded_hashes
                    )
                    uploaded_bytes += (
                        batch_result.uploaded_bytes
                    )

            if sorted(uploaded_hashes) != sorted(
                upload_plan.missing_hashes
            ):
                raise DeployPipelineCloudflareExecutionError(
                    "Cloudflare Pages asset upload result is inconsistent."
                )

            hash_result = (
                await self.client
                .upsert_pages_asset_hashes(
                    upload_session=upload_session,
                    content_hashes=content_hashes,
                )
            )

            if sorted(
                hash_result.registered_hashes
            ) != content_hashes:
                raise DeployPipelineCloudflareExecutionError(
                    "Cloudflare Pages hash registration result is inconsistent."
                )

            deployment = (
                await self.client
                .create_pages_deployment(
                    account_id=account_id,
                    project_name=project_name,
                    bearer_value=bearer_value,
                    branch=branch,
                    manifest=manifest,
                    commit_hash=context.commit_sha,
                    commit_dirty=False,
                )
            )
        except DeployPipelineCloudflareExecutionError:
            raise
        except CloudflareProviderError as exc:
            raise DeployPipelineCloudflareExecutionError(
                "Cloudflare Pages provider execution failed."
            ) from exc

        if (
            deployment.project_id
            != project.project_id
            or deployment.project_name
            != project.project_name
        ):
            raise DeployPipelineCloudflareExecutionError(
                "Cloudflare Pages deployment project result is inconsistent."
            )

        return PipelineProviderSummary(
            provider="cloudflare",
            action="deploy_pages",
            status="succeeded",
            provider_project_id=project.project_id,
            provider_deployment_id=(
                deployment.deployment_id
            ),
            deployment_url=deployment.url,
            metadata={
                "operation_count": len(
                    plan.operations
                ),
                "artifact_file_count": (
                    manifest.file_count
                ),
                "artifact_bytes": (
                    manifest.total_bytes
                ),
                "cached_asset_count": (
                    upload_plan.cached_hash_count
                ),
                "missing_asset_count": len(
                    upload_plan.missing_hashes
                ),
                "uploaded_asset_count": len(
                    uploaded_hashes
                ),
                "uploaded_bytes": uploaded_bytes,
                "registered_asset_count": (
                    hash_result
                    .registered_hash_count
                ),
                "environment": (
                    deployment.environment
                ),
                "stage_name": (
                    deployment.stage_name
                ),
                "stage_status": (
                    deployment.stage_status
                ),
            },
        )

    async def verify_deployment(
        self,
        context: DeploymentPipelineContext,
    ) -> PipelineProviderSummary:
        return PipelineProviderSummary(
            provider="cloudflare",
            action="verify_deployment",
            status="skipped",
            metadata={
                "reason": (
                    "typed_create_response_validated"
                ),
                "deployment_id": (
                    context.deployment_id
                ),
            },
        )


def build_cloudflare_pages_provider_gateway(
    *,
    bearer_value: SecretStr,
    client: CloudflareProviderClient | None = None,
    artifact_builder: (
        CloudflarePagesArtifactBuilder | None
    ) = None,
) -> CloudflarePagesProviderGateway:
    return CloudflarePagesProviderGateway(
        bearer_value=bearer_value,
        client=client,
        artifact_builder=artifact_builder,
    )


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
