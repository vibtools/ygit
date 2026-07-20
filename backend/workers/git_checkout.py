from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

_GITHUB_HOSTS = {"github.com", "www.github.com"}
_REF_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,255}$")


class WorkerGitCheckoutError(RuntimeError):
    """Raised when a worker checkout request is unsafe or fails."""


@dataclass(frozen=True)
class GitCheckoutRequest:
    repository_url: str
    destination_path: Path
    ref: str | None = None
    timeout_seconds: int = 180


@dataclass(frozen=True)
class GitCheckoutResult:
    repository_url: str
    destination_path: Path
    ref: str | None
    commit_sha: str | None


def validate_github_repository_url(repository_url: str) -> str:
    """Validate a public GitHub HTTPS repository URL.

    App-token/private checkout will be added later through provider boundaries.
    This utility intentionally rejects embedded credentials, query strings,
    fragments, SSH syntax, and non-GitHub hosts.
    """

    value = str(repository_url or "").strip()
    parsed = urlparse(value)

    if parsed.scheme != "https":
        raise WorkerGitCheckoutError("Repository checkout requires an HTTPS GitHub URL.")
    if parsed.hostname not in _GITHUB_HOSTS:
        raise WorkerGitCheckoutError("Repository checkout currently supports GitHub repositories only.")
    if parsed.username or parsed.password:
        raise WorkerGitCheckoutError("Repository URL must not include embedded credentials.")
    if parsed.query or parsed.fragment:
        raise WorkerGitCheckoutError("Repository URL must not include query strings or fragments.")

    path_parts = [part for part in parsed.path.strip("/").split("/") if part]
    if len(path_parts) != 2:
        raise WorkerGitCheckoutError("Repository URL must include owner and repository name.")

    owner, repo = path_parts
    if not owner or not repo:
        raise WorkerGitCheckoutError("Repository URL must include owner and repository name.")

    return value


def validate_git_ref(ref: str | None) -> str | None:
    if ref is None:
        return None

    value = str(ref).strip()
    if not value:
        return None

    unsafe = (
        ".." in value
        or "//" in value
        or "\\" in value
        or value.startswith(("/", "-", "."))
        or value.endswith(("/", ".", ".lock"))
        or "@{" in value
        or not _REF_PATTERN.fullmatch(value)
    )
    if unsafe:
        raise WorkerGitCheckoutError("Git ref is unsafe for worker checkout.")

    return value


def ensure_checkout_destination(destination_path: Path) -> Path:
    destination = Path(destination_path).expanduser().resolve()

    if destination.exists() and any(destination.iterdir()):
        raise WorkerGitCheckoutError("Checkout destination must be empty.")

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.mkdir(parents=True, exist_ok=True)
    return destination


def run_git_checkout(request: GitCheckoutRequest) -> GitCheckoutResult:
    """Run a safe non-shell git checkout into a worker-owned destination."""

    repository_url = validate_github_repository_url(request.repository_url)
    ref = validate_git_ref(request.ref)
    destination = ensure_checkout_destination(request.destination_path)

    command = ["git", "clone", "--depth", "1", "--no-tags"]
    if ref:
        command.extend(["--branch", ref])
    command.extend(["--", repository_url, str(destination)])

    checkout = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=request.timeout_seconds,
        shell=False,
    )
    if checkout.returncode != 0:
        raise WorkerGitCheckoutError("Git checkout failed.")

    revision = subprocess.run(
        ["git", "-C", str(destination), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        timeout=30,
        shell=False,
    )

    commit_sha = revision.stdout.strip() if revision.returncode == 0 and revision.stdout.strip() else None

    return GitCheckoutResult(
        repository_url=repository_url,
        destination_path=destination,
        ref=ref,
        commit_sha=commit_sha,
    )
