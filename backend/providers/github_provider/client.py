from __future__ import annotations

import time
from typing import Any
from urllib.parse import urlencode

import httpx
import jwt

from backend.providers.github_provider.errors import (
    GitHubAppAuthenticationError,
    GitHubAppConfigurationError,
    GitHubInstallationValidationError,
    GitHubProviderUnavailableError,
    GitHubRepositoryNotFoundError,
)
from backend.providers.github_provider.schemas import (
    GitHubAppInstallation,
    GitHubInstallationAccessToken,
    GitHubRepository,
)


class GitHubProviderClient:
    """GitHub API wrapper only. This class must not contain YGIT business logic."""

    provider = "github"

    def __init__(
        self,
        *,
        timeout_seconds: float = 10.0,
        api_base_url: str = "https://api.github.com",
    ) -> None:
        self.timeout_seconds = timeout_seconds
        self.api_base_url = api_base_url.rstrip("/")

    def build_app_installation_url(self, *, install_url: str, state: str) -> str:
        if not install_url:
            raise GitHubAppConfigurationError("GitHub App install URL is not configured.")
        if not state:
            raise GitHubAppConfigurationError("GitHub App installation state is missing.")
        separator = "&" if "?" in install_url else "?"
        return f"{install_url}{separator}{urlencode({'state': state})}"

    def create_app_jwt(self, *, app_id: str, private_key_pem: str) -> str:
        if not app_id.strip():
            raise GitHubAppConfigurationError("GitHub App ID is not configured.")
        if not private_key_pem.strip():
            raise GitHubAppConfigurationError("GitHub App private key is not configured.")

        issued_at = int(time.time()) - 60
        expires_at = issued_at + 540
        payload = {
            "iat": issued_at,
            "exp": expires_at,
            "iss": app_id.strip(),
        }

        try:
            token = jwt.encode(payload, private_key_pem, algorithm="RS256")
        except Exception as exc:
            raise GitHubAppAuthenticationError("GitHub App JWT generation failed.") from exc

        if isinstance(token, bytes):
            return token.decode("utf-8")
        return str(token)

    async def get_app_installation(
        self,
        *,
        installation_id: int | str,
        app_jwt: str,
    ) -> GitHubAppInstallation:
        if not app_jwt:
            raise GitHubAppAuthenticationError("GitHub App JWT is missing.")

        url = f"{self.api_base_url}/app/installations/{installation_id}"
        headers = self._app_headers(app_jwt)

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds, headers=headers) as client:
                response = await client.get(url)
        except httpx.HTTPError as exc:
            raise GitHubProviderUnavailableError("GitHub installation validation request failed.") from exc

        if response.status_code == 404:
            raise GitHubInstallationValidationError("GitHub App installation was not found.")
        if response.status_code >= 400:
            raise GitHubInstallationValidationError("GitHub App installation validation failed.")

        payload: dict[str, Any] = response.json()
        return self._installation_from_payload(payload)

    async def create_installation_access_token(
        self,
        *,
        installation_id: int | str,
        app_jwt: str,
    ) -> GitHubInstallationAccessToken:
        if not app_jwt:
            raise GitHubAppAuthenticationError("GitHub App JWT is missing.")

        url = f"{self.api_base_url}/app/installations/{installation_id}/access_tokens"
        headers = self._app_headers(app_jwt)

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds, headers=headers) as client:
                response = await client.post(url)
        except httpx.HTTPError as exc:
            raise GitHubProviderUnavailableError("GitHub installation token request failed.") from exc

        if response.status_code >= 400:
            raise GitHubInstallationValidationError("GitHub installation token request failed.")

        payload: dict[str, Any] = response.json()
        token = str(payload.get("token") or "")
        expires_at = str(payload.get("expires_at") or "")

        if not token or not expires_at:
            raise GitHubInstallationValidationError("GitHub installation token response was invalid.")

        return GitHubInstallationAccessToken(
            token=token,
            expires_at=expires_at,
            permissions=payload.get("permissions"),
            repository_selection=payload.get("repository_selection"),
        )

    async def delete_app_installation(
        self,
        *,
        installation_id: int | str,
        app_jwt: str,
    ) -> None:
        if not app_jwt:
            raise GitHubAppAuthenticationError("GitHub App JWT is missing.")

        url = f"{self.api_base_url}/app/installations/{installation_id}"
        headers = self._app_headers(app_jwt)

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds, headers=headers) as client:
                response = await client.delete(url)
        except httpx.HTTPError as exc:
            raise GitHubProviderUnavailableError("GitHub App installation uninstall request failed.") from exc

        if response.status_code in {204, 404}:
            return
        if response.status_code >= 400:
            raise GitHubInstallationValidationError("GitHub App installation uninstall failed.")


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

    def _app_headers(self, app_jwt: str) -> dict[str, str]:
        return {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {app_jwt}",
            "User-Agent": "YGIT",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def _installation_from_payload(self, payload: dict[str, Any]) -> GitHubAppInstallation:
        raw_id = payload.get("id")
        if raw_id is None:
            raise GitHubInstallationValidationError("GitHub installation payload is missing id.")

        account = payload.get("account") or {}
        account_login = str(account.get("login") or account.get("slug") or "")
        account_id = str(account.get("id") or "")

        if not account_login or not account_id:
            raise GitHubInstallationValidationError("GitHub installation payload is missing account metadata.")

        return GitHubAppInstallation(
            installation_id=int(raw_id),
            account_id=account_id,
            account_login=account_login,
            account_type=account.get("type"),
            target_type=payload.get("target_type"),
            repository_selection=payload.get("repository_selection"),
        )
