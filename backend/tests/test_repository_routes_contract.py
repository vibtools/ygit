from fastapi.testclient import TestClient

from backend.app.main import app


def test_repository_routes_require_authentication() -> None:
    client = TestClient(app)
    response = client.post("/api/v1/repositories/validate", json={"repository_url": "https://github.com/vibtools/ygit"})
    assert response.status_code == 401
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "AUTH_REQUIRED"
    assert "trace_id" in body["meta"]


def test_repository_metadata_route_requires_authentication_before_provider_call() -> None:
    client = TestClient(app)
    response = client.post("/api/v1/repositories/metadata", json={"repository_url": "https://github.com/vibtools/ygit"})
    assert response.status_code == 401
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "AUTH_REQUIRED"
