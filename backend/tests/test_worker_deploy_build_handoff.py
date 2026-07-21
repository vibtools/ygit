from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from backend.workers.errors import (
    WorkerBuildStageFailedError,
    WorkerDeploymentIncompleteError,
)
from backend.workers.git_checkout import WorkerGitCheckoutError
from backend.workers.jobs import deploy_project, redeploy_project


class FakeDeployPipeline:
    def __init__(
        self,
        *,
        build_status: str = "succeeded",
        deployment_status: str = "completed",
        provider_calls_executed: bool | None = True,
    ) -> None:
        self.build_status = build_status
        self.deployment_status = deployment_status
        self.provider_calls_executed = (
            provider_calls_executed
        )
        self.calls: list[tuple] = []

    def execute_build_stage(self, input_data):
        self.calls.append(("build", input_data))
        return SimpleNamespace(
            status=self.build_status
        )

    def _deployment_result(self):
        stage = (
            "completed"
            if self.deployment_status == "completed"
            else "provider_deploying"
        )

        metadata = {}

        if self.provider_calls_executed is not None:
            metadata["provider_calls_executed"] = (
                self.provider_calls_executed
            )

        return SimpleNamespace(
            status=self.deployment_status,
            stage=stage,
            metadata=metadata,
        )

    async def execute_deployment(
        self,
        deployment_id: str,
    ):
        self.calls.append(
            ("deploy", deployment_id)
        )
        return self._deployment_result()

    async def execute_redeployment(
        self,
        deployment_id: str,
        source_deployment_id: str | None = None,
    ):
        self.calls.append(
            (
                "redeploy",
                deployment_id,
                source_deployment_id,
            )
        )

        return self._deployment_result()


@pytest.mark.asyncio
async def test_deploy_worker_preserves_existing_behavior_without_build_payload(monkeypatch) -> None:
    fake_pipeline = FakeDeployPipeline()
    monkeypatch.setattr(deploy_project, "deploy_pipeline", fake_pipeline)

    await deploy_project.run({"deployment_id": "dep_1", "project_id": "proj_1", "user_id": "user_1"})

    assert fake_pipeline.calls == [("deploy", "dep_1")]


@pytest.mark.asyncio
async def test_deploy_worker_runs_build_stage_before_deployment_when_payload_is_complete(monkeypatch) -> None:
    fake_pipeline = FakeDeployPipeline(build_status="succeeded")
    monkeypatch.setattr(deploy_project, "deploy_pipeline", fake_pipeline)

    await deploy_project.run(
        {
            "deployment_id": "dep_2",
            "project_id": "proj_1",
            "user_id": "user_1",
            "repository_path": "C:/ygit/work/dep_2/repository",
            "package_manager": "npm",
            "build_command": "npm run build",
            "output_directory": "dist",
            "root_directory": ".",
            "timeout_seconds": "900",
            "environment": {"NODE_ENV": "production"},
        }
    )

    assert [call[0] for call in fake_pipeline.calls] == ["build", "deploy"]
    build_input = fake_pipeline.calls[0][1]
    assert build_input.deployment_id == "dep_2"
    assert build_input.repository_path == "C:/ygit/work/dep_2/repository"
    assert build_input.package_manager == "npm"
    assert build_input.build_command == "npm run build"
    assert build_input.output_directory == "dist"
    assert build_input.timeout_seconds == 900
    assert build_input.environment == {"NODE_ENV": "production"}
    assert fake_pipeline.calls[1] == ("deploy", "dep_2")


@pytest.mark.asyncio
async def test_deploy_worker_prepares_workspace_but_skips_build_until_checkout_exists(
    tmp_path: Path,
    monkeypatch,
) -> None:
    fake_pipeline = FakeDeployPipeline(build_status="succeeded")
    monkeypatch.setattr(deploy_project, "deploy_pipeline", fake_pipeline)
    monkeypatch.setenv("YGIT_WORKSPACE_ROOT", str(tmp_path))

    await deploy_project.run(
        {
            "deployment_id": "dep_workspace",
            "project_id": "proj_1",
            "user_id": "user_1",
            "package_manager": "npm",
            "build_command": "npm run build",
            "output_directory": "dist",
        }
    )

    assert (tmp_path / "dep_workspace" / "repository").is_dir()
    assert (tmp_path / "dep_workspace" / "artifacts").is_dir()
    assert fake_pipeline.calls == [("deploy", "dep_workspace")]


