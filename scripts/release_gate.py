#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

IMPLEMENTED_ENGINES = [
    "auth_engine",
    "project_engine",
    "repository_engine",
    "repository_analysis_engine",
    "deploy_engine",
    "deployment_history_engine",
    "domain_engine",
    "audit_engine",
    "platform_engine",
    "notification_engine",
]

REQUIRED_MIGRATIONS = [
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

REQUIRED_ROUTES = {
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
    "/api/v1/projects/{project_id}/readiness",
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

REQUIRED_IMPORTS = [
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
    "backend.app.admin_surface.service",
    "scripts.live_runtime_smoke_test",
]

PROVIDER_IMPORTS = [
    "backend.providers.github_provider",
    "backend.providers.cloudflare_provider",
]

SECRET_KEY_PATTERNS = re.compile(
    r"(?i)(token|secret|password|private_key|client_secret|authorization)[\w\-\s]*[:=][\w\-+/=]{12,}"
)


@dataclass(frozen=True)
class GateCheck:
    name: str
    status: str
    details: str

    def as_dict(self) -> dict[str, str]:
        return {"name": self.name, "status": self.status, "details": self.details}


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def python_files(root: Path) -> Iterable[Path]:
    yield from root.rglob("*.py")


def check_required_imports() -> GateCheck:
    failures: list[str] = []
    for module in REQUIRED_IMPORTS:
        try:
            importlib.import_module(module)
        except Exception as exc:  # pragma: no cover - release script
            failures.append(f"{module}: {exc}")
    if failures:
        return GateCheck("required_imports", "FAIL", "; ".join(failures))
    return GateCheck("required_imports", "PASS", f"{len(REQUIRED_IMPORTS)} import boundaries load")


def check_route_registry() -> GateCheck:
    from backend.app.main import app

    actual = set(app.openapi().get('paths', {}).keys())
    actual.update({'/dashboard', '/dashboard/assets/{asset_path:path}', '/admin', '/admin/assets/{asset_path:path}'})
    missing = sorted(REQUIRED_ROUTES - actual)
    if missing:
        return GateCheck("api_route_registry", "FAIL", "missing: " + ", ".join(missing))
    return GateCheck("api_route_registry", "PASS", f"{len(REQUIRED_ROUTES)} MVP routes registered")


def check_runtime_smoke() -> GateCheck:
    from fastapi.testclient import TestClient
    from backend.app.main import app

    client = TestClient(app)
    public_checks = [
        ("/api/v1/platform/version", "success"),
        ("/api/v1/platform/health", "success"),
    ]
    protected_shell_checks = [
        ("/dashboard", 401),
        ("/admin", 401),
    ]

    failures: list[str] = []

    for path, marker in public_checks:
        response = client.get(path)
        if response.status_code != 200:
            failures.append(f"{path}: HTTP {response.status_code}")
            continue
        if marker == "success" and response.json().get("success") is not True:
            failures.append(f"{path}: missing success envelope")

    for path, expected_status in protected_shell_checks:
        response = client.get(path, follow_redirects=False)
        if response.status_code != expected_status:
            failures.append(f"{path}: expected HTTP {expected_status}, got HTTP {response.status_code}")

    if failures:
        return GateCheck("runtime_smoke", "FAIL", "; ".join(failures))
    return GateCheck("runtime_smoke", "PASS", "API entrypoints respond and protected shells reject unauthenticated access")


def check_migration_chain() -> GateCheck:
    versions = ROOT / "backend" / "migrations" / "versions"
    missing = [name for name in REQUIRED_MIGRATIONS if not (versions / name).exists()]
    if missing:
        return GateCheck("migration_chain", "FAIL", "missing: " + ", ".join(missing))
    head = REQUIRED_MIGRATIONS[-1]
    version_data = json.loads(read(ROOT / "VERSION.json"))
    if version_data.get("database", {}).get("migration_head") != "0012_notification_engine":
        return GateCheck("migration_chain", "FAIL", "VERSION.json migration head is not 0012_notification_engine")
    return GateCheck("migration_chain", "PASS", f"{len(REQUIRED_MIGRATIONS)} ordered migrations present; head remains {head}")


def check_manifest_alignment() -> GateCheck:
    release = json.loads(read(ROOT / "RELEASE.json"))
    version = json.loads(read(ROOT / "VERSION.json"))
    manifest = json.loads(read(ROOT / "CONTRACT_MANIFEST.json"))
    failures: list[str] = []
    if release.get("component") != "live_runtime_smoke_test_plan":
        failures.append("RELEASE.json component mismatch")
    if release.get("release_type") != "live_runtime_smoke_test_plan":
        failures.append("RELEASE.json release_type mismatch")
    if version.get("release_gate", {}).get("mvp_integration_review") != "0.1.0":
        failures.append("VERSION.json release gate missing")
    if manifest.get("release_gate", {}).get("status") != "pass":
        failures.append("CONTRACT_MANIFEST release gate status missing")
    if manifest.get("live_runtime_smoke_test_plan", {}).get("status") != "created":
        failures.append("CONTRACT_MANIFEST live runtime smoke plan missing")
    implemented = set(version.get("engines", {}).keys())
    for engine in IMPLEMENTED_ENGINES:
        if engine not in implemented:
            failures.append(f"VERSION.json missing engine {engine}")
    if failures:
        return GateCheck("manifest_alignment", "FAIL", "; ".join(failures))
    return GateCheck("manifest_alignment", "PASS", "Release, version, and contract manifests align with MVP gate")


def check_architecture_boundaries() -> GateCheck:
    failures: list[str] = []
    if (ROOT / "backend" / "engines" / "admin_engine").exists():
        failures.append("backend/engines/admin_engine exists")

    forbidden_provider_consumers = [
        ROOT / "backend" / "engines" / "deploy_engine",
        ROOT / "backend" / "engines" / "deployment_history_engine",
        ROOT / "backend" / "engines" / "domain_engine",
        ROOT / "backend" / "engines" / "audit_engine",
        ROOT / "backend" / "engines" / "platform_engine",
        ROOT / "backend" / "engines" / "notification_engine",
        ROOT / "backend" / "app" / "routes",
        ROOT / "backend" / "app" / "admin_surface",
        ROOT / "backend" / "workers" / "jobs",
    ]
    for directory in forbidden_provider_consumers:
        if not directory.exists():
            continue
        for path in python_files(directory):
            text = read(path)
            for marker in PROVIDER_IMPORTS:
                if marker in text:
                    failures.append(f"{path.relative_to(ROOT)} imports {marker}")

    # Deploy jobs may call Deploy Pipeline but must not call providers or engine repositories.
    worker_jobs = ROOT / "backend" / "workers" / "jobs"
    if worker_jobs.exists():
        for path in python_files(worker_jobs):
            text = read(path)
            if ".repository" in text and "backend.workers" not in text:
                failures.append(f"{path.relative_to(ROOT)} imports repository layer")

    if failures:
        return GateCheck("architecture_boundaries", "FAIL", "; ".join(failures))
    return GateCheck("architecture_boundaries", "PASS", "No forbidden provider/admin/worker boundary violations found")


def check_secret_scan() -> GateCheck:
    allowed_fragments = [
        "CLIENT_SECRET=",
        "SESSION_SECRET=",
        "GITHUB_OAUTH_CLIENT_SECRET=",
        "CLOUDFLARE_OAUTH_CLIENT_SECRET=",
        "token_secret_ref=",
        "token_key_version=",
        "authorization_url=",
    ]
    findings: list[str] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() in {".pyc", ".zip", ".png", ".jpg", ".jpeg"}:
            continue
        if any(part.startswith(".") for part in path.relative_to(ROOT).parts):
            continue
        try:
            text = read(path)
        except UnicodeDecodeError:
            continue
        for match in SECRET_KEY_PATTERNS.finditer(text):
            line = match.group(0)
            if any(fragment in line for fragment in allowed_fragments):
                continue
            findings.append(f"{path.relative_to(ROOT)}: {line[:80]}")
            if len(findings) >= 10:
                break
        if len(findings) >= 10:
            break
    if findings:
        return GateCheck("basic_secret_scan", "FAIL", "; ".join(findings))
    return GateCheck("basic_secret_scan", "PASS", "No obvious committed secrets found in text files")


def check_release_artifacts() -> GateCheck:
    required = [
        "MVP_INTEGRATION_REVIEW_AND_RELEASE_GATE_v0.1.0.md",
        "MVP_RELEASE_GATE_CHECKLIST.md",
        "MVP_RELEASE_GATE_REPORT.json",
        "INTEGRATION_REVIEW_DELIVERY_NOTE.md",
        "LIVE_RUNTIME_SMOKE_TEST_PLAN_v0.1.0.md",
        "LIVE_RUNTIME_SMOKE_TEST_CHECKLIST.md",
        "LIVE_RUNTIME_SMOKE_TEST_RUNBOOK.md",
        "LIVE_RUNTIME_SMOKE_TEST_MATRIX.json",
        "LIVE_RUNTIME_SMOKE_TEST_PLAN_DELIVERY_NOTE.md",
        "scripts/live_runtime_smoke_test.py",
        "RELEASE.json",
        "VERSION.json",
        "CONTRACT_MANIFEST.json",
        "CHANGELOG.md",
        "AUDIT_REPORT.md",
    ]
    missing = [name for name in required if not (ROOT / name).exists()]
    if missing:
        return GateCheck("release_artifacts", "FAIL", "missing: " + ", ".join(missing))
    return GateCheck("release_artifacts", "PASS", f"{len(required)} release gate artifacts present")


def check_db_optional(skip_db: bool) -> GateCheck:
    if skip_db:
        return GateCheck("database_runtime", "SKIPPED", "live PostgreSQL check skipped")
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import asyncio; from backend.core.database import database_health; print(asyncio.run(database_health()))",
        ],
        capture_output=True,
        text=True,
        check=False,
        cwd=ROOT,
    )
    if result.returncode != 0:
        return GateCheck("database_runtime", "FAIL", result.stderr.strip() or result.stdout.strip())
    if "ok" not in result.stdout:
        return GateCheck("database_runtime", "FAIL", "database health did not return ok")
    return GateCheck("database_runtime", "PASS", "database health returned ok")


