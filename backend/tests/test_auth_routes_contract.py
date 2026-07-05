from fastapi.testclient import TestClient

from backend.app.main import app


def test_me_requires_authentication() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/me")
    assert response.status_code == 401
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "AUTH_REQUIRED"
    assert "trace_id" in body["meta"]


def test_logout_uses_response_envelope() -> None:
    client = TestClient(app)
    response = client.post("/api/v1/auth/logout")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["logged_out"] is True
    assert body["error"] is None
