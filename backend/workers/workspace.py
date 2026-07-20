from __future__ import annotations

import os
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

_DEFAULT_WORKSPACE_ROOT = ".ygit/workspaces"
_DEPLOYMENT_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")


class WorkerWorkspaceError(ValueError):
    """Raised when a worker workspace path cannot be safely resolved."""


@dataclass(frozen=True)
class RepositoryWorkspace:
    """Worker-owned filesystem contract for one deployment checkout."""

    deployment_id: str
    workspace_path: Path
    repository_path: Path
    artifacts_path: Path

    def as_build_payload(self) -> dict[str, str]:
        """Return the payload fragment needed by the worker build handoff."""

        return {"repository_path": str(self.repository_path)}


def resolve_workspace_root(root: str | Path | None = None) -> Path:
    """Resolve the configured worker workspace root.

    The default is intentionally local and provider-neutral. Deployment checkout
    and cleanup will remain worker-owned.
    """

    configured = root if root is not None else os.getenv("YGIT_WORKSPACE_ROOT", _DEFAULT_WORKSPACE_ROOT)
    return Path(configured).expanduser().resolve()


def _validate_deployment_id(deployment_id: str) -> str:
    text = str(deployment_id or "").strip()
    if not _DEPLOYMENT_ID_PATTERN.fullmatch(text) or ".." in text:
        raise WorkerWorkspaceError("Invalid deployment id for worker workspace.")
    return text


def _is_relative_to(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
    except ValueError:
        return False
    return True


def get_repository_workspace(
    deployment_id: str,
    *,
    root: str | Path | None = None,
) -> RepositoryWorkspace:
    """Return deterministic workspace paths without creating directories."""

    workspace_root = resolve_workspace_root(root)
    deployment_key = _validate_deployment_id(deployment_id)
    deployment_workspace = (workspace_root / deployment_key).resolve()

    if deployment_workspace == workspace_root or not _is_relative_to(deployment_workspace, workspace_root):
        raise WorkerWorkspaceError("Resolved deployment workspace escaped the workspace root.")

    return RepositoryWorkspace(
        deployment_id=deployment_key,
        workspace_path=deployment_workspace,
        repository_path=deployment_workspace / "repository",
        artifacts_path=deployment_workspace / "artifacts",
    )


def prepare_repository_workspace(
    deployment_id: str,
    *,
    root: str | Path | None = None,
) -> RepositoryWorkspace:
    """Create the worker workspace directories for a deployment."""

    workspace = get_repository_workspace(deployment_id, root=root)
    workspace.repository_path.mkdir(parents=True, exist_ok=True)
    workspace.artifacts_path.mkdir(parents=True, exist_ok=True)
    return workspace


def cleanup_repository_workspace(
    deployment_id: str,
    *,
    root: str | Path | None = None,
) -> None:
    """Delete only the resolved workspace for one deployment."""

    workspace_root = resolve_workspace_root(root)
    workspace = get_repository_workspace(deployment_id, root=workspace_root)
    target = workspace.workspace_path.resolve()

    if target == workspace_root or not _is_relative_to(target, workspace_root):
        raise WorkerWorkspaceError("Refusing to clean a path outside the workspace root.")

    if target.exists():
        shutil.rmtree(target)