def run_gate(skip_db: bool) -> dict[str, object]:
    checks = [
        check_required_imports(),
        check_route_registry(),
        check_runtime_smoke(),
        check_migration_chain(),
        check_manifest_alignment(),
        check_architecture_boundaries(),
        check_release_artifacts(),
        check_secret_scan(),
        check_db_optional(skip_db),
    ]
    failures = [check for check in checks if check.status == "FAIL"]
    report = {
        "product": "YGIT",
        "package": "YGIT_Live_Runtime_Smoke_Test_Plan_v0.1.0",
        "release_gate_version": "0.1.0",
        "architecture_version": "1.1",
        "engine_contract_version": "1.0",
        "api_contract_version": "1.0",
        "database_contract_version": "1.0",
        "overall_status": "PASS" if not failures else "FAIL",
        "checks": [check.as_dict() for check in checks],
        "failures": [check.as_dict() for check in failures],
        "live_runtime_not_executed": [
            "Cloudflare Pages deployment",
            "GitHub API integration",
            "Cloudflare API integration",
            "live Redis worker loop",
            "live runtime smoke against production URL",
        ],
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="YGIT MVP Integration Review and Release Gate")
    parser.add_argument("--skip-db", action="store_true", help="Skip live PostgreSQL health check")
    parser.add_argument("--write-report", action="store_true", help="Write MVP_RELEASE_GATE_REPORT.json")
    args = parser.parse_args()
    report = run_gate(skip_db=args.skip_db)
    if args.write_report:
        (ROOT / "MVP_RELEASE_GATE_REPORT.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["overall_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
