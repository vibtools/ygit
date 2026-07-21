from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.release_gate import check_secret_scan

from backend.pipelines.deploy_pipeline.errors import (
    DeployPipelineContextInvalidError,
)
from backend.pipelines.deploy_pipeline.internal.service import (
    DeployPipelineService,
)
from backend.pipelines.deploy_pipeline.public import (
    DeployPipeline,
    DeploymentPipelineContext,
)
from backend.pipelines.deploy_pipeline.schemas import (
    PipelineProviderSummary,
)
from backend.workers.jobs import (
    deploy_project,
    redeploy_project,
)
from backend.workers.jobs.deployment_runtime import (
    execute_deployment_with_context,
    provider_token_reference,
)


class ContextAwarePipeline:
    def __init__(self) -> None:
        self.contexts: list[
            tuple[str, DeploymentPipelineContext]
        ] = []

    def execute_build_stage(
        self,
        input_data,
    ):
        output_path = (
            Path(input_data.repository_path)
            / input_data.root_directory
            / input_data.output_directory
        ).resolve()

        return SimpleNamespace(
            status="succeeded",
            artifact_ready=True,
            output_directory=str(output_path),
        )

    async def execute_deployment(
        self,
        deployment_id: str,
        *,
        context: DeploymentPipelineContext,
    ):
        self.contexts.append(
            ("deploy", context)
        )

        return SimpleNamespace(
            status="completed",
            stage="completed",
            metadata={
                "provider_calls_executed": True,
            },
        )

    async def execute_redeployment(
        self,
        deployment_id: str,
        source_deployment_id: str | None = None,
        *,
        context: DeploymentPipelineContext,
    ):
        self.contexts.append(
            ("redeploy", context)
        )

        assert (
            context.source_deployment_id
            == source_deployment_id
        )

        return SimpleNamespace(
            status="completed",
            stage="completed",
            metadata={
                "provider_calls_executed": True,
            },
        )


class CapturingGateway:
    def __init__(self) -> None:
        self.context = None

    async def deploy_to_cloudflare(
        self,
        context: DeploymentPipelineContext,
    ) -> PipelineProviderSummary:
        self.context = context

        return PipelineProviderSummary(
            provider="cloudflare",
            action="deploy_pages",
            status="pending",
            metadata={
                "reason": "contract_skeleton",
            },
        )


@pytest.mark.asyncio
async def test_deploy_worker_passes_verified_artifact_context(
    tmp_path: Path,
    monkeypatch,
) -> None:
    pipeline = ContextAwarePipeline()
    repository_path = (
        tmp_path / "repository"
    ).resolve()
    repository_path.mkdir()

    monkeypatch.setattr(
        deploy_project,
        "deploy_pipeline",
        pipeline,
    )

    await deploy_project.run(
        {
            "deployment_id": "dep_context",
            "project_id": "proj_context",
            "user_id": "user_context",
            "repository_id": "repo_context",
            "analysis_id": "analysis_context",
            "domain_id": "domain_context",
            "trace_id": "trace_context",
            "framework": "vite",
            "github_token_ref": {
                "provider": "github",
                "token_secret_ref": (
                    "github_app_installation:123"
                ),
                "account_name": "vibtools",
            },
            "cloudflare_token_ref": {
                "provider": "cloudflare",
                "token_secret_ref": (
                    "cloudflare_oauth_account:abc"
                ),
                "account_name": "Vib Tools",
            },
            "repository_url": (
                "https://github.com/vibtools/ygit"
            ),
            "git_ref": "main",
            "commit_sha": "abc123",
            "repository_path": str(
                repository_path
            ),
            "package_manager": "npm",
            "build_command": "npm run build",
            "output_directory": "dist",
            "root_directory": ".",
        }
    )

    assert len(pipeline.contexts) == 1

    action, context = pipeline.contexts[0]

    assert action == "deploy"
    assert context.deployment_id == "dep_context"
    assert context.project_id == "proj_context"
    assert context.user_id == "user_context"
    assert context.repository_id == "repo_context"
    assert context.analysis_id == "analysis_context"
    assert context.domain_id == "domain_context"
    assert context.trace_id == "trace_context"
    assert context.framework == "vite"

    assert context.github_token_ref is not None
    assert (
        context.github_token_ref.provider
        == "github"
    )
    assert (
        context.github_token_ref.token_secret_ref
        == "github_app_installation:123"
    )

    assert context.cloudflare_token_ref is not None
    assert (
        context.cloudflare_token_ref.provider
        == "cloudflare"
    )
    assert (
        context.cloudflare_token_ref.token_secret_ref
        == "cloudflare_oauth_account:abc"
    )

    assert (
        context.repository_url
        == "https://github.com/vibtools/ygit"
    )
    assert context.branch == "main"
    assert context.commit_sha == "abc123"
    assert (
        context.repository_path
        == str(repository_path)
    )
    assert context.artifact_path == str(
        (
            repository_path
            / "dist"
        ).resolve()
    )


