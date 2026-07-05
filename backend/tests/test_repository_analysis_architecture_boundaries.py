from pathlib import Path


def test_repository_analysis_engine_does_not_import_cloudflare_or_deploy_pipeline() -> None:
    engine_dir = Path("backend/engines/repository_analysis_engine")
    source = "\n".join(path.read_text() for path in engine_dir.rglob("*.py"))
    assert "providers.cloudflare_provider" not in source
    assert "pipelines.deploy_pipeline" not in source
    assert "deploy_engine.internal" not in source
    assert "project_engine.internal" not in source


def test_other_engines_do_not_import_repository_analysis_internal_modules() -> None:
    engines_dir = Path("backend/engines")
    offenders: list[str] = []
    for path in engines_dir.rglob("*.py"):
        if "repository_analysis_engine" in path.parts:
            continue
        text = path.read_text()
        if (
            "repository_analysis_engine.internal" in text
            or "repository_analysis_engine.repository" in text
            or "repository_analysis_engine.models" in text
        ):
            offenders.append(str(path))
    assert offenders == []


def test_repository_analysis_engine_modules_are_present() -> None:
    expected = {
        "quick_analysis.py",
        "framework_detection.py",
        "package_manager_detection.py",
        "build_command_detection.py",
        "output_directory_detection.py",
        "static_dynamic_detection.py",
        "deploy_readiness.py",
        "repository_score.py",
        "warnings.py",
        "recommendations.py",
        "deep_analysis.py",
        "result_store.py",
    }
    actual = {path.name for path in Path("backend/engines/repository_analysis_engine/internal").glob("*.py")}
    assert expected.issubset(actual)
