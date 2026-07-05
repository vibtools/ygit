from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read_platform_engine_files() -> str:
    parts: list[str] = []
    for path in (ROOT / "backend" / "engines" / "platform_engine").rglob("*.py"):
        parts.append(path.read_text())
    return "\n".join(parts)


def test_platform_engine_does_not_import_providers_or_pipeline() -> None:
    source = read_platform_engine_files()
    assert "backend.providers.github_provider" not in source
    assert "backend.providers.cloudflare_provider" not in source
    assert "backend.pipelines.deploy_pipeline" not in source


def test_platform_engine_does_not_import_other_engine_internals() -> None:
    source = read_platform_engine_files()
    forbidden = [
        "project_engine.internal",
        "repository_engine.internal",
        "repository_analysis_engine.internal",
        "deploy_engine.internal",
        "deployment_history_engine.internal",
        "audit_engine.internal",
    ]
    for marker in forbidden:
        assert marker not in source


def test_platform_engine_tables_are_owned_by_platform_engine() -> None:
    model_source = (ROOT / "backend" / "engines" / "platform_engine" / "models.py").read_text()
    assert '__tablename__ = "platform_settings"' in model_source
    assert '__tablename__ = "feature_flags"' in model_source
    migration = ROOT / "backend" / "migrations" / "versions" / "0011_platform_engine_settings_and_flags.py"
    assert migration.exists()
    migration_source = migration.read_text()
    assert 'create_table(\n        "platform_settings"' in migration_source
    assert 'create_table(\n        "feature_flags"' in migration_source
    assert "0010_audit_engine_audit_logs" in migration_source


def test_api_routes_use_platform_public_api_only() -> None:
    source = (ROOT / "backend" / "app" / "routes" / "platform_routes.py").read_text()
    assert "backend.engines.platform_engine.public" in source
    assert "backend.engines.platform_engine.internal" not in source
    assert "backend.engines.platform_engine.repository" not in source
    assert "backend.engines.platform_engine.models" not in source
