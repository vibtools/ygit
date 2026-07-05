from fastapi.testclient import TestClient

from backend.app.main import app


def test_project_deploy_requires_authentication() -> None:
    client = TestClient(app)
    response = client.post("/api/v1/projects/proj_1/deploy", json={})
    assert response.status_code == 401
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "AUTH_REQUIRED"


def test_get_deployment_requires_authentication() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/deployments/dep_1")
    assert response.status_code == 401
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "AUTH_REQUIRED"


def test_redeploy_requires_authentication() -> None:
    client = TestClient(app)
    response = client.post("/api/v1/deployments/dep_1/redeploy", json={})
    assert response.status_code == 401
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "AUTH_REQUIRED"


def test_cancel_deployment_requires_authentication() -> None:
    client = TestClient(app)
    response = client.post("/api/v1/deployments/dep_1/cancel")
    assert response.status_code == 401
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "AUTH_REQUIRED"
