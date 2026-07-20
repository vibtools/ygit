from __future__ import annotations

from pathlib import Path

from types import SimpleNamespace

import pytest

from backend.workers.jobs import deploy_project


class FakeDeployPipeline:
    def __init__(self, *, build_status: str = "succeeded") -> None:
        self.build_status = build_status
        self.calls: list[tuple[str, object]] = []

    def execute_build_stage(self, input_data):
        self.calls.append(("build", input_data))
        return SimpleNamespace(status=self.build_status)

    async def execute_deployment(self, deployment_id: str):
        self.calls.append(("deploy", deployment_id))


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
async def test_deploy_worker_stops_before_deployment_when_build_stage_fails(monkeypatch) -> None:
    fake_pipeline = FakeDeployPipeline(build_status="failed")
    monkeypatch.setattr(deploy_project, "deploy_pipeline", fake_pipeline)

    await deploy_project.run(
        {
            "deployment_id": "dep_3",
            "repository_path": "C:/ygit/work/dep_3/repository",
            "build_command": "npm run build",
            "output_directory": "dist",
        }
    )

    assert [call[0] for call in fake_pipeline.calls] == ["build"]


def test_deploy_worker_ignores_partial_build_payload_until_checkout_contract_is_complete() -> None:
    assert deploy_project._build_stage_input(
        "dep_partial",
        {
            "deployment_id": "dep_partial",
            "repository_path": "C:/ygit/work/dep_partial/repository",
            "build_command": "npm run build",
        },
    ) is None


def test_deploy_worker_build_handoff_keeps_architecture_boundaries() -> None:
    source = Path("backend/workers/jobs/deploy_project.py").read_text(encoding="utf-8")

    assert "from backend.pipelines.deploy_pipeline.public import DeployBuildStageInput, deploy_pipeline" in source
    assert "execute_build_stage" in source
    assert "backend.pipelines.deploy_pipeline.internal" not in source
    assert "backend.providers" not in source
    assert "github_provider" not in source
    assert "cloudflare_provider" not in source
