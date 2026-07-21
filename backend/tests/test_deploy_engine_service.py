from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from backend.engines.auth_engine.connected_accounts_module.errors import ProviderNotConnectedError
from backend.engines.deploy_engine.errors import (
    DeploymentAnalysisRequiredError,
    DeploymentCloudflareNotConnectedError,
    DeploymentProjectNotReadyError,
)
from backend.engines.deploy_engine.internal.service import DeployInternalService
from backend.engines.deploy_engine.schemas import DeploymentRecord, DeploymentRequestInput
from backend.engines.project_engine.schemas import ProjectDetail
from backend.engines.repository_analysis_engine.schemas import AnalysisDetail
from backend.engines.repository_engine.schemas import RepositoryDetail
from backend.workers.queue.schemas import JobRef

NOW = datetime.now(timezone.utc)


def project_detail(*, repository_id: str | None = "repo_1", analysis_id: str | None = "analysis_1") -> ProjectDetail:
    return ProjectDetail(
        id="proj_1",
        user_id="user_1",
        name="Demo",
        slug="demo",
        status="deploy_ready",
        repository_id=repository_id,
        analysis_id=analysis_id,
        current_deployment_id=None,
        created_at=NOW,
        updated_at=NOW,
        deleted_at=None,
        version=1,
    )


def analysis_detail(
    *,
    deploy_ready: bool = True,
    package_manager: str | None = "npm",
    build_command: str | None = "npm run build",
    output_directory: str | None = "dist",
) -> AnalysisDetail:
    return AnalysisDetail(
        id="analysis_1",
        repository_id="repo_1",
        user_id="user_1",
        project_id="proj_1",
        stage="quick",
        status="quick_completed",
        framework="vite",
        package_manager=package_manager,
        build_command=build_command,
        output_directory=output_directory,
        deploy_ready=deploy_ready,
        score=95,
        explanation={},
        warnings=[],
        errors=[],
        commit_sha="abc123",
        is_latest=True,
        created_at=NOW,
        updated_at=NOW,
        deleted_at=None,
    )


def repository_detail(
    *,
    repository_url: str = "https://github.com/vibtools/ygit",
    default_branch: str | None = "main",
) -> RepositoryDetail:
    return RepositoryDetail(
        id="repo_1",
        user_id="user_1",
        provider="github",
        repository_url=repository_url,
        owner="vibtools",
        name="ygit",
        default_branch=default_branch,
        visibility="public",
        latest_commit_sha="abc123",
        fetched_at=NOW,
        created_at=NOW,
        updated_at=NOW,
        file_tree_snapshot=None,
        metadata=None,
        deleted_at=None,
    )


class FakeRepositoryMetadataService:
    def __init__(self, repository: RepositoryDetail) -> None:
        self.repository = repository

    async def get_repository_metadata(
        self,
        db,
        *,
        user_id: str,
        repository_id: str,
    ) -> RepositoryDetail:
        assert user_id == self.repository.user_id
        assert repository_id == self.repository.id
        return self.repository


class FakeProjectService:
    def __init__(self, project: ProjectDetail) -> None:
        self.project = project

    async def get_project(self, db, *, user_id: str, project_id: str) -> ProjectDetail:
        return self.project


class FakeAnalysisService:
    def __init__(self, analysis: AnalysisDetail) -> None:
        self.analysis = analysis

    async def get_analysis_result(self, db, *, user_id: str, analysis_id: str) -> AnalysisDetail:
        return self.analysis


class FakeConnectedAccounts:
    def __init__(self, missing: set[str] | None = None) -> None:
        self.missing = missing or set()

    async def require_provider_connected(self, db, *, user_id: str, provider: str):
        if provider in self.missing:
            raise ProviderNotConnectedError()
        return SimpleNamespace(provider=provider, status="connected", token_secret_ref=f"{provider}:ref")


class FakeQueue:
    def __init__(self) -> None:
        self.payloads = []

    async def enqueue(self, payload, db=None) -> JobRef:
        _ = db
        assert payload.job_type == "deploy_project"
        assert payload.payload["deployment_id"] == "dep_1"
        self.payloads.append(payload)
        return JobRef(id="job_1", type=payload.job_type, status="queued")


class FakeRepository:
    async def create_queued_deployment(self, db, **kwargs) -> DeploymentRecord:
        return DeploymentRecord(
            id="dep_1",
            project_id=kwargs["project_id"],
            user_id=kwargs["user_id"],
            repository_id=kwargs["repository_id"],
            analysis_id=kwargs["analysis_id"],
            domain_id=kwargs.get("domain_id"),
            job_id=None,
            status="queued",
            requested_by=kwargs.get("requested_by", "user"),
            source_deployment_id=kwargs.get("source_deployment_id"),
            queued_at=NOW,
            started_at=None,
            completed_at=None,
            cancelled_at=None,
            failure_code=None,
            failure_summary=None,
            created_at=NOW,
            updated_at=NOW,
            version=1,
        )

    async def attach_job_id(self, db, *, deployment_id: str, job_id: str) -> DeploymentRecord:
        assert deployment_id == "dep_1"
        assert job_id == "job_1"
        return DeploymentRecord(
            id="dep_1",
            project_id="proj_1",
            user_id="user_1",
            repository_id="repo_1",
            analysis_id="analysis_1",
            job_id=job_id,
            status="queued",
            requested_by="user",
            queued_at=NOW,
            created_at=NOW,
            updated_at=NOW,
            version=2,
        )


class FakeDB:
    async def commit(self) -> None:
        self.committed = True


