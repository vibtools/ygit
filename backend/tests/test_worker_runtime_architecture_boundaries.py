from __future__ import annotations

import ast
from pathlib import Path

WORKER_ROOT = Path("backend/workers")
WORKER_JOBS = WORKER_ROOT / "jobs"
API_ROUTES = Path("backend/app/routes")
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


def test_worker_runtime_does_not_import_providers_directly() -> None:
    for path in WORKER_ROOT.rglob("*.py"):
        for module in _imports(path):
            assert not module.startswith(PROVIDER_PREFIXES), f"{path} imports {module}"


def test_worker_jobs_never_import_engine_repositories() -> None:
    for path in WORKER_JOBS.rglob("*.py"):
        for module in _imports(path):
            assert ".repository" not in module or not module.startswith("backend.engines"), f"{path} imports {module}"


def test_api_routes_do_not_import_worker_internal_runtime() -> None:
    forbidden = (
        "backend.workers.runner",
        "backend.workers.jobs",
        "backend.workers.worker",
        "backend.workers.repository",
    )
    for path in API_ROUTES.rglob("*.py"):
        for module in _imports(path):
            assert not module.startswith(forbidden), f"{path} imports {module}"


def test_jobs_migration_exists() -> None:
    assert Path("backend/migrations/versions/0008_worker_runtime_jobs.py").exists()
