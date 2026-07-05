from fastapi.testclient import TestClient

from backend.app.main import app


def test_projects_require_authentication() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/projects")
    assert response.status_code == 401
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "AUTH_REQUIRED"
    assert "trace_id" in body["meta"]


def test_create_project_requires_authentication_before_db() -> None:
    client = TestClient(app)
    response = client.post("/api/v1/projects", json={"name": "Demo", "slug": "demo-site"})
    assert response.status_code == 401
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "AUTH_REQUIRED"
