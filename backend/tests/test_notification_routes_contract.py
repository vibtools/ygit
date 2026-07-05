from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app.main import app


def test_notifications_list_requires_authentication() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/notifications")
    assert response.status_code == 401
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "AUTH_REQUIRED"


def test_notifications_unread_count_requires_authentication() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/notifications/unread-count")
    assert response.status_code == 401
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "AUTH_REQUIRED"


def test_notifications_mark_read_requires_authentication() -> None:
    client = TestClient(app)
    response = client.patch("/api/v1/notifications/notif_1/read")
    assert response.status_code == 401
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "AUTH_REQUIRED"
