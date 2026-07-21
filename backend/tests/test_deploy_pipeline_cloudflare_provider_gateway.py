from __future__ import annotations

from pydantic import SecretStr
import pytest

from backend.pipelines.deploy_pipeline.contract import (
    DeployPipelineStage,
)
from backend.pipelines.deploy_pipeline.errors import (
    DeployPipelineCloudflareExecutionError,
    DeployPipelineContextInvalidError,
    DeployPipelineProviderExecutionNotEnabledError,
)
from backend.pipelines.deploy_pipeline.internal.provider_gateway import (
    CloudflarePagesProviderGateway,
)
from backend.pipelines.deploy_pipeline.internal.service import (
    DeployPipelineService,
)
from backend.pipelines.deploy_pipeline.public import (
    build_provider_gateway,
)
from backend.pipelines.deploy_pipeline.schemas import (
    DeploymentPipelineContext,
    PipelineProviderSummary,
    ProviderTokenReference,
)
from backend.providers.cloudflare_provider.artifacts import (
    CloudflarePagesAssetUploadBatch,
    CloudflarePagesAssetUploadItem,
)
from backend.providers.cloudflare_provider.errors import (
    CloudflarePagesProjectError,
)
from backend.providers.cloudflare_provider.schemas import (
    CloudflarePagesArtifactFile,
    CloudflarePagesArtifactManifest,
    CloudflarePagesAssetUploadBatchResult,
    CloudflarePagesAssetUploadPlan,
    CloudflarePagesDeployment,
    CloudflarePagesHashUpsertResult,
    CloudflarePagesProject,
)


HASH_A = "a" * 32
HASH_B = "b" * 32
BEARER_VALUE = "provider-" + "runtime-value"


def ready_context() -> DeploymentPipelineContext:
    reference = ProviderTokenReference(
        provider="cloudflare",
        token_secret_ref=(
            "cloudflare_oauth_account:account-1"
        ),
        account_id="account-1",
        account_name="Primary Account",
    )
    return DeploymentPipelineContext.model_validate(
        {
            "deployment_id": "deployment-1",
            "project_id": "project-1",
            "cloudflare_project_name": (
                "portfolio-site"
            ),
            "user_id": "user-1",
            "artifact_path": (
                "D:/workspace/deployment-1/dist"
            ),
            "branch": "main",
            "commit_sha": "abcdef1234567",
            "cloudflare_token_ref": (
                reference.model_dump()
            ),
            "execution_mode": (
                "provider_enabled"
            ),
        }
    )


def artifact_manifest() -> CloudflarePagesArtifactManifest:
    files = [
        CloudflarePagesArtifactFile(
            relative_path="index.html",
            content_hash=HASH_A,
            size_bytes=12,
        ),
        CloudflarePagesArtifactFile(
            relative_path="assets/app.js",
            content_hash=HASH_B,
            size_bytes=20,
        ),
    ]
    return CloudflarePagesArtifactManifest(
        output_directory_name="dist",
        file_count=2,
        total_bytes=32,
        files=files,
        manifest={
            "index.html": HASH_A,
            "assets/app.js": HASH_B,
        },
    )


class FakeArtifactBuilder:
    def __init__(
        self,
        calls: list[str],
    ) -> None:
        self.calls = calls
        self.manifest = artifact_manifest()

    def build(
        self,
        output_directory: str,
    ) -> CloudflarePagesArtifactManifest:
        assert output_directory.endswith("dist")
        self.calls.append(
            "build_artifact_manifest"
        )
        return self.manifest

    def iter_upload_batches(
        self,
        *,
        output_directory: str,
        manifest: CloudflarePagesArtifactManifest,
        missing_hashes: list[str],
    ):
        assert output_directory.endswith("dist")
        assert manifest is self.manifest
        assert missing_hashes == [HASH_B]
        yield CloudflarePagesAssetUploadBatch(
            items=(
                CloudflarePagesAssetUploadItem(
                    content_hash=HASH_B,
                    content_type=(
                        "application/javascript"
                    ),
                    encoded_value="YXBw",
                    size_bytes=20,
                ),
            ),
            total_bytes=20,
        )


