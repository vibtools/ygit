from __future__ import annotations

from backend.app.main import app


def test_deployment_history_routes_are_registered() -> None:
    paths = set(app.openapi().get('paths', {}).keys())
    assert "/api/v1/deployments/{deployment_id}/logs" in paths
    assert "/api/v1/projects/{project_id}/deployments" in paths