@pytest.mark.asyncio
async def test_request_deployment_queues_job_without_provider_logic() -> None:
    queue = FakeQueue()
    service = DeployInternalService(
        repository=FakeRepository(),
        project_public_service=FakeProjectService(project_detail()),
        analysis_public_service=FakeAnalysisService(analysis_detail()),
        repository_public_service=FakeRepositoryMetadataService(repository_detail()),
        connected_accounts_public_service=FakeConnectedAccounts(),
        queue_client=queue,
    )
    result = await service.request_deployment(
        FakeDB(),
        user_id="user_1",
        project_id="proj_1",
        input_data=DeploymentRequestInput(),
        trace_id="trace_test",
    )
    assert result.deployment.id == "dep_1"
    assert result.deployment.status == "queued"
    assert result.job.id == "job_1"
    assert result.job.type == "deploy_project"

    payload = queue.payloads[0].payload
    assert payload["deployment_id"] == "dep_1"
    assert payload["project_id"] == "proj_1"
    assert payload["user_id"] == "user_1"
    assert payload["repository_url"] == "https://github.com/vibtools/ygit"
    assert payload["git_ref"] == "main"
    assert payload["package_manager"] == "npm"
    assert payload["build_command"] == "npm run build"
    assert payload["output_directory"] == "dist"
    assert payload["root_directory"] == "."
    assert "repository_path" not in payload


@pytest.mark.asyncio
async def test_request_deployment_omits_missing_build_settings_without_crashing() -> None:
    queue = FakeQueue()
    service = DeployInternalService(
        repository=FakeRepository(),
        project_public_service=FakeProjectService(project_detail()),
        analysis_public_service=FakeAnalysisService(
            analysis_detail(build_command=None, output_directory=None)
        ),
        repository_public_service=FakeRepositoryMetadataService(repository_detail()),
        connected_accounts_public_service=FakeConnectedAccounts(),
        queue_client=queue,
    )

    result = await service.request_deployment(
        FakeDB(),
        user_id="user_1",
        project_id="proj_1",
        input_data=DeploymentRequestInput(),
        trace_id="trace_test",
    )

    assert result.job.type == "deploy_project"
    payload = queue.payloads[0].payload
    assert payload["deployment_id"] == "dep_1"
    assert payload["project_id"] == "proj_1"
    assert payload["user_id"] == "user_1"
    assert payload["repository_url"] == "https://github.com/vibtools/ygit"
    assert payload["git_ref"] == "main"
    assert payload["package_manager"] == "npm"
    assert "build_command" not in payload
    assert "output_directory" not in payload
    assert "root_directory" not in payload
    assert "repository_path" not in payload


def test_deploy_engine_queue_build_settings_keeps_architecture_boundaries() -> None:
    source = Path("backend/engines/deploy_engine/internal/service.py").read_text(encoding="utf-8")

    assert "_build_configuration_from_analysis" in source
    assert "_repository_checkout_configuration" in source
    assert "build_configuration" in source
    assert "repository_configuration" in source
    assert "backend.engines.repository_engine.public" in source
    assert "backend.engines.repository_engine.internal" not in source
    assert '"repository_path"' not in source
    assert "\'repository_path\'" not in source
    assert "backend.providers" not in source
    assert "github_provider" not in source
    assert "cloudflare_provider" not in source


@pytest.mark.asyncio
async def test_request_deployment_requires_repository() -> None:
    service = DeployInternalService(
        repository=FakeRepository(),
        project_public_service=FakeProjectService(project_detail(repository_id=None)),
        analysis_public_service=FakeAnalysisService(analysis_detail()),
        repository_public_service=FakeRepositoryMetadataService(repository_detail()),
        connected_accounts_public_service=FakeConnectedAccounts(),
        queue_client=FakeQueue(),
    )
    with pytest.raises(DeploymentProjectNotReadyError):
        await service.request_deployment(FakeDB(), user_id="user_1", project_id="proj_1")


@pytest.mark.asyncio
async def test_request_deployment_requires_analysis() -> None:
    service = DeployInternalService(
        repository=FakeRepository(),
        project_public_service=FakeProjectService(project_detail(analysis_id=None)),
        analysis_public_service=FakeAnalysisService(analysis_detail()),
        repository_public_service=FakeRepositoryMetadataService(repository_detail()),
        connected_accounts_public_service=FakeConnectedAccounts(),
        queue_client=FakeQueue(),
    )
    with pytest.raises(DeploymentAnalysisRequiredError):
        await service.request_deployment(FakeDB(), user_id="user_1", project_id="proj_1")


@pytest.mark.asyncio
async def test_request_deployment_requires_deploy_ready_analysis() -> None:
    service = DeployInternalService(
        repository=FakeRepository(),
        project_public_service=FakeProjectService(project_detail()),
        analysis_public_service=FakeAnalysisService(analysis_detail(deploy_ready=False)),
        repository_public_service=FakeRepositoryMetadataService(repository_detail()),
        connected_accounts_public_service=FakeConnectedAccounts(),
        queue_client=FakeQueue(),
    )
    with pytest.raises(DeploymentProjectNotReadyError):
        await service.request_deployment(FakeDB(), user_id="user_1", project_id="proj_1")


@pytest.mark.asyncio
async def test_request_deployment_requires_cloudflare_connection() -> None:
    service = DeployInternalService(
        repository=FakeRepository(),
        project_public_service=FakeProjectService(project_detail()),
        analysis_public_service=FakeAnalysisService(analysis_detail()),
        repository_public_service=FakeRepositoryMetadataService(repository_detail()),
        connected_accounts_public_service=FakeConnectedAccounts(missing={"cloudflare"}),
        queue_client=FakeQueue(),
    )
    with pytest.raises(DeploymentCloudflareNotConnectedError):
        await service.request_deployment(FakeDB(), user_id="user_1", project_id="proj_1")
