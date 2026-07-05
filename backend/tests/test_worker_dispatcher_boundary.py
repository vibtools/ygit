from __future__ import annotations

import ast
from pathlib import Path

WORKER_JOBS = Path("backend/workers/jobs")
FORBIDDEN_PROVIDER_PREFIXES = (
    "backend.providers.github_provider",
    "backend.providers.cloudflare_provider",
)


def test_deploy_worker_jobs_do_not_import_providers() -> None:
    for path in [WORKER_JOBS / "deploy_project.py", WORKER_JOBS / "redeploy_project.py"]:
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert not node.module.startswith(FORBIDDEN_PROVIDER_PREFIXES)
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith(FORBIDDEN_PROVIDER_PREFIXES)
