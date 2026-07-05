from __future__ import annotations

import json
from pathlib import Path

from scripts.release_gate import run_gate


def test_release_gate_passes_without_live_database() -> None:
    report = run_gate(skip_db=True)
    assert report["overall_status"] == "PASS"
    statuses = {item["name"]: item["status"] for item in report["checks"]}
    assert statuses["required_imports"] == "PASS"
    assert statuses["api_route_registry"] == "PASS"
    assert statuses["migration_chain"] == "PASS"
    assert statuses["architecture_boundaries"] == "PASS"
    assert statuses["database_runtime"] == "SKIPPED"


def test_release_gate_and_live_smoke_artifacts_exist() -> None:
    required = [
        "MVP_INTEGRATION_REVIEW_AND_RELEASE_GATE_v0.1.0.md",
        "MVP_RELEASE_GATE_CHECKLIST.md",
        "MVP_RELEASE_GATE_REPORT.json",
        "INTEGRATION_REVIEW_DELIVERY_NOTE.md",
        "scripts/release_gate.py",
        "LIVE_RUNTIME_SMOKE_TEST_PLAN_v0.1.0.md",
        "LIVE_RUNTIME_SMOKE_TEST_CHECKLIST.md",
        "LIVE_RUNTIME_SMOKE_TEST_RUNBOOK.md",
        "LIVE_RUNTIME_SMOKE_TEST_MATRIX.json",
        "scripts/live_runtime_smoke_test.py",
    ]
    for artifact in required:
        assert Path(artifact).exists(), artifact


def test_live_runtime_smoke_manifest_contract() -> None:
    release = json.loads(Path("RELEASE.json").read_text())
    version = json.loads(Path("VERSION.json").read_text())
    manifest = json.loads(Path("CONTRACT_MANIFEST.json").read_text())
    assert release["component"] == "live_runtime_smoke_test_plan"
    assert release["release_type"] == "live_runtime_smoke_test_plan"
    assert release["owned_tables"] == []
    assert release["new_migration"] is None
    assert release["boundary"]["no_new_engine"] is True
    assert release["boundary"]["no_new_external_dependency"] is True
    assert version["release_gate"]["mvp_integration_review"] == "0.1.0"
    assert version["live_runtime_smoke_test_plan"]["version"] == "0.1.0"
    assert version["database"]["migration_head"] == "0012_notification_engine"
    assert manifest["release_gate"]["status"] == "pass"
    assert manifest["live_runtime_smoke_test_plan"]["status"] == "created"
