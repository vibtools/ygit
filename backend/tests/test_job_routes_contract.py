from fastapi.testclient import TestClient

from backend.app.main import app


def test_get_job_requires_authentication() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/jobs/job_1")
    assert response.status_code == 401
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "AUTH_REQUIRED"
