from __future__ import annotations

import ast
from pathlib import Path

DEPLOY_ENGINE = Path("backend/engines/deploy_engine")

FORBIDDEN_IMPORT_PREFIXES = (
    "backend.providers.github_provider",
    "backend.providers.cloudflare_provider",
)


def iter_python_files() -> list[Path]:
    return [path for path in DEPLOY_ENGINE.rglob("*.py") if "__pycache__" not in path.parts]


def test_deploy_engine_does_not_import_provider_layer() -> None:
    for path in iter_python_files():
        tree = ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert not node.module.startswith(FORBIDDEN_IMPORT_PREFIXES), f"{path} imports {node.module}"
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith(FORBIDDEN_IMPORT_PREFIXES), f"{path} imports {alias.name}"


def test_deploy_engine_boundary_mentions_pipeline() -> None:
    readme = (DEPLOY_ENGINE / "README.md").read_text(encoding='utf-8')
    assert "Deploy Pipeline" in readme
    assert "Deploy Engine → Cloudflare Provider" in readme
