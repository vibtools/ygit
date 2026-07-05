from fastapi.testclient import TestClient

from backend.app.main import app


def test_dashboard_index_is_served() -> None:
    client = TestClient(app)
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert "YGIT Dashboard" in response.text
    assert "Paste Repository" in response.text
    assert "/api/v1" not in response.url.path


def test_dashboard_assets_are_served() -> None:
    client = TestClient(app)
    css_response = client.get("/dashboard/assets/styles.css")
    js_response = client.get("/dashboard/assets/app.js")
    assert css_response.status_code == 200
    assert "--primary: #2563eb" in css_response.text
    assert js_response.status_code == 200
    assert "const API = \"/api/v1\"" in js_response.text


def test_dashboard_asset_path_traversal_is_blocked() -> None:
    client = TestClient(app)
    response = client.get("/dashboard/assets/../index.html")
    assert response.status_code == 404
