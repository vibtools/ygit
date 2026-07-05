from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read_notification_engine_files() -> str:
    parts: list[str] = []
    for path in (ROOT / "backend" / "engines" / "notification_engine").rglob("*.py"):
        parts.append(path.read_text())
    return "\n".join(parts)


def test_notification_engine_does_not_import_providers_or_pipeline() -> None:
    source = read_notification_engine_files()
    assert "backend.providers.github_provider" not in source
    assert "backend.providers.cloudflare_provider" not in source
    assert "backend.pipelines.deploy_pipeline" not in source


def test_notification_engine_does_not_mutate_other_engine_internals() -> None:
    source = read_notification_engine_files()
    forbidden = [
        "project_engine.internal",
        "repository_engine.internal",
        "repository_analysis_engine.internal",
        "deploy_engine.internal",
        "deployment_history_engine.internal",
        "platform_engine.repository",
        "audit_engine.repository",
    ]
    for marker in forbidden:
        assert marker not in source


def test_notification_engine_table_owned_by_notification_engine() -> None:
    model_source = (ROOT / "backend" / "engines" / "notification_engine" / "models.py").read_text()
    assert '__tablename__ = "notifications"' in model_source
    migration = ROOT / "backend" / "migrations" / "versions" / "0012_notification_engine_notifications.py"
    assert migration.exists()
    migration_source = migration.read_text()
    assert 'create_table(\n        "notifications"' in migration_source
    assert 'down_revision = "0011_platform_engine"' in migration_source


def test_notification_routes_use_public_api_only() -> None:
    source = (ROOT / "backend" / "app" / "routes" / "notification_routes.py").read_text()
    assert "backend.engines.notification_engine.public" in source
    assert "backend.engines.notification_engine.internal" not in source
    assert "backend.engines.notification_engine.repository" not in source
    assert "backend.engines.notification_engine.models" not in source
