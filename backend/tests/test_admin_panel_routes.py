from fastapi.testclient import TestClient

from backend.app.main import app


def test_admin_index_is_served() -> None:
    client = TestClient(app)
    response = client.get("/admin")
    assert response.status_code == 200
    assert "Platform Operations Console" in response.text
    assert "Project management stays in the user dashboard" in response.text


def test_admin_assets_are_served() -> None:
    client = TestClient(app)
    css_response = client.get("/admin/assets/styles.css")
    js_response = client.get("/admin/assets/app.js")
    assert css_response.status_code == 200
    assert "--primary: #2563eb" in css_response.text
    assert js_response.status_code == 200
    assert "const API = \"/api/v1\"" in js_response.text


def test_admin_asset_path_traversal_is_blocked() -> None:
    client = TestClient(app)
    response = client.get("/admin/assets/../index.html")
    assert response.status_code == 404


def test_admin_api_requires_admin_authentication() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/admin/overview")
    assert response.status_code == 401
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "AUTH_REQUIRED"
