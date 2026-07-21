from __future__ import annotations

import httpx
import pytest

from backend.providers.cloudflare_provider import (
    client as cloudflare_client_module,
)
from backend.providers.cloudflare_provider.client import (
    CloudflareProviderClient,
)
from backend.providers.cloudflare_provider.errors import (
    CloudflareOAuthRefreshError,
    CloudflareProviderUnavailableError,
)


class FakeResponse:
    def __init__(
        self,
        *,
        status_code: int,
        payload: dict[str, object],
    ) -> None:
        self.status_code = status_code
        self._payload = payload

    def json(self) -> dict[str, object]:
        return self._payload


@pytest.mark.asyncio
async def test_refresh_oauth_token_posts_refresh_grant(
    monkeypatch,
) -> None:
    captured: dict[str, object] = {}

    class SuccessClient:
        def __init__(
            self,
            *,
            timeout: float,
        ) -> None:
            captured["timeout"] = timeout

        async def __aenter__(
            self,
        ) -> "SuccessClient":
            return self

        async def __aexit__(
            self,
            exc_type,
            exc,
            traceback,
        ) -> None:
            return None

        async def post(
            self,
            url: str,
            *,
            data: dict[str, str],
        ) -> FakeResponse:
            captured["url"] = url
            captured["data"] = dict(data)

            return FakeResponse(
                status_code=200,
                payload={
                    "access_token": (
                        "new-access-value-for-test"
                    ),
                    "refresh_token": (
                        "new-refresh-value-for-test"
                    ),
                    "token_type": "bearer",
                    "expires_in": 3600,
                    "scope": (
                        "account.read page.write"
                    ),
                },
            )

    monkeypatch.setattr(
        cloudflare_client_module.httpx,
        "AsyncClient",
        SuccessClient,
    )

    provider = CloudflareProviderClient(
        token_url=(
            "https://dash.cloudflare.com/"
            "oauth2/token"
        ),
        timeout_seconds=7.5,
    )

    result = await provider.refresh_oauth_token(
        refresh_value=(
            "refresh-value-for-test"
        ),
        client_id="client-id",
        client_secret=(
            "client-secret-value-for-test"
        ),
    )

    assert captured["timeout"] == 7.5
    assert captured["url"] == (
        "https://dash.cloudflare.com/"
        "oauth2/token"
    )
    assert captured["data"] == {
        "grant_type": "refresh_token",
        "refresh_token": (
            "refresh-value-for-test"
        ),
        "client_id": "client-id",
        "client_secret": (
            "client-secret-value-for-test"
        ),
    }
    assert result.access_token == (
        "new-access-value-for-test"
    )
    assert result.refresh_token == (
        "new-refresh-value-for-test"
    )
    assert result.expires_in == 3600


@pytest.mark.asyncio
async def test_refresh_oauth_token_rejects_missing_refresh_value() -> None:
    provider = CloudflareProviderClient()

    with pytest.raises(
        CloudflareOAuthRefreshError
    ):
        await provider.refresh_oauth_token(
            refresh_value="",
            client_id="client-id",
            client_secret=(
                "client-secret-value-for-test"
            ),
        )


@pytest.mark.asyncio
async def test_refresh_oauth_token_maps_transport_failure(
    monkeypatch,
) -> None:
    class FailingClient:
        def __init__(
            self,
            *,
            timeout: float,
        ) -> None:
            self.timeout = timeout

        async def __aenter__(
            self,
        ) -> "FailingClient":
            return self

        async def __aexit__(
            self,
            exc_type,
            exc,
            traceback,
        ) -> None:
            return None

        async def post(
            self,
            url: str,
            *,
            data: dict[str, str],
        ) -> FakeResponse:
            request = httpx.Request(
                "POST",
                url,
            )
            raise httpx.ConnectError(
                "provider unavailable",
                request=request,
            )

    monkeypatch.setattr(
        cloudflare_client_module.httpx,
        "AsyncClient",
        FailingClient,
    )

    provider = CloudflareProviderClient()

    with pytest.raises(
        CloudflareProviderUnavailableError
    ):
        await provider.refresh_oauth_token(
            refresh_value=(
                "refresh-value-for-test"
            ),
            client_id="client-id",
            client_secret=(
                "client-secret-value-for-test"
            ),
        )


@pytest.mark.asyncio
async def test_refresh_oauth_token_rejects_provider_error(
    monkeypatch,
) -> None:
    class RejectedClient:
        def __init__(
            self,
            *,
            timeout: float,
        ) -> None:
            self.timeout = timeout

        async def __aenter__(
            self,
        ) -> "RejectedClient":
            return self

        async def __aexit__(
            self,
            exc_type,
            exc,
            traceback,
        ) -> None:
            return None

        async def post(
            self,
            url: str,
            *,
            data: dict[str, str],
        ) -> FakeResponse:
            return FakeResponse(
                status_code=400,
                payload={
                    "error": "invalid_grant",
                },
            )

    monkeypatch.setattr(
        cloudflare_client_module.httpx,
        "AsyncClient",
        RejectedClient,
    )

    provider = CloudflareProviderClient()

    with pytest.raises(
        CloudflareOAuthRefreshError
    ):
        await provider.refresh_oauth_token(
            refresh_value=(
                "refresh-value-for-test"
            ),
            client_id="client-id",
            client_secret=(
                "client-secret-value-for-test"
            ),
        )
