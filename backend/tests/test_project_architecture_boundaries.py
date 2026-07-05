from pathlib import Path


def test_project_engine_does_not_import_providers_or_deploy_pipeline() -> None:
    engine_dir = Path("backend/engines/project_engine")
    source = "\n".join(path.read_text() for path in engine_dir.rglob("*.py"))
    assert "providers.github_provider" not in source
    assert "providers.cloudflare_provider" not in source
    assert "pipelines.deploy_pipeline" not in source


def test_other_engines_do_not_import_project_internal_modules() -> None:
    engines_dir = Path("backend/engines")
    offenders: list[str] = []
    for path in engines_dir.rglob("*.py"):
        if "project_engine" in path.parts:
            continue
        text = path.read_text()
        if "project_engine.internal" in text or "project_engine.repository" in text or "project_engine.models" in text:
            offenders.append(str(path))
    assert offenders == []
