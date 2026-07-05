from backend.engines.repository_analysis_engine.internal.quick_analysis import QuickAnalysisRunner
from backend.engines.repository_engine.schemas import RepositoryAnalysisInput


def test_quick_analysis_detects_vite_repository() -> None:
    repository = RepositoryAnalysisInput(
        repository_id="repo_123",
        repository_url="https://github.com/vibtools/ygit-demo",
        owner="vibtools",
        repo="ygit-demo",
        default_branch="main",
        visibility="public",
        file_tree_snapshot={
            "files": [
                "package.json",
                "pnpm-lock.yaml",
                "vite.config.ts",
                "src/main.tsx",
                "index.html",
            ]
        },
    )

    result = QuickAnalysisRunner().run(repository)

    assert result.framework.framework == "vite"
    assert result.package_manager.package_manager == "pnpm"
    assert result.build_command.build_command == "pnpm build"
    assert result.output_directory.output_directory == "dist"
    assert result.static_dynamic.render_mode == "static"
    assert result.deploy_readiness.deploy_ready is True
    assert result.repository_score.score >= 80
    assert result.recommendations


def test_quick_analysis_marks_unknown_repository_not_deploy_ready() -> None:
    repository = RepositoryAnalysisInput(
        repository_id="repo_123",
        repository_url="https://github.com/vibtools/unknown",
        owner="vibtools",
        repo="unknown",
        default_branch="main",
        visibility="public",
        file_tree_snapshot={"files": ["README.md"]},
    )

    result = QuickAnalysisRunner().run(repository)

    assert result.framework.framework == "unknown"
    assert result.deploy_readiness.deploy_ready is False
    assert "Unsupported or unknown framework." in result.deploy_readiness.blocking_reasons