@pytest.mark.asyncio
async def test_deploy_worker_runs_checkout_then_build_when_repository_url_exists(
    tmp_path: Path,
    monkeypatch,
) -> None:
    fake_pipeline = FakeDeployPipeline(build_status="succeeded")
    checkout_calls = []

    def fake_checkout(request):
        checkout_calls.append(request)
        request.destination_path.mkdir(parents=True, exist_ok=True)
        (request.destination_path / "package.json").write_text("{}", encoding="utf-8")
        return SimpleNamespace(commit_sha="abc123")

    monkeypatch.setattr(deploy_project, "deploy_pipeline", fake_pipeline)
    monkeypatch.setattr(deploy_project, "run_git_checkout", fake_checkout)
    monkeypatch.setenv("YGIT_WORKSPACE_ROOT", str(tmp_path))

    await deploy_project.run(
        {
            "deployment_id": "dep_checkout_url",
            "project_id": "proj_1",
            "user_id": "user_1",
            "repository_url": "https://github.com/vibtools/ygit",
            "git_ref": "main",
            "checkout_timeout_seconds": "45",
            "package_manager": "npm",
            "build_command": "npm run build",
            "output_directory": "dist",
        }
    )

    assert len(checkout_calls) == 1
    assert checkout_calls[0].repository_url == "https://github.com/vibtools/ygit"
    assert checkout_calls[0].destination_path == (tmp_path / "dep_checkout_url" / "repository").resolve()
    assert checkout_calls[0].ref == "main"
    assert checkout_calls[0].timeout_seconds == 45

    assert [call[0] for call in fake_pipeline.calls] == ["build", "deploy"]
    build_input = fake_pipeline.calls[0][1]
    assert Path(build_input.repository_path) == (tmp_path / "dep_checkout_url" / "repository").resolve()
    assert build_input.build_command == "npm run build"
    assert build_input.output_directory == "dist"


@pytest.mark.asyncio
async def test_deploy_worker_stops_when_checkout_fails(
    tmp_path: Path,
    monkeypatch,
) -> None:
    fake_pipeline = FakeDeployPipeline(build_status="succeeded")

    def fake_checkout(_request):
        raise WorkerGitCheckoutError("checkout failed")

    monkeypatch.setattr(deploy_project, "deploy_pipeline", fake_pipeline)
    monkeypatch.setattr(deploy_project, "run_git_checkout", fake_checkout)
    monkeypatch.setenv("YGIT_WORKSPACE_ROOT", str(tmp_path))

    with pytest.raises(WorkerGitCheckoutError):
        await deploy_project.run(
            {
                "deployment_id": "dep_checkout_fail",
                "repository_url": "https://github.com/vibtools/ygit",
                "build_command": "npm run build",
                "output_directory": "dist",
            }
        )

    assert fake_pipeline.calls == []


@pytest.mark.asyncio
async def test_deploy_worker_uses_workspace_repository_path_after_checkout_content_exists(
    tmp_path: Path,
    monkeypatch,
) -> None:
    fake_pipeline = FakeDeployPipeline(build_status="succeeded")
    monkeypatch.setattr(deploy_project, "deploy_pipeline", fake_pipeline)
    monkeypatch.setenv("YGIT_WORKSPACE_ROOT", str(tmp_path))

    checkout_path = tmp_path / "dep_checkout" / "repository"
    checkout_path.mkdir(parents=True)
    (checkout_path / "package.json").write_text("{}", encoding="utf-8")

    await deploy_project.run(
        {
            "deployment_id": "dep_checkout",
            "project_id": "proj_1",
            "user_id": "user_1",
            "package_manager": "npm",
            "build_command": "npm run build",
            "output_directory": "dist",
        }
    )

    assert [call[0] for call in fake_pipeline.calls] == ["build", "deploy"]
    build_input = fake_pipeline.calls[0][1]
    assert Path(build_input.repository_path) == checkout_path.resolve()
    assert build_input.build_command == "npm run build"
    assert build_input.output_directory == "dist"


