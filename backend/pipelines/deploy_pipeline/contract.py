from __future__ import annotations

from enum import StrEnum


class DeployPipelineStage(StrEnum):
    """Frozen Deploy Pipeline stage names for v0.1.0.

    These are pipeline stages, not direct database deployment statuses.
    Deployment History Engine stores these stages as timeline metadata while
    mapping them to its own history statuses.
    """

    PENDING = "pending"
    PREPARING = "preparing"
    PROVIDER_DEPLOYING = "provider_deploying"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    FAILED = "failed"


class DeployPipelineEventName(StrEnum):
    """Pipeline events that Deployment History Engine may consume."""

    DEPLOYMENT_STARTED = "deployment.started"
    DEPLOYMENT_PREPARING = "deployment.preparing"
    DEPLOYMENT_PROVIDER_DEPLOYING = "deployment.provider_deploying"
    DEPLOYMENT_VERIFYING = "deployment.verifying"
    DEPLOYMENT_COMPLETED = "deployment.completed"
    DEPLOYMENT_FAILED = "deployment.failed"
    DEPLOYMENT_LOG_APPENDED = "deployment.log_appended"


STAGE_EVENT_MAP: dict[DeployPipelineStage, DeployPipelineEventName] = {
    DeployPipelineStage.PENDING: DeployPipelineEventName.DEPLOYMENT_STARTED,
    DeployPipelineStage.PREPARING: DeployPipelineEventName.DEPLOYMENT_PREPARING,
    DeployPipelineStage.PROVIDER_DEPLOYING: DeployPipelineEventName.DEPLOYMENT_PROVIDER_DEPLOYING,
    DeployPipelineStage.VERIFYING: DeployPipelineEventName.DEPLOYMENT_VERIFYING,
    DeployPipelineStage.COMPLETED: DeployPipelineEventName.DEPLOYMENT_COMPLETED,
    DeployPipelineStage.FAILED: DeployPipelineEventName.DEPLOYMENT_FAILED,
}



class CloudflareProviderOperation(StrEnum):
    """Ordered Cloudflare Pages operations owned by provider orchestration."""

    ENSURE_PROJECT = "ensure_project"
    BUILD_ARTIFACT_MANIFEST = (
        "build_artifact_manifest"
    )
    PREPARE_ASSET_UPLOAD = (
        "prepare_asset_upload"
    )
    UPLOAD_MISSING_ASSETS = (
        "upload_missing_assets"
    )
    UPSERT_ASSET_HASHES = (
        "upsert_asset_hashes"
    )
    CREATE_DEPLOYMENT = "create_deployment"


CLOUDFLARE_PROVIDER_OPERATION_ORDER: tuple[
    CloudflareProviderOperation,
    ...,
] = (
    CloudflareProviderOperation.ENSURE_PROJECT,
    CloudflareProviderOperation.BUILD_ARTIFACT_MANIFEST,
    CloudflareProviderOperation.PREPARE_ASSET_UPLOAD,
    CloudflareProviderOperation.UPLOAD_MISSING_ASSETS,
    CloudflareProviderOperation.UPSERT_ASSET_HASHES,
    CloudflareProviderOperation.CREATE_DEPLOYMENT,
)


class DeployPipelineErrorCode(StrEnum):
    CONTEXT_INVALID = "DEPLOY_PIPELINE_CONTEXT_INVALID"
    GITHUB_FAILED = "DEPLOY_PIPELINE_GITHUB_FAILED"
    CLOUDFLARE_FAILED = "DEPLOY_PIPELINE_CLOUDFLARE_FAILED"
    PROVIDER_TIMEOUT = "DEPLOY_PIPELINE_PROVIDER_TIMEOUT"
    RESULT_INVALID = "DEPLOY_PIPELINE_RESULT_INVALID"
    PROVIDER_EXECUTION_NOT_ENABLED = "DEPLOY_PIPELINE_PROVIDER_EXECUTION_NOT_ENABLED"
