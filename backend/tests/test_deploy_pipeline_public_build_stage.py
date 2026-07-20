from __future__ import annotations

import sys
from pathlib import Path

from backend.pipelines.deploy_pipeline.internal.build_stage import DeployBuildStageInput
from backend.pipelines.deploy_pipeline.public import DeployPipeline


def test_deploy_pipeline_public_boundary_runs_isolated_build_stage(tmp_path: Path) -> None:
    build_script = tmp_path / "build_site.py"
    build_script.write_text(
        "from pathlib import Path\n"
        "Path('dist').mkdir(exist_ok=True)\n"
        "Path('dist/index.html').write_text('<main>YGIT public build</main>', encoding='utf-8')\n",
        encoding="utf-8",
    )

    result = DeployPipeline().execute_build_stage(
        DeployBuildStageInput(
            deployment_id="dep_public_build",
            repository_path=str(tmp_path),
            package_manager="none",
            build_command=f'"{sys.executable}" build_site.py',
            output_directory="dist",
            timeout_seconds=30,
        )
    )

    assert result.status == "succeeded"
    assert result.build_status == "succeeded"
    assert result.artifact_ready is True
    assert result.metadata["stage"] == "build"
    assert result.metadata["build_artifact_ready"] is True


def test_deploy_pipeline_public_build_stage_keeps_runtime_boundaries() -> None:
    source = Path("backend/pipelines/deploy_pipeline/public.py").read_text(encoding="utf-8")

    assert "execute_build_stage" in source
    assert "DeployPipelineBuildStage" in source
    assert "backend.providers" not in source
    assert "backend.app.routes" not in source
    assert "backend.pipelines.build_pipeline.internal" not in source