@pytest.mark.asyncio
async def test_deploy_worker_raises_when_build_stage_fails(
    monkeypatch,
) -> None:
    fake_pipeline = FakeDeployPipeline(
        build_status="failed"
    )

    monkeypatch.setattr(
        deploy_project,
        "deploy_pipeline",
        fake_pipeline,
    )

    with pytest.raises(
        WorkerBuildStageFailedError
    ) as error_info:
        await deploy_project.run(
            {
                "deployment_id": "dep_3",
                "repository_path": (
                    "C:/ygit/work/dep_3/repository"
                ),
                "build_command": "npm run build",
                "output_directory": "dist",
            }
        )

    assert (
        error_info.value.code
        == "DEPLOY_BUILD_STAGE_FAILED"
    )

    assert [
        call[0] for call in fake_pipeline.calls
    ] == ["build"]


@pytest.mark.asyncio
async def test_deploy_worker_rejects_prepared_pipeline_result(
    monkeypatch,
) -> None:
    fake_pipeline = FakeDeployPipeline(
        deployment_status="prepared",
        provider_calls_executed=False,
    )

    monkeypatch.setattr(
        deploy_project,
        "deploy_pipeline",
        fake_pipeline,
    )

    with pytest.raises(
        WorkerDeploymentIncompleteError
    ) as error_info:
        await deploy_project.run(
            {
                "deployment_id": "dep_prepared",
            }
        )

    assert (
        error_info.value.code
        == "DEPLOY_PIPELINE_INCOMPLETE"
    )

    assert fake_pipeline.calls == [
        ("deploy", "dep_prepared")
    ]


@pytest.mark.asyncio
async def test_deploy_worker_rejects_false_provider_completion(
    monkeypatch,
) -> None:
    fake_pipeline = FakeDeployPipeline(
        deployment_status="completed",
        provider_calls_executed=False,
    )

    monkeypatch.setattr(
        deploy_project,
        "deploy_pipeline",
        fake_pipeline,
    )

    with pytest.raises(
        WorkerDeploymentIncompleteError
    ):
        await deploy_project.run(
            {
                "deployment_id": "dep_false_complete",
            }
        )


@pytest.mark.asyncio
async def test_deploy_worker_rejects_missing_provider_proof(
    monkeypatch,
) -> None:
    fake_pipeline = FakeDeployPipeline(
        deployment_status="completed",
        provider_calls_executed=None,
    )

    monkeypatch.setattr(
        deploy_project,
        "deploy_pipeline",
        fake_pipeline,
    )

    with pytest.raises(
        WorkerDeploymentIncompleteError
    ) as error_info:
        await deploy_project.run(
            {
                "deployment_id": "dep_missing_proof",
            }
        )

    assert (
        error_info.value.metadata[
            "provider_calls_executed"
        ]
        is None
    )


