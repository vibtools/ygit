from __future__ import annotations

import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from backend.pipelines.deploy_pipeline.internal.build_stage import (
    DeployBuildStageInput,
    DeployPipelineBuildStage,
)


def test_deploy_pipeline_build_stage_runs_build_and_maps_result(tmp_path: Path) -> None:
    build_script = tmp_path / "build_site.py"
    build_script.write_text(
        "from pathlib import Path\n"
        "Path('dist').mkdir(exist_ok=True)\n"
        "Path('dist/index.html').write_text('<main>YGIT</main>', encoding='utf-8')\n",
        encoding="utf-8",
    )

    result = DeployPipelineBuildStage().run(
        DeployBuildStageInput(
            deployment_id="dep_build_1",
            repository_path=str(tmp_path),
            package_manager="none",
            build_command=f'"{sys.executable}" build_site.py',
            output_directory="dist",
            timeout_seconds=30,
        )
    )

    assert result.deployment_id == "dep_build_1"
    assert result.status == "succeeded"
    assert result.build_status == "succeeded"
    assert result.artifact_ready is True
    assert "dist" in result.output_directory
    assert result.metadata["stage"] == "build"
    assert result.metadata["build_artifact_ready"] is True
    assert any("artifact verified" in log.message for log in result.logs)


def test_deploy_pipeline_build_stage_maps_invalid_build_to_failed(tmp_path: Path) -> None:
    result = DeployPipelineBuildStage().run(
        DeployBuildStageInput(
            deployment_id="dep_build_invalid",
            repository_path=str(tmp_path),
            package_manager="npm",
            build_command="npm run build && echo unsafe",
            output_directory="dist",
            timeout_seconds=30,
        )
    )

    assert result.status == "failed"
    assert result.build_status == "invalid"
    assert result.artifact_ready is False
    assert result.error_message is not None
    assert "unsupported shell operators" in result.error_message
    assert result.metadata["build_status"] == "invalid"


def test_deploy_pipeline_build_stage_requires_worker_repository_path() -> None:
    with pytest.raises(ValidationError):
        DeployBuildStageInput(
            deployment_id="dep_missing_repo",
            repository_path="",
            package_manager="none",
            build_command=f'"{sys.executable}" -c "print(123)"',
            output_directory="dist",
        )


def test_deploy_pipeline_build_stage_keeps_boundaries() -> None:
    source = Path("backend/pipelines/deploy_pipeline/internal/build_stage.py").read_text(encoding="utf-8")

    assert "DeployPipelineBuildAdapter" in source
    assert "backend.pipelines.build_pipeline.internal" not in source
    assert "backend.providers" not in source
    assert "backend.app.routes" not in source
    assert "github_provider" not in source
    assert "cloudflare_provider" not in source
