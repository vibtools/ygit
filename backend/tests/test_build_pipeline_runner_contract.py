from __future__ import annotations

import sys
from pathlib import Path

from backend.pipelines.build_pipeline.public import BuildPipelinePublicService
from backend.pipelines.build_pipeline.schemas import BuildExecutionInput, BuildPlan


def test_build_pipeline_runs_real_command_and_verifies_artifact(tmp_path: Path) -> None:
    build_script = tmp_path / "build_fixture.py"
    build_script.write_text(
        "from pathlib import Path\n"
        "Path('dist').mkdir(exist_ok=True)\n"
        "Path('dist/index.html').write_text('<h1>YGIT</h1>', encoding='utf-8')\n",
        encoding="utf-8",
    )

    result = BuildPipelinePublicService().run_build(
        BuildExecutionInput(
            repository_path=str(tmp_path),
            plan=BuildPlan(
                package_manager="none",
                build_command=f'"{sys.executable}" build_fixture.py',
                output_directory="dist",
                timeout_seconds=30,
            ),
        )
    )

    assert result.status == "succeeded"
    assert result.exit_code == 0
    assert result.artifact_ready is True
    assert Path(result.output_directory, "index.html").exists()


def test_build_pipeline_rejects_shell_operators(tmp_path: Path) -> None:
    result = BuildPipelinePublicService().run_build(
        BuildExecutionInput(
            repository_path=str(tmp_path),
            plan=BuildPlan(
                package_manager="npm",
                build_command="npm run build && echo unsafe",
                output_directory="dist",
            ),
        )
    )

    assert result.status == "invalid"
    assert "unsupported shell operators" in str(result.error_message)


def test_build_pipeline_rejects_secret_environment_keys(tmp_path: Path) -> None:
    result = BuildPipelinePublicService().run_build(
        BuildExecutionInput(
            repository_path=str(tmp_path),
            plan=BuildPlan(
                package_manager="none",
                build_command=f'"{sys.executable}" -c "print(123)"',
                output_directory="dist",
            ),
            environment={"APP_SECRET": "blocked"},
        )
    )

    assert result.status == "invalid"
    assert "Unsafe build environment key blocked" in str(result.error_message)


def test_build_pipeline_does_not_import_providers_or_api_routes() -> None:
    root = Path("backend/pipelines/build_pipeline")
    source = "\n".join(path.read_text(encoding="utf-8") for path in root.rglob("*.py"))

    assert "github_provider" not in source
    assert "cloudflare_provider" not in source
    assert "backend.app.routes" not in source
    assert "shell=True" not in source