@pytest.mark.asyncio
async def test_redeploy_worker_runs_checkout_and_build_before_redeployment(
    tmp_path: Path,
    monkeypatch,
) -> None:
    fake_pipeline = FakeDeployPipeline(
        build_status="succeeded"
    )
    checkout_calls = []

    def fake_checkout(request):
        checkout_calls.append(request)
        request.destination_path.mkdir(
            parents=True,
            exist_ok=True,
        )
        (
            request.destination_path
            / "package.json"
        ).write_text(
            "{}",
            encoding="utf-8",
        )

        return SimpleNamespace(
            commit_sha="redeploy123"
        )

    monkeypatch.setattr(
        redeploy_project,
        "deploy_pipeline",
        fake_pipeline,
    )
    monkeypatch.setattr(
        redeploy_project,
        "run_git_checkout",
        fake_checkout,
    )
    monkeypatch.setenv(
        "YGIT_WORKSPACE_ROOT",
        str(tmp_path),
    )

    await redeploy_project.run(
        {
            "deployment_id": "dep_redeploy_build",
            "source_deployment_id": "dep_source",
            "repository_url": (
                "https://github.com/vibtools/ygit"
            ),
            "git_ref": "main",
            "checkout_timeout_seconds": "45",
            "package_manager": "npm",
            "build_command": "npm run build",
            "output_directory": "dist",
            "root_directory": ".",
            "timeout_seconds": "900",
            "environment": {
                "NODE_ENV": "production",
            },
        }
    )

    assert len(checkout_calls) == 1
    assert (
        checkout_calls[0].repository_url
        == "https://github.com/vibtools/ygit"
    )
    assert checkout_calls[0].ref == "main"
    assert (
        checkout_calls[0].timeout_seconds
        == 45
    )

    assert [
        call[0]
        for call in fake_pipeline.calls
    ] == [
        "build",
        "redeploy",
    ]

    build_input = fake_pipeline.calls[0][1]

    assert Path(
        build_input.repository_path
    ) == (
        tmp_path
        / "dep_redeploy_build"
        / "repository"
    ).resolve()

    assert (
        build_input.build_command
        == "npm run build"
    )
    assert (
        build_input.output_directory
        == "dist"
    )
    assert build_input.timeout_seconds == 900
    assert build_input.environment == {
        "NODE_ENV": "production"
    }

    assert fake_pipeline.calls[1] == (
        "redeploy",
        "dep_redeploy_build",
        "dep_source",
    )


@pytest.mark.asyncio
async def test_redeploy_worker_stops_when_checkout_fails(
    tmp_path: Path,
    monkeypatch,
) -> None:
    fake_pipeline = FakeDeployPipeline()

    def fake_checkout(_request):
        raise WorkerGitCheckoutError(
            "redeploy checkout failed"
        )

    monkeypatch.setattr(
        redeploy_project,
        "deploy_pipeline",
        fake_pipeline,
    )
    monkeypatch.setattr(
        redeploy_project,
        "run_git_checkout",
        fake_checkout,
    )
    monkeypatch.setenv(
        "YGIT_WORKSPACE_ROOT",
        str(tmp_path),
    )

    with pytest.raises(
        WorkerGitCheckoutError
    ):
        await redeploy_project.run(
            {
                "deployment_id": (
                    "dep_redeploy_checkout_fail"
                ),
                "source_deployment_id": (
                    "dep_source"
                ),
                "repository_url": (
                    "https://github.com/vibtools/ygit"
                ),
                "build_command": "npm run build",
                "output_directory": "dist",
            }
        )

    assert fake_pipeline.calls == []


@pytest.mark.asyncio
async def test_redeploy_worker_raises_when_build_stage_fails(
    tmp_path: Path,
    monkeypatch,
) -> None:
    fake_pipeline = FakeDeployPipeline(
        build_status="failed"
    )

    def fake_checkout(request):
        request.destination_path.mkdir(
            parents=True,
            exist_ok=True,
        )
        (
            request.destination_path
            / "package.json"
        ).write_text(
            "{}",
            encoding="utf-8",
        )

        return SimpleNamespace(
            commit_sha="redeploy-failed-build"
        )

    monkeypatch.setattr(
        redeploy_project,
        "deploy_pipeline",
        fake_pipeline,
    )
    monkeypatch.setattr(
        redeploy_project,
        "run_git_checkout",
        fake_checkout,
    )
    monkeypatch.setenv(
        "YGIT_WORKSPACE_ROOT",
        str(tmp_path),
    )

    with pytest.raises(
        WorkerBuildStageFailedError
    ) as error_info:
        await redeploy_project.run(
            {
                "deployment_id": (
                    "dep_redeploy_build_fail"
                ),
                "source_deployment_id": (
                    "dep_source"
                ),
                "repository_url": (
                    "https://github.com/vibtools/ygit"
                ),
                "build_command": "npm run build",
                "output_directory": "dist",
            }
        )

    assert (
        error_info.value.code
        == "DEPLOY_BUILD_STAGE_FAILED"
    )

    assert [
        call[0]
        for call in fake_pipeline.calls
    ] == ["build"]


