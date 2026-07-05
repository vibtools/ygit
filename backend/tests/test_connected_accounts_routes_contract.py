from fastapi.testclient import TestClient

from backend.app.main import app


def test_connected_accounts_routes_require_authentication() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/connected-accounts")
    assert response.status_code == 401
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "AUTH_REQUIRED"


def test_connected_accounts_provider_connect_requires_authentication() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/connected-accounts/github/connect")
    assert response.status_code == 401
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "AUTH_REQUIRED"
