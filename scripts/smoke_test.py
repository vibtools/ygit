#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def check_imports() -> list[str]:
    modules = [
        "backend.app.main",
        "backend.core.database",
        "backend.engines.auth_engine.public",
        "backend.engines.project_engine.public",
        "backend.engines.repository_engine.public",
        "backend.engines.repository_analysis_engine.public",
        "backend.engines.auth_engine.connected_accounts_module.public",
        "backend.engines.deploy_engine.public",
        "backend.engines.deployment_history_engine.public",
        "backend.engines.domain_engine.public",
        "backend.engines.audit_engine.public",
        "backend.engines.platform_engine.public",
        "backend.engines.notification_engine.public",
        "backend.pipelines.deploy_pipeline.public",
        "backend.workers.worker",
        "backend.workers.public",
        "backend.workers.repository",
        "backend.app.routes.dashboard_routes",
        "backend.app.routes.admin_panel_routes",
        "backend.app.routes.admin_routes",
        "backend.app.admin_surface.service",
        "backend.providers.github_provider.client",
        "backend.providers.cloudflare_provider.client",
        "scripts.release_gate",
        "scripts.live_runtime_smoke_test",
    ]
    failures: list[str] = []
    for module in modules:
        try:
            importlib.import_module(module)
        except Exception as exc:  # pragma: no cover - smoke script
            failures.append(f"import {module}: {exc}")
    return failures


def check_routes() -> list[str]:
    from backend.app.main import app

    expected = {
        "/api/v1/platform/health",
        "/api/v1/platform/version",
        "/api/v1/platform/status",
        "/api/v1/platform/feature-flags",
        "/api/v1/auth/login",
        "/api/v1/me",
        "/api/v1/projects",
        "/api/v1/repositories/validate",
        "/api/v1/repositories/metadata",
        "/api/v1/repository-analysis/quick",
        "/api/v1/repository-analysis/deep",
        "/api/v1/connected-accounts",
        "/api/v1/connected-accounts/{provider}/connect",
        "/api/v1/domains/check",
        "/api/v1/projects/{project_id}/domain",
        "/api/v1/projects/{project_id}/deploy",
        "/api/v1/deployments/{deployment_id}",
        "/api/v1/deployments/{deployment_id}/redeploy",
        "/api/v1/deployments/{deployment_id}/cancel",
        "/api/v1/deployments/{deployment_id}/logs",
        "/api/v1/projects/{project_id}/deployments",
        "/api/v1/jobs/{job_id}",
        "/api/v1/notifications/{notification_id}/read",
        "/api/v1/notifications/unread-count",
        "/api/v1/notifications",
        "/dashboard",
        "/dashboard/assets/{asset_path:path}",
        "/admin",
        "/admin/assets/{asset_path:path}",
        "/api/v1/admin/overview",
        "/api/v1/admin/platform/health",
        "/api/v1/admin/queue/status",
        "/api/v1/admin/system-monitoring",
        "/api/v1/admin/deployments",
        "/api/v1/admin/users",
        "/api/v1/admin/audit-logs",
        "/api/v1/admin/settings",
        "/api/v1/admin/manifest",
    }
    actual = set(app.openapi().get('paths', {}).keys())
    actual.update({'/dashboard', '/dashboard/assets/{asset_path:path}', '/admin', '/admin/assets/{asset_path:path}'})
    return [f"missing route: {route}" for route in sorted(expected - actual)]


def check_health() -> list[str]:
    from fastapi.testclient import TestClient
    from backend.app.main import app

    client = TestClient(app)
    response = client.get("/api/v1/platform/version")
    if response.status_code != 200:
        return [f"platform version failed: HTTP {response.status_code}"]
    body = response.json()
    if body.get("success") is not True:
        return ["platform version did not use success envelope"]
    dashboard = client.get("/dashboard")
    if dashboard.status_code != 401:
        return [f"dashboard protected route failed: HTTP {dashboard.status_code}"]
    admin = client.get("/admin")
    if admin.status_code != 401:
        return [f"admin protected route failed: HTTP {admin.status_code}"]
    return []


def check_migrations() -> list[str]:
    versions = Path("backend/migrations/versions")
    expected = [
        "0001_auth_engine_users_and_identities.py",
        "0002_project_engine_projects.py",
        "0003_repository_engine_repository_metadata.py",
        "0004_repository_analysis_engine_analysis_results.py",
        "0005_connected_accounts_module.py",
        "0006_deploy_engine_deployments.py",
        "0007_deployment_history_engine.py",
        "0008_worker_runtime_jobs.py",
        "0009_domain_engine_domains.py",
        "0010_audit_engine_audit_logs.py",
        "0011_platform_engine_settings_and_flags.py",
        "0012_notification_engine_notifications.py",
    ]
    return [f"missing migration: {name}" for name in expected if not (versions / name).exists()]



def check_live_runtime_smoke_artifacts() -> list[str]:
    required = [
        "LIVE_RUNTIME_SMOKE_TEST_PLAN_v0.1.0.md",
        "LIVE_RUNTIME_SMOKE_TEST_CHECKLIST.md",
        "LIVE_RUNTIME_SMOKE_TEST_RUNBOOK.md",
        "LIVE_RUNTIME_SMOKE_TEST_MATRIX.json",
        "LIVE_RUNTIME_SMOKE_TEST_PLAN_DELIVERY_NOTE.md",
        "scripts/live_runtime_smoke_test.py",
    ]
    return [f"missing live runtime smoke artifact: {name}" for name in required if not Path(name).exists()]


def check_release_gate_artifacts() -> list[str]:
    required = [
        "MVP_INTEGRATION_REVIEW_AND_RELEASE_GATE_v0.1.0.md",
        "MVP_RELEASE_GATE_CHECKLIST.md",
        "MVP_RELEASE_GATE_REPORT.json",
        "INTEGRATION_REVIEW_DELIVERY_NOTE.md",
        "scripts/release_gate.py",
    ]
    return [f"missing release gate artifact: {name}" for name in required if not Path(name).exists()]


def check_db_optional(skip_db: bool) -> list[str]:
    if skip_db:
        return []
    result = subprocess.run(
        [sys.executable, "-c", "import asyncio; from backend.core.database import database_health; print(asyncio.run(database_health()))"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return ["database health failed: " + (result.stderr.strip() or result.stdout.strip())]
    if "ok" not in result.stdout:
        return ["database health did not return ok"]
    return []


def main() -> int:
    parser = argparse.ArgumentParser(description="YGIT runtime smoke test")
    parser.add_argument("--skip-db", action="store_true", help="Skip live database connection check")
    args = parser.parse_args()

    failures: list[str] = []
    failures.extend(check_imports())
    failures.extend(check_routes())
    failures.extend(check_health())
    failures.extend(check_migrations())
    failures.extend(check_release_gate_artifacts())
    failures.extend(check_live_runtime_smoke_artifacts())
    failures.extend(check_db_optional(args.skip_db))

    report = {
        "success": not failures,
        "checks": {
            "imports": "checked",
            "routes": "checked",
            "health": "checked",
            "migrations": "checked",
            "release_gate_artifacts": "checked",
            "live_runtime_smoke_artifacts": "checked",
            "database": "skipped" if args.skip_db else "checked",
        },
        "failures": failures,
    }
    print(json.dumps(report, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
