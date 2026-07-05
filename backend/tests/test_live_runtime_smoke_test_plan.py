from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts.live_runtime_smoke_test import build_url, make_report


def test_live_runtime_smoke_plan_artifacts_exist() -> None:
    required = [
        "LIVE_RUNTIME_SMOKE_TEST_PLAN_v0.1.0.md",
        "LIVE_RUNTIME_SMOKE_TEST_CHECKLIST.md",
        "LIVE_RUNTIME_SMOKE_TEST_RUNBOOK.md",
        "LIVE_RUNTIME_SMOKE_TEST_MATRIX.json",
        "LIVE_RUNTIME_SMOKE_TEST_PLAN_DELIVERY_NOTE.md",
        "scripts/live_runtime_smoke_test.py",
    ]
    for artifact in required:
        assert Path(artifact).exists(), artifact


def test_live_runtime_smoke_matrix_contract() -> None:
    matrix = json.loads(Path("LIVE_RUNTIME_SMOKE_TEST_MATRIX.json").read_text())
    assert matrix["package"] == "YGIT_Live_Runtime_Smoke_Test_Plan_v0.1.0"
    assert matrix["version"] == "0.1.0"
    assert matrix["architecture_version"] == "1.1"
    assert "/api/v1/platform/health" in matrix["public_endpoints"]
    assert "/api/v1/admin/overview" in matrix["admin_endpoints"]
    assert any(phase["name"] == "worker_runtime" for phase in matrix["phases"])


def test_live_runtime_smoke_report_skips_optional_phases(monkeypatch) -> None:
    def fake_request(method: str, url: str, cookie: str | None = None, timeout: float = 10.0):
        if url.endswith("/api/v1/platform/health") or url.endswith("/api/v1/platform/version"):
            return 200, '{"success": true, "data": {}, "error": null, "meta": {}}', "application/json"
        if url.endswith("/dashboard"):
            return 200, "YGIT Dashboard", "text/html"
        if url.endswith("/admin"):
            return 200, "Platform Operations Console", "text/html"
        return 404, "not found", "text/plain"

    monkeypatch.setattr("scripts.live_runtime_smoke_test.request", fake_request)
    args = argparse.Namespace(
        base_url="https://ygit.example",
        include_authenticated=False,
        include_admin=False,
        session_cookie=None,
        admin_cookie=None,
        write_report=False,
        plan_only=False,
    )
    report = make_report(args)
    assert report["overall_status"] == "PASS"
    statuses = {check["name"]: check["status"] for check in report["checks"]}
    assert statuses["GET /api/v1/platform/health"] == "PASS"
    assert statuses["authenticated_phase"] == "SKIPPED"
    assert statuses["admin_phase"] == "SKIPPED"


def test_build_url_normalizes_base_url() -> None:
    assert build_url("https://ygit.example/", "/api/v1/platform/health") == "https://ygit.example/api/v1/platform/health"