@pytest.mark.asyncio
async def test_redeploy_worker_passes_source_and_artifact_context(
    tmp_path: Path,
    monkeypatch,
) -> None:
    pipeline = ContextAwarePipeline()
    repository_path = (
        tmp_path / "redeploy-repository"
    ).resolve()
    repository_path.mkdir()

    monkeypatch.setattr(
        redeploy_project,
        "deploy_pipeline",
        pipeline,
    )

    await redeploy_project.run(
        {
            "deployment_id": "dep_redeploy_context",
            "source_deployment_id": "dep_source",
            "project_id": "proj_context",
            "user_id": "user_context",
            "repository_id": "repo_context",
            "analysis_id": "analysis_context",
            "domain_id": "domain_context",
            "trace_id": "trace_redeploy_context",
            "framework": "vite",
            "github_token_ref": {
                "provider": "github",
                "token_secret_ref": (
                    "github_app_installation:123"
                ),
                "account_name": "vibtools",
            },
            "cloudflare_token_ref": {
                "provider": "cloudflare",
                "token_secret_ref": (
                    "cloudflare_oauth_account:abc"
                ),
                "account_name": "Vib Tools",
            },
            "repository_path": str(
                repository_path
            ),
            "build_command": "npm run build",
            "output_directory": "dist",
        }
    )

    action, context = pipeline.contexts[0]

    assert action == "redeploy"
    assert (
        context.source_deployment_id
        == "dep_source"
    )

    assert context.repository_id == "repo_context"
    assert context.analysis_id == "analysis_context"
    assert context.domain_id == "domain_context"

    assert (
        context.trace_id
        == "trace_redeploy_context"
    )

    assert context.framework == "vite"

    assert context.github_token_ref is not None
    assert (
        context.github_token_ref.provider
        == "github"
    )
    assert (
        context.github_token_ref.token_secret_ref
        == "github_app_installation:123"
    )

    assert context.cloudflare_token_ref is not None
    assert (
        context.cloudflare_token_ref.provider
        == "cloudflare"
    )
    assert (
        context.cloudflare_token_ref.token_secret_ref
        == "cloudflare_oauth_account:abc"
    )

    assert context.artifact_path == str(
        (
            repository_path
            / "dist"
        ).resolve()
    )


def test_provider_reference_rejects_provider_mismatch() -> None:
    with pytest.raises(
        ValueError,
        match="does not match",
    ):
        provider_token_reference(
            {
                "provider": "cloudflare",
                "token_secret_ref": (
                    "cloudflare_oauth_account:abc"
                ),
            },
            expected_provider="github",
        )


def test_provider_reference_rejects_wrong_prefix() -> None:
    with pytest.raises(
        ValueError,
        match="format is not supported",
    ):
        provider_token_reference(
            {
                "provider": "github",
                "token_secret_ref": (
                    "cloudflare_oauth_account:abc"
                ),
            },
            expected_provider="github",
        )


def test_provider_reference_changes_pass_real_secret_scan() -> None:
    result = check_secret_scan()

    assert result.status == "PASS", result.details


@pytest.mark.asyncio
async def test_public_pipeline_forwards_context_to_gateway() -> None:
    gateway = CapturingGateway()
    pipeline = DeployPipeline(
        service=DeployPipelineService(
            provider_gateway=gateway
        )
    )

    context = DeploymentPipelineContext(
        deployment_id="dep_gateway",
        project_id="proj_gateway",
        artifact_path="/tmp/site/dist",
    )

    result = await pipeline.execute_deployment(
        "dep_gateway",
        context=context,
    )

    assert gateway.context is context
    assert result.status == "prepared"
    assert (
        result.metadata[
            "provider_calls_executed"
        ]
        is False
    )


@pytest.mark.asyncio
async def test_pipeline_rejects_mismatched_context() -> None:
    context = DeploymentPipelineContext(
        deployment_id="dep_wrong"
    )

    with pytest.raises(
        DeployPipelineContextInvalidError
    ):
        await DeployPipeline().execute_deployment(
            "dep_expected",
            context=context,
        )


@pytest.mark.asyncio
async def test_legacy_pipeline_fake_remains_supported() -> None:
    class LegacyPipeline:
        async def execute_deployment(
            self,
            deployment_id: str,
        ):
            return {
                "deployment_id": deployment_id
            }

    context = DeploymentPipelineContext(
        deployment_id="dep_legacy"
    )

    result = await execute_deployment_with_context(
        LegacyPipeline(),
        "dep_legacy",
        context=context,
    )

    assert result == {
        "deployment_id": "dep_legacy"
    }