class FakeClient:
    def __init__(
        self,
        calls: list[str],
        *,
        missing_hashes: (
            list[str] | None
        ) = None,
        fail_project: bool = False,
    ) -> None:
        self.calls = calls
        self.missing_hashes = (
            [HASH_B]
            if missing_hashes is None
            else missing_hashes
        )
        self.fail_project = fail_project

    async def ensure_pages_project(
        self,
        **kwargs,
    ) -> CloudflarePagesProject:
        self.calls.append("ensure_project")
        assert kwargs["account_id"] == "account-1"
        assert kwargs["project_name"] == "portfolio-site"
        assert kwargs["production_branch"] == "main"
        assert kwargs["bearer_value"] == BEARER_VALUE

        if self.fail_project:
            raise CloudflarePagesProjectError(
                "provider-detail-that-must-not-leak"
            )

        return CloudflarePagesProject(
            project_id="cf-project-1",
            project_name="portfolio-site",
            production_branch="main",
            subdomain="portfolio-site.pages.dev",
        )

    async def prepare_pages_asset_upload(
        self,
        **kwargs,
    ) -> CloudflarePagesAssetUploadPlan:
        self.calls.append(
            "prepare_asset_upload"
        )
        assert kwargs["content_hashes"] == [
            HASH_A,
            HASH_B,
        ]
        return CloudflarePagesAssetUploadPlan(
            upload_token=SecretStr(
                "upload-" + "runtime-value"
            ),
            requested_hash_count=2,
            missing_hashes=self.missing_hashes,
            cached_hash_count=(
                2 - len(self.missing_hashes)
            ),
        )

    async def upload_pages_asset_batch(
        self,
        **kwargs,
    ) -> CloudflarePagesAssetUploadBatchResult:
        self.calls.append(
            "upload_missing_assets"
        )
        batch = kwargs["batch"]
        return CloudflarePagesAssetUploadBatchResult(
            uploaded_hashes=[
                item.content_hash
                for item in batch.items
            ],
            uploaded_file_count=len(
                batch.items
            ),
            uploaded_bytes=batch.total_bytes,
        )

    async def upsert_pages_asset_hashes(
        self,
        **kwargs,
    ) -> CloudflarePagesHashUpsertResult:
        self.calls.append(
            "upsert_asset_hashes"
        )
        assert kwargs["content_hashes"] == [
            HASH_A,
            HASH_B,
        ]
        return CloudflarePagesHashUpsertResult(
            registered_hashes=[
                HASH_A,
                HASH_B,
            ],
            registered_hash_count=2,
        )

    async def create_pages_deployment(
        self,
        **kwargs,
    ) -> CloudflarePagesDeployment:
        self.calls.append(
            "create_deployment"
        )
        assert kwargs["commit_hash"] == (
            "abcdef1234567"
        )
        return CloudflarePagesDeployment(
            deployment_id="cf-deployment-1",
            project_id="cf-project-1",
            project_name="portfolio-site",
            environment="production",
            url=(
                "https://portfolio-site.pages.dev"
            ),
            aliases=[],
            created_on=(
                "2026-07-21T13:00:00Z"
            ),
            stage_name="deploy",
            stage_status="success",
            branch="main",
            commit_hash="abcdef1234567",
            commit_dirty=False,
        )


@pytest.mark.asyncio
async def test_concrete_gateway_executes_exact_operation_order(
) -> None:
    calls: list[str] = []
    gateway = CloudflarePagesProviderGateway(
        bearer_value=SecretStr(
            BEARER_VALUE
        ),
        client=FakeClient(calls),
        artifact_builder=(
            FakeArtifactBuilder(calls)
        ),
    )

    summary = await gateway.deploy_to_cloudflare(
        ready_context()
    )

    assert calls == [
        "ensure_project",
        "build_artifact_manifest",
        "prepare_asset_upload",
        "upload_missing_assets",
        "upsert_asset_hashes",
        "create_deployment",
    ]
    assert summary.status == "succeeded"
    assert summary.provider_project_id == (
        "cf-project-1"
    )
    assert summary.provider_deployment_id == (
        "cf-deployment-1"
    )
    assert summary.deployment_url == (
        "https://portfolio-site.pages.dev"
    )
    assert summary.metadata[
        "operation_count"
    ] == 6
    assert summary.metadata[
        "uploaded_asset_count"
    ] == 1

    serialized = summary.model_dump_json()
    assert BEARER_VALUE not in serialized
    assert "upload-runtime-value" not in serialized
    assert "token" not in serialized.lower()


