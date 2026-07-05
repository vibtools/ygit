from pathlib import Path


def test_repository_engine_does_not_import_cloudflare_or_deploy_pipeline() -> None:
    engine_dir = Path("backend/engines/repository_engine")
    source = "\n".join(path.read_text() for path in engine_dir.rglob("*.py"))
    assert "providers.cloudflare_provider" not in source
    assert "pipelines.deploy_pipeline" not in source
    assert "deploy_engine.internal" not in source
    assert "repository_analysis_engine.internal" not in source


def test_other_engines_do_not_import_repository_internal_modules() -> None:
    engines_dir = Path("backend/engines")
    offenders: list[str] = []
    for path in engines_dir.rglob("*.py"):
        if "repository_engine" in path.parts:
            continue
        text = path.read_text()
        if (
            "repository_engine.internal" in text
            or "repository_engine.repository" in text
            or "repository_engine.models" in text
        ):
            offenders.append(str(path))
    assert offenders == []
