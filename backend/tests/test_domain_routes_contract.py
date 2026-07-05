from fastapi.testclient import TestClient

from backend.app.main import app


def test_domain_check_requires_authentication() -> None:
    client = TestClient(app)
    response = client.post("/api/v1/domains/check", json={"slug": "portfolio"})
    assert response.status_code == 401
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "AUTH_REQUIRED"


def test_project_domain_routes_require_authentication() -> None:
    client = TestClient(app)
    response = client.post("/api/v1/projects/proj_1/domain", json={"slug": "portfolio"})
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTH_REQUIRED"

    response = client.get("/api/v1/projects/proj_1/domain")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTH_REQUIRED"

    response = client.delete("/api/v1/projects/proj_1/domain")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTH_REQUIRED"
