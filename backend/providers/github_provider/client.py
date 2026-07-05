from __future__ import annotations

from typing import Any

import httpx

from backend.providers.github_provider.errors import GitHubProviderUnavailableError, GitHubRepositoryNotFoundError
from backend.providers.github_provider.schemas import GitHubRepository


class GitHubProviderClient:
    """GitHub API wrapper only. This class must not contain YGIT business logic."""

    provider = "github"
    api_base_url = "https://api.github.com"

    def __init__(self, *, timeout_seconds: float = 10.0) -> None:
        self.timeout_seconds = timeout_seconds

    async def validate_account(self, token_ref: str) -> dict[str, str]:
        if not token_ref:
            return {"provider": self.provider, "status": "invalid"}
        return {"provider": self.provider, "status": "validated", "account_name": "github-account"}

    async def get_repository_metadata(
        self,
        *,
        owner: str,
        repo: str,
        token_ref: str | None = None,
    ) -> GitHubRepository:
        headers = {"Accept": "application/vnd.github+json", "User-Agent": "YGIT"}
        # token_ref is intentionally not dereferenced by the provider. Token resolution belongs to Connected Accounts.
        url = f"{self.api_base_url}/repos/{owner}/{repo}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds, headers=headers) as client:
                response = await client.get(url)
        except httpx.HTTPError as exc:
            raise GitHubProviderUnavailableError("GitHub API request failed.") from exc

        if response.status_code == 404:
            raise GitHubRepositoryNotFoundError("GitHub repository was not found.")
        if response.status_code >= 400:
            raise GitHubProviderUnavailableError("GitHub API returned an error.")

        payload: dict[str, Any] = response.json()
        owner_login = str(payload.get("owner", {}).get("login") or owner)
        name = str(payload.get("name") or repo)
        visibility = "private" if payload.get("private") else "public"
        default_branch = payload.get("default_branch")
        pushed_at = payload.get("pushed_at")
        return GitHubRepository(
            repository_url=f"https://github.com/{owner_login}/{name}",
            owner=owner_login,
            name=name,
            default_branch=default_branch,
            visibility=visibility,
            latest_commit_sha=None,
            file_tree_snapshot={"default_branch": default_branch} if default_branch else None,
            metadata={
                "id": payload.get("id"),
                "full_name": payload.get("full_name"),
                "html_url": payload.get("html_url"),
                "description": payload.get("description"),
                "pushed_at": pushed_at,
                "archived": payload.get("archived"),
                "disabled": payload.get("disabled"),
            },
        )