@pytest.mark.asyncio
async def test_cached_assets_skip_upload_batches(
) -> None:
    calls: list[str] = []
    gateway = CloudflarePagesProviderGateway(
        bearer_value=SecretStr(
            BEARER_VALUE
        ),
        client=FakeClient(
            calls,
            missing_hashes=[],
        ),
        artifact_builder=(
            FakeArtifactBuilder(calls)
        ),
    )

    summary = await gateway.deploy_to_cloudflare(
        ready_context()
    )

    assert "upload_missing_assets" not in calls
    assert summary.metadata[
        "uploaded_asset_count"
    ] == 0
    assert summary.metadata[
        "cached_asset_count"
    ] == 2


@pytest.mark.asyncio
async def test_blocked_plan_stops_before_provider_calls(
) -> None:
    calls: list[str] = []
    gateway = CloudflarePagesProviderGateway(
        bearer_value=SecretStr(
            BEARER_VALUE
        ),
        client=FakeClient(calls),
        artifact_builder=(
            FakeArtifactBuilder(calls)
        ),
    )
    context = ready_context().model_copy(
        update={
            "execution_mode": (
                "contract_skeleton"
            ),
        }
    )

    with pytest.raises(
        DeployPipelineProviderExecutionNotEnabledError
    ) as raised:
        await gateway.deploy_to_cloudflare(
            context
        )

    assert calls == []
    assert BEARER_VALUE not in str(
        raised.value
    )
    assert context.artifact_path not in str(
        raised.value
    )


@pytest.mark.asyncio
async def test_provider_error_is_sanitized(
) -> None:
    calls: list[str] = []
    gateway = CloudflarePagesProviderGateway(
        bearer_value=SecretStr(
            BEARER_VALUE
        ),
        client=FakeClient(
            calls,
            fail_project=True,
        ),
        artifact_builder=(
            FakeArtifactBuilder(calls)
        ),
    )

    with pytest.raises(
        DeployPipelineCloudflareExecutionError
    ) as raised:
        await gateway.deploy_to_cloudflare(
            ready_context()
        )

    rendered = str(raised.value)
    assert "provider-detail-that-must-not-leak" not in rendered
    assert BEARER_VALUE not in rendered


class SuccessfulGateway:
    async def prepare_source(
        self,
        context,
    ) -> PipelineProviderSummary:
        raise AssertionError(
            "source preparation is not called here"
        )

    async def deploy_to_cloudflare(
        self,
        context,
    ) -> PipelineProviderSummary:
        return PipelineProviderSummary(
            provider="cloudflare",
            action="deploy_pages",
            status="succeeded",
            provider_project_id="cf-project-1",
            provider_deployment_id=(
                "cf-deployment-1"
            ),
            deployment_url=(
                "https://portfolio-site.pages.dev"
            ),
            metadata={
                "operation_count": 6,
            },
        )

    async def verify_deployment(
        self,
        context,
    ) -> PipelineProviderSummary:
        raise AssertionError(
            "typed create response is sufficient"
        )


@pytest.mark.asyncio
async def test_pipeline_service_completes_succeeded_provider_result(
) -> None:
    service = DeployPipelineService(
        provider_gateway=SuccessfulGateway()
    )

    result = await service.execute_deployment(
        "deployment-1",
        context=ready_context(),
    )

    assert result.status == "completed"
    assert result.stage == (
        DeployPipelineStage.COMPLETED
    )
    assert result.deployment_url == (
        "https://portfolio-site.pages.dev"
    )
    assert result.metadata[
        "provider_calls_executed"
    ] is True
    assert [
        event.stage
        for event in result.events
    ] == [
        DeployPipelineStage.PENDING,
        DeployPipelineStage.PREPARING,
        DeployPipelineStage.PROVIDER_DEPLOYING,
        DeployPipelineStage.VERIFYING,
        DeployPipelineStage.COMPLETED,
    ]
    assert result.history_writes[
        -1
    ].provider_summary is not None


def test_public_gateway_factory_requires_secret_wrapped_value(
) -> None:
    gateway = build_provider_gateway(
        bearer_value=SecretStr(
            BEARER_VALUE
        ),
        client=FakeClient([]),
        artifact_builder=(
            FakeArtifactBuilder([])
        ),
    )

    assert hasattr(
        gateway,
        "deploy_to_cloudflare",
    )

    with pytest.raises(
        DeployPipelineContextInvalidError
    ):
        build_provider_gateway(
            bearer_value=BEARER_VALUE,
            client=FakeClient([]),
            artifact_builder=(
                FakeArtifactBuilder([])
            ),
        )
