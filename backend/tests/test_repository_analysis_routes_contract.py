from fastapi.testclient import TestClient

from backend.app.main import app


def test_repository_analysis_routes_require_authentication() -> None:
    client = TestClient(app)
    response = client.post("/api/v1/repository-analysis/quick", json={"repository_id": "repo_123"})
    assert response.status_code == 401
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "AUTH_REQUIRED"
    assert "trace_id" in body["meta"]


def test_repository_analysis_deep_route_requires_authentication_before_job_creation() -> None:
    client = TestClient(app)
    response = client.post("/api/v1/repository-analysis/deep", json={"repository_id": "repo_123"})
    assert response.status_code == 401
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "AUTH_REQUIRED"
