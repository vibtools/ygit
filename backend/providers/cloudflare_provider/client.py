from __future__ import annotations

from urllib.parse import urlencode

import httpx

from backend.providers.cloudflare_provider.errors import (
    CloudflareAccountValidationError,
    CloudflareOAuthConfigurationError,
    CloudflareOAuthExchangeError,
    CloudflareProviderUnavailableError,
)
from backend.providers.cloudflare_provider.schemas import (
    CloudflareAccount,
    CloudflareAccountValidation,
    CloudflareOAuthResponse,
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
            "scope": scopes,
            "state": state,
        }
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
