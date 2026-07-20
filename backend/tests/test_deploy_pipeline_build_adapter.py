from __future__ import annotations

import sys
from pathlib import Path

import pytest

from backend.pipelines.deploy_pipeline.internal.build_adapter import DeployPipelineBuildAdapter


def test_deploy_pipeline_build_adapter_runs_real_build_and_verifies_artifact(tmp_path: Path) -> None:
    build_script = tmp_path / "build_site.py"
    build_script.write_text(
        "from pathlib import Path\n"
        "Path('dist').mkdir(exist_ok=True)\n"
        "Path('dist/index.html').write_text('<main>YGIT build</main>', encoding='utf-8')\n",
        encoding="utf-8",
    )

    result = DeployPipelineBuildAdapter().run_repository_build(
        repository_path=str(tmp_path),
        package_manager="none",
        build_command=f'"{sys.executable}" build_site.py',
        output_directory="dist",
        timeout_seconds=30,
    )

    assert result.status == "succeeded"
    assert result.artifact_ready is True
    assert Path(result.output_directory, "index.html").exists()


def test_deploy_pipeline_build_adapter_requires_build_command(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="build command is required"):
        DeployPipelineBuildAdapter().run_repository_build(
            repository_path=str(tmp_path),
            package_manager="npm",
            build_command=None,
            output_directory="dist",
        )


def test_deploy_pipeline_build_adapter_requires_output_directory(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="output directory is required"):
        DeployPipelineBuildAdapter().run_repository_build(
            repository_path=str(tmp_path),
            package_manager="npm",
            build_command="npm run build",
            output_directory=None,
        )


def test_deploy_pipeline_build_adapter_keeps_provider_and_api_boundaries() -> None:
    source = Path("backend/pipelines/deploy_pipeline/internal/build_adapter.py").read_text(encoding="utf-8")

    assert "backend.pipelines.build_pipeline.public" in source
    assert "backend.pipelines.build_pipeline.internal" not in source
    assert "backend.providers" not in source
    assert "backend.app.routes" not in source
    assert "github_provider" not in source
    assert "cloudflare_provider" not in source
