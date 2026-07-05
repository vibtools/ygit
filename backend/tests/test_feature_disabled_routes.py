from fastapi.testclient import TestClient
from backend.app.main import app


def test_project_routes_are_registered_and_require_authentication() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/projects")
    assert response.status_code == 401
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "AUTH_REQUIRED"
