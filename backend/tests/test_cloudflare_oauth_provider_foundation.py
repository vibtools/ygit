from urllib.parse import parse_qs, urlparse

from backend.providers.cloudflare_provider.client import CloudflareProviderClient


def test_cloudflare_oauth_config_keys_are_declared() -> None:
    source = open("backend/core/config.py", encoding="utf-8").read()

    assert "cloudflare_oauth_client_id" in source
    assert "cloudflare_oauth_client_secret" in source
    assert "cloudflare_oauth_redirect_uri" in source
    assert "cloudflare_oauth_authorization_url" in source
    assert "cloudflare_oauth_token_url" in source
    assert "cloudflare_api_base_url" in source


def test_cloudflare_authorization_url_contains_required_oauth_parameters() -> None:
    client = CloudflareProviderClient()
    url = client.build_oauth_authorization_url(
        client_id="client_123",
        redirect_uri="https://ygit.net/api/v1/connected-accounts/cloudflare/callback",
        scopes="account:read pages:write",
        state="ca.cloudflare.user_123.nonce",
    )

    parsed = urlparse(url)
    query = parse_qs(parsed.query)

    assert parsed.scheme == "https"
    assert parsed.netloc == "dash.cloudflare.com"
    assert parsed.path == "/oauth2/auth"
    assert query["client_id"] == ["client_123"]
    assert query["response_type"] == ["code"]
    assert query["scope"] == ["account:read pages:write"]
    assert query["state"] == ["ca.cloudflare.user_123.nonce"]


def test_cloudflare_provider_preserves_placeholder_validation_contract() -> None:
    source = open("backend/providers/cloudflare_provider/client.py", encoding="utf-8").read()

    assert "async def validate_account" in source
    assert "cloudflare-account-placeholder" in source
    assert "async def exchange_oauth_code" in source
    assert "async def validate_oauth_access" in source


def test_cloudflare_authorization_url_omits_scope_when_not_configured() -> None:
    client = CloudflareProviderClient()
    url = client.build_oauth_authorization_url(
        client_id="client_123",
        redirect_uri="https://ygit.net/api/v1/connected-accounts/cloudflare/callback",
        scopes="",
        state="ca.cloudflare.user_123.nonce",
    )

    parsed = urlparse(url)
    query = parse_qs(parsed.query)

    assert "scope" not in query
    assert query["client_id"] == ["client_123"]
    assert query["response_type"] == ["code"]
    assert query["state"] == ["ca.cloudflare.user_123.nonce"]