@pytest.mark.asyncio
async def test_redeploy_worker_accepts_completed_pipeline_result(
    monkeypatch,
) -> None:
    fake_pipeline = FakeDeployPipeline()

    monkeypatch.setattr(
        redeploy_project,
        "deploy_pipeline",
        fake_pipeline,
    )

    await redeploy_project.run(
        {
            "deployment_id": "dep_redeploy",
            "source_deployment_id": "dep_source",
        }
    )

    assert fake_pipeline.calls == [
        (
            "redeploy",
            "dep_redeploy",
            "dep_source",
        )
    ]


@pytest.mark.asyncio
async def test_redeploy_worker_rejects_prepared_pipeline_result(
    monkeypatch,
) -> None:
    fake_pipeline = FakeDeployPipeline(
        deployment_status="prepared",
        provider_calls_executed=False,
    )

    monkeypatch.setattr(
        redeploy_project,
        "deploy_pipeline",
        fake_pipeline,
    )

    with pytest.raises(
        WorkerDeploymentIncompleteError
    ) as error_info:
        await redeploy_project.run(
            {
                "deployment_id": "dep_redeploy_prepared",
                "source_deployment_id": "dep_source",
            }
        )

    assert (
        error_info.value.code
        == "DEPLOY_PIPELINE_INCOMPLETE"
    )


def test_deploy_worker_ignores_partial_build_payload_until_checkout_contract_is_complete() -> None:
    assert deploy_project._build_stage_input(
        "dep_partial",
        {
            "deployment_id": "dep_partial",
            "repository_path": "C:/ygit/work/dep_partial/repository",
            "build_command": "npm run build",
        },
    ) is None


def test_deploy_worker_workspace_payload_does_not_expose_repository_path_when_checkout_is_empty(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("YGIT_WORKSPACE_ROOT", str(tmp_path))

    payload = deploy_project._payload_with_workspace_if_checkout_ready(
        "dep_empty_checkout",
        {
            "deployment_id": "dep_empty_checkout",
            "build_command": "npm run build",
            "output_directory": "dist",
        },
    )

    assert "workspace_path" in payload
    assert "artifacts_path" in payload
    assert "repository_path" not in payload


def test_deploy_worker_build_handoff_keeps_architecture_boundaries() -> None:
    source = Path("backend/workers/jobs/deploy_project.py").read_text(encoding="utf-8")

    assert "from backend.pipelines.deploy_pipeline.public import DeployBuildStageInput, deploy_pipeline" in source
    assert "from backend.workers.workspace import prepare_repository_workspace" in source
    assert "from backend.workers.git_checkout import run_git_checkout" in source
    assert "from backend.workers.jobs.deployment_outcome import require_completed_pipeline_result" in source
    assert "from backend.workers.jobs.deployment_runtime import (" in source
    assert "WorkerBuildStageFailedError" in source
    assert "execute_build_stage" in source
    assert "require_completed_pipeline_result" in source
    assert "backend.pipelines.deploy_pipeline.internal" not in source
    assert "backend.providers" not in source
    assert "github_provider" not in source
    assert "cloudflare_provider" not in source

def test_redeploy_worker_build_handoff_keeps_architecture_boundaries() -> None:
    source = Path(
        "backend/workers/jobs/redeploy_project.py"
    ).read_text(encoding="utf-8")

    runtime_source = Path(
        "backend/workers/jobs/deployment_runtime.py"
    ).read_text(encoding="utf-8")

    assert (
        "from backend.workers.jobs."
        "deployment_runtime import ("
        in source
    )
    assert "run_git_checkout" in source
    assert "prepare_repository_workspace" in source
    assert "execute_build_stage" in source
    assert "execute_redeployment" in source
    assert "WorkerBuildStageFailedError" in source
    assert "require_completed_pipeline_result" in source

    for worker_source in (
        source,
        runtime_source,
    ):
        assert "backend.providers" not in worker_source
        assert (
            "backend.pipelines."
            "deploy_pipeline.internal"
            not in worker_source
        )
        assert "github_provider" not in worker_source
        assert "cloudflare_provider" not in worker_source
