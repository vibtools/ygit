from __future__ import annotations

import ast
from pathlib import Path

DEPLOY_ENGINE = Path("backend/engines/deploy_engine")
API_ROUTES = Path("backend/app/routes")
WORKER_JOBS = Path("backend/workers/jobs")
DEPLOY_PIPELINE = Path("backend/pipelines/deploy_pipeline")

PROVIDER_PREFIXES = (
    "backend.providers.github_provider",
    "backend.providers.cloudflare_provider",
)


def _imports(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(), filename=str(path))
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            modules.append(node.module)
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
    return modules


def test_deploy_engine_does_not_import_provider_layer() -> None:
    for path in DEPLOY_ENGINE.rglob("*.py"):
        for module in _imports(path):
            assert not module.startswith(PROVIDER_PREFIXES), f"{path} imports {module}"


def test_api_routes_do_not_import_deploy_pipeline() -> None:
    for path in API_ROUTES.rglob("*.py"):
        for module in _imports(path):
            assert not module.startswith("backend.pipelines.deploy_pipeline"), f"{path} imports {module}"


def test_worker_jobs_import_pipeline_not_providers() -> None:
    for path in [WORKER_JOBS / "deploy_project.py", WORKER_JOBS / "redeploy_project.py"]:
        imports = _imports(path)
        assert "backend.pipelines.deploy_pipeline.public" in imports
        for module in imports:
            assert not module.startswith(PROVIDER_PREFIXES), f"{path} imports {module}"


def test_deploy_pipeline_has_history_contract_module() -> None:
    assert (DEPLOY_PIPELINE / "internal" / "history_contract.py").exists()
