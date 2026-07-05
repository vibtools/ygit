from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read_engine_files() -> str:
    parts: list[str] = []
    for path in (ROOT / "backend" / "engines" / "audit_engine").rglob("*.py"):
        parts.append(path.read_text())
    return "\n".join(parts)


def test_audit_engine_does_not_import_providers_or_pipeline() -> None:
    source = read_engine_files()
    assert "backend.providers.github_provider" not in source
    assert "backend.providers.cloudflare_provider" not in source
    assert "backend.pipelines.deploy_pipeline" not in source


def test_admin_audit_route_uses_audit_public_api_only() -> None:
    source = (ROOT / "backend" / "app" / "routes" / "admin_routes.py").read_text()
    assert "backend.engines.audit_engine.public" in source
    assert "backend.engines.audit_engine.internal" not in source
    assert "backend.engines.audit_engine.repository" not in source
    assert "backend.engines.audit_engine.models" not in source


def test_audit_repository_is_append_only_by_contract() -> None:
    source = (ROOT / "backend" / "engines" / "audit_engine" / "repository.py").read_text()
    assert "async def create" in source
    assert "async def list" in source
    assert "async def delete(" not in source
    assert "async def update(" not in source
    assert "AuditDeleteForbiddenError" in source


def test_audit_migration_exists_and_declares_immutability() -> None:
    migration = ROOT / "backend" / "migrations" / "versions" / "0010_audit_engine_audit_logs.py"
    assert migration.exists()
    source = migration.read_text()
    assert 'create_table(\n        "audit_logs"' in source
    assert "0009_domain_engine_domains" in source
    assert "trg_prevent_audit_logs_update" in source
    assert "trg_prevent_audit_logs_delete" in source
