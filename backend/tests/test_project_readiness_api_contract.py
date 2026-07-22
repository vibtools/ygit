from pathlib import Path

ROUTES = Path("backend/app/routes/project_routes.py")
RELEASE_GATE = Path("scripts/release_gate.py")
SPEC = Path("DASHBOARD_PROJECT_READINESS_API_SPEC.md")


def test_project_readiness_route_is_registered() -> None:
    source = ROUTES.read_text(encoding="utf-8")
    assert '@router.get("/{project_id}/readiness")' in source


def test_project_readiness_route_uses_deploy_engine_authority() -> None:
    source = ROUTES.read_text(encoding="utf-8")
    assert "deploy_service.validate_deploy_ready(" in source
    assert '"readiness": result.model_dump(' in source
    assert 'mode="json"' in source


def test_project_readiness_route_is_read_only_boundary() -> None:
    source = ROUTES.read_text(encoding="utf-8")
    route = source.split(
        '@router.get("/{project_id}/readiness")',
        1,
    )[1].split(
        '@router.post("/{project_id}/deploy"',
        1,
    )[0]
    assert "validate_deploy_ready(" in route
    assert "request_deployment(" not in route
    assert "backend.providers" not in route
    assert "DeploymentRepository" not in route


def test_release_gate_requires_project_readiness_route() -> None:
    source = RELEASE_GATE.read_text(encoding="utf-8")
    assert '"/api/v1/projects/{project_id}/readiness"' in source


def test_readiness_spec_locks_engine_authority() -> None:
    source = SPEC.read_text(encoding="utf-8")
    assert "DeployEngineService.validate_deploy_ready" in source
    assert "This route is read-only." in source
    assert "later independent patches" in source
