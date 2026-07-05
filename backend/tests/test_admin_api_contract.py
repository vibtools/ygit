from fastapi.testclient import TestClient

from backend.app.dependencies.auth import require_admin
from backend.app.main import app
from backend.engines.auth_engine.schemas import CurrentUser


async def _admin_user() -> CurrentUser:
    return CurrentUser(
        id="user_admin_test",
        email="admin@example.com",
        name="Admin Test",
        roles=("ygit_admin",),
        status="active",
    )


def test_admin_overview_uses_response_envelope_with_admin_override() -> None:
    app.dependency_overrides[require_admin] = _admin_user
    try:
        client = TestClient(app)
        response = client.get("/api/v1/admin/overview")
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["error"] is None
        assert body["data"]["overview"]["title"] == "Platform Operations Console"
        assert "Platform Health" in body["data"]["overview"]["operations_focus"]
        assert "No Admin Engine" in body["data"]["overview"]["boundary"]
    finally:
        app.dependency_overrides.clear()


def test_admin_queue_status_contract_with_admin_override() -> None:
    app.dependency_overrides[require_admin] = _admin_user
    try:
        client = TestClient(app)
        response = client.get("/api/v1/admin/queue/status")
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"]["queue"]["retry_policy"]["owner"] == "Worker / Job System"
        queue_labels = [queue["label"] for queue in body["data"]["queue"]["queues"]]
        assert "Deployments Queue" in queue_labels
    finally:
        app.dependency_overrides.clear()


def test_admin_settings_do_not_expose_secrets() -> None:
    app.dependency_overrides[require_admin] = _admin_user
    try:
        client = TestClient(app)
        response = client.get("/api/v1/admin/settings")
        assert response.status_code == 200
        body_text = response.text.lower()
        assert "token" not in body_text
        assert "secret" in body_text
        assert "environment / secret store" in body_text
    finally:
        app.dependency_overrides.clear()
