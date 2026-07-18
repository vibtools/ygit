from __future__ import annotations

from urllib.parse import parse_qs, urlparse

import pytest

from backend.engines.auth_engine.connected_accounts_module.internal.oauth_state import (
    ConnectedAccountInstallState,
    ConnectedAccountOAuthState,
)
from backend.engines.auth_engine.connected_accounts_module.internal.service import ConnectedAccountsInternalService


@pytest.mark.asyncio
async def test_github_connect_uses_github_app_installation_url() -> None:
    service = ConnectedAccountsInternalService()

    result = await service.start_provider_connect(user_id="user_1", provider="github")

    parsed = urlparse(result.authorization_url)
    query = parse_qs(parsed.query)

    assert result.provider == "github"
    assert parsed.scheme == "https"
    assert parsed.netloc == "github.com"
    assert parsed.path == "/apps/ygit/installations/new"
    assert query["state"] == [result.state]
    assert ConnectedAccountInstallState.validate_state(
        state=result.state,
        user_id="user_1",
        provider="github",
    )

    unsafe_terms = [
        "private_key",
        "client_secret",
        "access_token",
        "installation_token",
        "refresh_token",
    ]
    lowered_url = result.authorization_url.lower()
    for unsafe_term in unsafe_terms:
        assert unsafe_term not in lowered_url


@pytest.mark.asyncio
async def test_cloudflare_connect_keeps_placeholder_callback_url() -> None:
    service = ConnectedAccountsInternalService()

    result = await service.start_provider_connect(user_id="user_1", provider="cloudflare")

    parsed = urlparse(result.authorization_url)
    query = parse_qs(parsed.query)

    assert result.provider == "cloudflare"
    assert "/api/v1/connected-accounts/cloudflare/callback" in result.authorization_url
    assert query["state"] == [result.state]
    assert ConnectedAccountOAuthState.validate_state(
        state=result.state,
        user_id="user_1",
        provider="cloudflare",
    )
