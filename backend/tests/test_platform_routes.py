from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app.dependencies.auth import require_user
from backend.app.main import app
from backend.engines.auth_engine.schemas import CurrentUser


async def _user() -> CurrentUser:
    return CurrentUser(
        id="user_platform_test",
        email="platform@example.com",
        name="Platform Test",
        roles=(),
        status="active",
    )


def test_health_response_envelope() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/platform/health")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["error"] is None
    assert "data" in body
    assert "meta" in body
    assert "trace_id" in body["meta"]
    assert body["data"]["status"] in {"ok", "warning"}
    assert body["data"]["worker"] == "configured"


def test_version_contracts() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/platform/version")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["api_contract"] == "1.0"
    assert data["engine_contract"] == "1.0"
    assert data["database_architecture"] == "1.0"
    assert data["architecture_freeze"] == "1.1"
    assert data["platform_engine"] == "0.1.0"


def test_system_status_contract_with_auth_override() -> None:
    app.dependency_overrides[require_user] = _user
    try:
        client = TestClient(app)
        response = client.get("/api/v1/platform/status")
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"]["maintenance"] is False
        assert body["data"]["queue_status"] == "configured"
        assert body["data"]["worker_status"] == "configured"
    finally:
        app.dependency_overrides.clear()


def test_feature_flags_contract_with_auth_override() -> None:
    app.dependency_overrides[require_user] = _user
    try:
        client = TestClient(app)
        response = client.get("/api/v1/platform/feature-flags")
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"]["flags"]["templates_beta"] is True
        assert body["data"]["flags"]["marketplace_preview"] is False
        assert "items" in body["data"]
    finally:
        app.dependency_overrides.clear()
