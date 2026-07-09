from fastapi.testclient import TestClient

from backend.app.main import app


def test_admin_index_requires_authentication() -> None:
    client = TestClient(app)
    response = client.get("/admin")
    assert response.status_code == 401


def test_admin_assets_are_served() -> None:
    client = TestClient(app)
    css_response = client.get("/admin/assets/styles.css")
    js_response = client.get("/admin/assets/app.js")
    assert css_response.status_code == 200
    assert js_response.status_code == 200
    assert "text/css" in css_response.headers["content-type"]
    assert "javascript" in js_response.headers["content-type"]


def test_admin_asset_path_traversal_is_blocked() -> None:
    client = TestClient(app)
    response = client.get("/admin/assets/../index.html")
    assert response.status_code == 404


def test_admin_api_requires_admin_authentication() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/admin/overview")
    assert response.status_code == 401