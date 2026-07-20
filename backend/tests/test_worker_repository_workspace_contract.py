from __future__ import annotations

from pathlib import Path

import pytest

from backend.workers.workspace import (
    WorkerWorkspaceError,
    cleanup_repository_workspace,
    get_repository_workspace,
    prepare_repository_workspace,
    resolve_workspace_root,
)


def test_get_repository_workspace_resolves_paths_without_creating_directories(tmp_path: Path) -> None:
    workspace = get_repository_workspace("dep_123", root=tmp_path)

    assert workspace.deployment_id == "dep_123"
    assert workspace.workspace_path == (tmp_path / "dep_123").resolve()
    assert workspace.repository_path == workspace.workspace_path / "repository"
    assert workspace.artifacts_path == workspace.workspace_path / "artifacts"
    assert workspace.as_build_payload() == {"repository_path": str(workspace.repository_path)}
    assert not workspace.workspace_path.exists()


def test_prepare_repository_workspace_creates_repository_and_artifact_directories(tmp_path: Path) -> None:
    workspace = prepare_repository_workspace("dep_build_1", root=tmp_path)

    assert workspace.workspace_path.exists()
    assert workspace.repository_path.is_dir()
    assert workspace.artifacts_path.is_dir()
    assert workspace.repository_path.parent == workspace.workspace_path
    assert workspace.artifacts_path.parent == workspace.workspace_path


@pytest.mark.parametrize(
    "deployment_id",
    [
        "",
        ".hidden",
        "../escape",
        "dep/escape",
        "dep\\escape",
        "dep..escape",
        "dep:escape",
    ],
)
def test_repository_workspace_rejects_unsafe_deployment_ids(tmp_path: Path, deployment_id: str) -> None:
    with pytest.raises(WorkerWorkspaceError):
        get_repository_workspace(deployment_id, root=tmp_path)


def test_cleanup_repository_workspace_removes_only_selected_workspace(tmp_path: Path) -> None:
    workspace = prepare_repository_workspace("dep_cleanup", root=tmp_path)
    sibling_file = tmp_path / "sibling.txt"
    sibling_file.write_text("keep", encoding="utf-8")

    cleanup_repository_workspace("dep_cleanup", root=tmp_path)

    assert not workspace.workspace_path.exists()
    assert sibling_file.read_text(encoding="utf-8") == "keep"
    assert tmp_path.exists()


def test_resolve_workspace_root_supports_environment_configuration(tmp_path: Path, monkeypatch) -> None:
    configured_root = tmp_path / "configured-root"
    monkeypatch.setenv("YGIT_WORKSPACE_ROOT", str(configured_root))

    assert resolve_workspace_root() == configured_root.resolve()


def test_worker_workspace_contract_keeps_provider_and_process_boundaries() -> None:
    source = Path("backend/workers/workspace.py").read_text(encoding="utf-8")

    assert "backend.providers" not in source
    assert "github_provider" not in source
    assert "cloudflare_provider" not in source
    assert "subprocess" not in source
    assert "requests" not in source
