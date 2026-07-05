from __future__ import annotations

import re
from urllib.parse import urlparse

from backend.engines.repository_engine.errors import RepositoryProviderUnsupportedError, RepositoryUrlInvalidError
from backend.engines.repository_engine.schemas import ParsedRepositoryUrl

_GITHUB_PATH_RE = re.compile(r"^(?P<owner>[A-Za-z0-9_.-]+)/(?P<repo>[A-Za-z0-9_.-]+?)(?:\.git)?/?$")
_GITHUB_SSH_RE = re.compile(r"^git@github\.com:(?P<owner>[A-Za-z0-9_.-]+)/(?P<repo>[A-Za-z0-9_.-]+?)(?:\.git)?$")


def _clean_repo_name(repo: str) -> str:
    return repo[:-4] if repo.endswith(".git") else repo


def parse_github_repository_url(repository_url: str) -> ParsedRepositoryUrl:
    value = repository_url.strip()
    if not value:
        raise RepositoryUrlInvalidError()

    ssh_match = _GITHUB_SSH_RE.match(value)
    if ssh_match:
        owner = ssh_match.group("owner")
        repo = _clean_repo_name(ssh_match.group("repo"))
        return ParsedRepositoryUrl(
            provider="github",
            owner=owner,
            repo=repo,
            normalized_url=f"https://github.com/{owner}/{repo}",
        )

    parsed = urlparse(value)
    if parsed.scheme not in {"https", "http"}:
        raise RepositoryUrlInvalidError()
    host = parsed.netloc.lower()
    if host != "github.com":
        if "github" in host:
            raise RepositoryProviderUnsupportedError()
        raise RepositoryProviderUnsupportedError()

    path = parsed.path.strip("/")
    match = _GITHUB_PATH_RE.match(path)
    if not match:
        raise RepositoryUrlInvalidError()

    owner = match.group("owner")
    repo = _clean_repo_name(match.group("repo"))
    if not owner or not repo or owner in {".", ".."} or repo in {".", ".."}:
        raise RepositoryUrlInvalidError()

    return ParsedRepositoryUrl(
        provider="github",
        owner=owner,
        repo=repo,
        normalized_url=f"https://github.com/{owner}/{repo}",
    )
