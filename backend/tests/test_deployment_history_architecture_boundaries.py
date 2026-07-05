from __future__ import annotations

import ast
from pathlib import Path

DEPLOYMENT_HISTORY_ENGINE = Path("backend/engines/deployment_history_engine")

FORBIDDEN_IMPORT_PREFIXES = (
    "backend.providers.github_provider",
    "backend.providers.cloudflare_provider",
    "backend.pipelines.deploy_pipeline.public",
    "backend.pipelines.deploy_pipeline.internal.service",
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


def test_deployment_history_engine_does_not_import_providers_or_pipeline_execution() -> None:
    for path in DEPLOYMENT_HISTORY_ENGINE.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        for module in _imports(path):
            assert not module.startswith(FORBIDDEN_IMPORT_PREFIXES), f"{path} imports {module}"


def test_deployment_history_engine_has_owned_tables_and_public_boundary() -> None:
    assert (DEPLOYMENT_HISTORY_ENGINE / "models.py").read_text().count("deployment_history") >= 1
    assert (DEPLOYMENT_HISTORY_ENGINE / "models.py").read_text().count("deployment_logs") >= 1
    assert (DEPLOYMENT_HISTORY_ENGINE / "public.py").exists()
