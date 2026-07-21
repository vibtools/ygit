from __future__ import annotations

from urllib.parse import quote, urlencode

import httpx

from backend.providers.cloudflare_provider.errors import (
    CloudflareAccountValidationError,
    CloudflareOAuthConfigurationError,
    CloudflareOAuthExchangeError,
    CloudflareOAuthRefreshError,
    CloudflarePagesProjectError,
    CloudflareProviderUnavailableError,
)
from backend.providers.cloudflare_provider.schemas import (
    CloudflareAccount,
    CloudflareAccountValidation,
    CloudflareOAuthResponse,
    CloudflarePagesProject,
)


class CloudflareProviderClient:
    def __init__(
        self,
        *,
        authorization_url: str = "https://dash.cloudflare.com/oauth2/auth",
        token_url: str = "https://dash.cloudflare.com/oauth2/token",
        api_base_url: str = "https://api.cloudflare.com/client/v4",
        timeout_seconds: float = 10.0,
    ) -> None:
        self.authorization_url = authorization_url
        self.token_url = token_url
        self.api_base_url = api_base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    @staticmethod
    def _normalize_oauth_scope_string(scopes: str) -> str:
        if not scopes:
            return ""

        normalized = str(scopes).strip()
        normalized = normalized.replace('\\"', '"').replace("\\'", "'")
        parts = [
            part.strip().strip("\\\"'")
            for part in normalized.split()
        ]
        return " ".join(part for part in parts if part)

    def build_oauth_authorization_url(
        self,
        *,
        client_id: str,
        redirect_uri: str,
        scopes: str,
        state: str,
    ) -> str:
        if not client_id:
            raise CloudflareOAuthConfigurationError("Cloudflare OAuth client ID is missing.")
        if not redirect_uri:
            raise CloudflareOAuthConfigurationError("Cloudflare OAuth redirect URI is missing.")
        if not state:
            raise CloudflareOAuthConfigurationError("Cloudflare OAuth state is missing.")

        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "state": state,
        }

        normalized_scopes = self._normalize_oauth_scope_string(scopes)
        if normalized_scopes:
            params["scope"] = normalized_scopes

        return f"{self.authorization_url}?{urlencode(params)}"

    async def exchange_oauth_code(
        self,
        *,
        code_value: str,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
    ) -> CloudflareOAuthResponse:
        if not code_value:
            raise CloudflareOAuthExchangeError("Cloudflare OAuth code is missing.")
        if not client_id or not client_secret:
            raise CloudflareOAuthConfigurationError("Cloudflare OAuth credentials are missing.")

        form_data = {
            "grant_type": "authorization_code",
            "code": code_value,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(self.token_url, data=form_data)
        except httpx.HTTPError as exc:
            raise CloudflareProviderUnavailableError("Cloudflare OAuth token endpoint is unavailable.") from exc

        if response.status_code >= 400:
            raise CloudflareOAuthExchangeError("Cloudflare OAuth token exchange failed.")

        return CloudflareOAuthResponse.model_validate(response.json())

    async def refresh_oauth_token(
        self,
        *,
        refresh_value: str,
        client_id: str,
        client_secret: str,
    ) -> CloudflareOAuthResponse:
        normalized_refresh = refresh_value.strip()

        if not normalized_refresh:
            raise CloudflareOAuthRefreshError(
                "Cloudflare OAuth refresh value is missing."
            )

        if not client_id or not client_secret:
            raise CloudflareOAuthConfigurationError(
                "Cloudflare OAuth credentials are missing."
            )

        form_data = {
            "grant_type": "refresh_token",
            "refresh_token": normalized_refresh,
            "client_id": client_id,
            "client_secret": client_secret,
        }

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout_seconds
            ) as client:
                response = await client.post(
                    self.token_url,
                    data=form_data,
                )
        except httpx.HTTPError as exc:
            raise CloudflareProviderUnavailableError(
                "Cloudflare OAuth token endpoint is unavailable."
            ) from exc

        if response.status_code >= 400:
            raise CloudflareOAuthRefreshError(
                "Cloudflare OAuth refresh failed."
            )

        try:
            payload = response.json()
            return CloudflareOAuthResponse.model_validate(
                payload
            )
        except (TypeError, ValueError) as exc:
            raise CloudflareOAuthRefreshError(
                "Cloudflare OAuth refresh returned an invalid response."
            ) from exc

    @staticmethod
    def _required_pages_value(
        value: str,
        *,
        label: str,
    ) -> str:
        normalized = str(value or "").strip()

        if (
            not normalized
            or any(
                character in normalized
                for character in ("\x00", "\r", "\n")
            )
        ):
            raise CloudflarePagesProjectError(
                f"Cloudflare Pages {label} is invalid."
            )

        return normalized

    @staticmethod
    def _pages_project_from_payload(
        payload: object,
    ) -> CloudflarePagesProject:
        if not isinstance(payload, dict):
            raise CloudflarePagesProjectError(
                "Cloudflare Pages returned an invalid response."
            )

        result = payload.get("result")

        if (
            payload.get("success") is not True
            or not isinstance(result, dict)
        ):
            raise CloudflarePagesProjectError(
                "Cloudflare Pages returned an invalid response."
            )

        project_data = {
            "project_id": str(result.get("id") or "").strip(),
            "project_name": str(result.get("name") or "").strip(),
            "production_branch": str(
                result.get("production_branch") or ""
            ).strip(),
            "subdomain": (
                str(result.get("subdomain")).strip()
                if result.get("subdomain")
                else None
            ),
        }

        if (
            not project_data["project_id"]
            or not project_data["project_name"]
            or not project_data["production_branch"]
        ):
            raise CloudflarePagesProjectError(
                "Cloudflare Pages returned incomplete project data."
            )

        try:
            return CloudflarePagesProject.model_validate(project_data)
        except (TypeError, ValueError) as exc:
            raise CloudflarePagesProjectError(
                "Cloudflare Pages returned invalid project data."
            ) from exc

    async def get_pages_project(
        self,
        *,
        account_id: str,
        project_name: str,
        bearer_value: str,
    ) -> CloudflarePagesProject | None:
        account_value = self._required_pages_value(
            account_id,
            label="account identifier",
        )
        project_value = self._required_pages_value(
            project_name,
            label="project name",
        )
        access_value = self._required_pages_value(
            bearer_value,
            label="access credential",
        )

        url = (
            f"{self.api_base_url}/accounts/"
            f"{quote(account_value, safe='')}/pages/projects/"
            f"{quote(project_value, safe='')}"
        )
        headers = {
            "Authorization": f"Bearer {access_value}",
        }

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout_seconds,
                headers=headers,
            ) as client:
                response = await client.get(url)
        except httpx.HTTPError as exc:
            raise CloudflareProviderUnavailableError(
                "Cloudflare Pages project API is unavailable."
            ) from exc

        if response.status_code == 404:
            return None

        if response.status_code >= 400:
            raise CloudflarePagesProjectError(
                "Cloudflare Pages project lookup failed."
            )

        try:
            payload = response.json()
        except (TypeError, ValueError) as exc:
            raise CloudflarePagesProjectError(
                "Cloudflare Pages returned an invalid response."
            ) from exc

        return self._pages_project_from_payload(payload)

    async def create_pages_project(
        self,
        *,
        account_id: str,
        project_name: str,
        production_branch: str,
        bearer_value: str,
    ) -> CloudflarePagesProject:
        account_value = self._required_pages_value(
            account_id,
            label="account identifier",
        )
        project_value = self._required_pages_value(
            project_name,
            label="project name",
        )
        branch_value = self._required_pages_value(
            production_branch,
            label="production branch",
        )
        access_value = self._required_pages_value(
            bearer_value,
            label="access credential",
        )

        url = (
            f"{self.api_base_url}/accounts/"
            f"{quote(account_value, safe='')}/pages/projects"
        )
        headers = {
            "Authorization": f"Bearer {access_value}",
        }
        body = {
            "name": project_value,
            "production_branch": branch_value,
        }

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout_seconds,
                headers=headers,
            ) as client:
                response = await client.post(url, json=body)
        except httpx.HTTPError as exc:
            raise CloudflareProviderUnavailableError(
                "Cloudflare Pages project API is unavailable."
            ) from exc

        if response.status_code >= 400:
            raise CloudflarePagesProjectError(
                "Cloudflare Pages project creation failed."
            )

        try:
            payload = response.json()
        except (TypeError, ValueError) as exc:
            raise CloudflarePagesProjectError(
                "Cloudflare Pages returned an invalid response."
            ) from exc

        return self._pages_project_from_payload(payload)

    async def ensure_pages_project(
        self,
        *,
        account_id: str,
        project_name: str,
        production_branch: str,
        bearer_value: str,
    ) -> CloudflarePagesProject:
        existing = await self.get_pages_project(
            account_id=account_id,
            project_name=project_name,
            bearer_value=bearer_value,
        )

        if existing is not None:
            return existing

        return await self.create_pages_project(
            account_id=account_id,
            project_name=project_name,
            production_branch=production_branch,
            bearer_value=bearer_value,
        )

    async def list_accounts(self, bearer_value: str) -> list[CloudflareAccount]:
        if not bearer_value:
            raise CloudflareAccountValidationError("Cloudflare bearer value is missing.")

        headers = {"Authorization": f"Bearer {bearer_value}"}
        url = f"{self.api_base_url}/accounts"

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds, headers=headers) as client:
                response = await client.get(url)
        except httpx.HTTPError as exc:
            raise CloudflareProviderUnavailableError("Cloudflare accounts API is unavailable.") from exc

        if response.status_code >= 400:
            raise CloudflareAccountValidationError("Cloudflare account validation failed.")

        payload = response.json()
        accounts = payload.get("result") or []
        return [
            CloudflareAccount(
                account_id=str(item.get("id") or ""),
                account_name=str(item.get("name") or "Cloudflare Account"),
            )
            for item in accounts
            if item.get("id")
        ]

    async def validate_oauth_access(
        self,
        *,
        bearer_value: str,
        scopes: list[str] | None = None,
    ) -> CloudflareAccountValidation:
        accounts = await self.list_accounts(bearer_value)
        if not accounts:
            raise CloudflareAccountValidationError("No Cloudflare accounts are available.")

        account = accounts[0]
        return CloudflareAccountValidation(
            account_id=account.account_id,
            account_name=account.account_name,
            scopes=scopes or [],
        )

    async def validate_account(self, token_ref: str) -> dict[str, str]:
        if not token_ref:
            raise CloudflareAccountValidationError("Cloudflare token reference is missing.")
        return {
            "provider_account_id": "cloudflare-account-placeholder",
            "provider_account_name": "Cloudflare Account",
        }
