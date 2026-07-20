from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from backend.workers.git_checkout import (
    GitCheckoutRequest,
    WorkerGitCheckoutError,
    run_git_checkout,
    validate_github_repository_url,
    validate_git_ref,
)


def test_validate_github_repository_url_accepts_clean_https_github_url() -> None:
    assert validate_github_repository_url("https://github.com/vibtools/ygit") == "https://github.com/vibtools/ygit"


@pytest.mark.parametrize(
    "repository_url",
    [
        "",
        "http://github.com/vibtools/ygit",
        "git@github.com:vibtools/ygit.git",
        "https://example.com/vibtools/ygit",
        "https://github.com/vibtools",
        "https://github.com/vibtools/ygit/issues",
        "https://user:secret@github.com/vibtools/ygit",
        "https://github.com/vibtools/ygit?x=1",
        "https://github.com/vibtools/ygit#main",
    ],
)
def test_validate_github_repository_url_rejects_unsafe_or_unsupported_urls(repository_url: str) -> None:
    with pytest.raises(WorkerGitCheckoutError):
        validate_github_repository_url(repository_url)


@pytest.mark.parametrize("ref", ["main", "feature/deploy", "release-1.0.0", "v1_2_3"])
def test_validate_git_ref_accepts_safe_refs(ref: str) -> None:
    assert validate_git_ref(ref) == ref


@pytest.mark.parametrize(
    "ref",
    [
        "../main",
        "-main",
        ".hidden",
        "feature//bad",
        "feature\\bad",
        "feature..bad",
        "refs/heads/main.lock",
        "main@{1}",
        "main;echo bad",
    ],
)
def test_validate_git_ref_rejects_unsafe_refs(ref: str) -> None:
    with pytest.raises(WorkerGitCheckoutError):
        validate_git_ref(ref)


def test_run_git_checkout_uses_non_shell_git_commands(tmp_path: Path, monkeypatch) -> None:
    calls = []

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        if "rev-parse" in command:
            return subprocess.CompletedProcess(command, 0, stdout="abc123\n", stderr="")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = run_git_checkout(
        GitCheckoutRequest(
            repository_url="https://github.com/vibtools/ygit",
            destination_path=tmp_path / "repo",
            ref="main",
            timeout_seconds=60,
        )
    )

    assert result.repository_url == "https://github.com/vibtools/ygit"
    assert result.destination_path == (tmp_path / "repo").resolve()
    assert result.ref == "main"
    assert result.commit_sha == "abc123"

    clone_command, clone_kwargs = calls[0]
    assert clone_command[:4] == ["git", "clone", "--depth", "1"]
    assert "--branch" in clone_command
    assert clone_kwargs["shell"] is False
    assert clone_kwargs["timeout"] == 60

    revision_command, revision_kwargs = calls[1]
    assert revision_command[:4] == ["git", "-C", str((tmp_path / "repo").resolve()), "rev-parse"]
    assert revision_kwargs["shell"] is False


def test_run_git_checkout_rejects_non_empty_destination(tmp_path: Path) -> None:
    destination = tmp_path / "repo"
    destination.mkdir()
    (destination / "existing.txt").write_text("already here", encoding="utf-8")

    with pytest.raises(WorkerGitCheckoutError, match="destination must be empty"):
        run_git_checkout(
            GitCheckoutRequest(
                repository_url="https://github.com/vibtools/ygit",
                destination_path=destination,
            )
        )


def test_worker_git_checkout_keeps_provider_and_route_boundaries() -> None:
    source = Path("backend/workers/git_checkout.py").read_text(encoding="utf-8")

    assert "shell=False" in source
    assert "backend.providers" not in source
    assert "backend.app.routes" not in source
    assert "github_provider" not in source
    assert "cloudflare_provider" not in source
    assert "access_token" not in source
