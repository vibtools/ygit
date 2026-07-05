import json
from pathlib import Path


def test_release_manifest_matches_live_runtime_smoke_test_plan() -> None:
    data = json.loads(Path("RELEASE.json").read_text())
    assert data["component"] == "live_runtime_smoke_test_plan"
    assert data["version"] == "0.1.0"
    assert data["release_type"] == "live_runtime_smoke_test_plan"
    assert data["architecture_version"] == "1.1"
    assert data["engine_contract_version"] == "1.0"
    assert data["api_contract_version"] == "1.0"
    assert data["database_contract_version"] == "1.0"
    assert data["owned_tables"] == []
    assert data["new_migration"] is None
    assert data["database_migration_head"] == "0012_notification_engine"
    assert data["boundary"]["no_new_engine"] is True
    assert data["boundary"]["no_new_database_table"] is True
    assert data["boundary"]["no_new_external_dependency"] is True
    assert data["boundary"]["no_provider_execution_added"] is True


def test_version_registry_tracks_live_runtime_smoke_plan_and_prior_runtime() -> None:
    data = json.loads(Path("VERSION.json").read_text())
    assert data["architecture"] == "1.1"
    assert data["contracts"]["engine"] == "1.0"
    assert data["contracts"]["api"] == "1.0"
    assert data["contracts"]["database"] == "1.0"
    assert data["engines"]["deploy_engine"] == "0.1.0"
    assert data["engines"]["deployment_history_engine"] == "0.1.0"
    assert data["engines"]["domain_engine"] == "0.1.0"
    assert data["engines"]["audit_engine"] == "0.1.0"
    assert data["engines"]["platform_engine"] == "0.1.0"
    assert data["engines"]["notification_engine"] == "0.1.0"
    assert data["pipelines"]["deploy_pipeline"]["version"] == "0.1.0"
    assert data["worker"]["worker_runtime_integration"] == "0.1.0"
    assert data["frontend"]["dashboard"] == "0.1.0"
    assert data["frontend"]["admin_panel"] == "0.1.0"
    assert data["database"]["migration_head"] == "0012_notification_engine"
    assert data["release_gate"]["mvp_integration_review"] == "0.1.0"
    assert data["live_runtime_smoke_test_plan"]["version"] == "0.1.0"
    assert data["live_runtime_smoke_test_plan"]["adds_database_table"] is False
