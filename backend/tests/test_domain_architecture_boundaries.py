from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read_engine_files() -> str:
    parts: list[str] = []
    for path in (ROOT / "backend" / "engines" / "domain_engine").rglob("*.py"):
        parts.append(path.read_text())
    return "\n".join(parts)


def test_domain_engine_does_not_import_providers_or_pipeline() -> None:
    source = read_engine_files()
    assert "backend.providers.github_provider" not in source
    assert "backend.providers.cloudflare_provider" not in source
    assert "backend.pipelines.deploy_pipeline" not in source


def test_domain_routes_use_public_engine_api_only() -> None:
    source = (ROOT / "backend" / "app" / "routes" / "domain_routes.py").read_text()
    assert "backend.engines.domain_engine.public" in source
    assert "backend.engines.domain_engine.internal" not in source
    assert "backend.engines.domain_engine.repository" not in source
    assert "backend.engines.domain_engine.models" not in source


def test_project_routes_use_domain_public_api_only_for_domain_endpoints() -> None:
    source = (ROOT / "backend" / "app" / "routes" / "project_routes.py").read_text()
    assert "backend.engines.domain_engine.public" in source
    assert "backend.engines.domain_engine.internal" not in source
    assert "FeatureNotEnabledError(\"Domain Engine\")" not in source


def test_domain_migration_exists() -> None:
    migration = ROOT / "backend" / "migrations" / "versions" / "0009_domain_engine_domains.py"
    assert migration.exists()
    source = migration.read_text()
    assert "create_table(\n        \"domains\"" in source
    assert "0008_worker_runtime_jobs" in source
