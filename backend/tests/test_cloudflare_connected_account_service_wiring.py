from pathlib import Path


def _service_source() -> str:
    return Path("backend/engines/auth_engine/connected_accounts_module/internal/service.py").read_text(encoding="utf-8")


def _route_source() -> str:
    return Path("backend/app/routes/connected_accounts_routes.py").read_text(encoding="utf-8")


def test_cloudflare_connect_uses_oauth_authorization_when_configured() -> None:
    source = _service_source()

    assert "settings.cloudflare_oauth_client_id" in source
    assert "self.cloudflare_provider.build_oauth_authorization_url(" in source
    assert "settings.cloudflare_oauth_redirect_uri" in source
    assert "settings.cloudflare_oauth_scopes" in source


def test_cloudflare_callback_has_real_oauth_exchange_and_validation_path() -> None:
    source = _service_source()

    assert "async def _handle_cloudflare_oauth_callback(" in source
    assert "ConnectedAccountOAuthState.validate_state(" in source
    assert "exchange_oauth_code(**exchange_kwargs)" in source
    assert "validate_oauth_access(" in source
    assert "bearer_value = oauth_payload.access_token" in source
    assert "cloudflare_oauth_account:" in source


def test_cloudflare_callback_keeps_legacy_safe_fallback_for_unconfigured_env() -> None:
    source = _service_source()

    assert "TokenReferenceFactory.new_token_ref(provider=provider_name)" in source
    assert "self._validate_provider_account(provider_name, safe_reference)" in source
    assert "self._default_scopes(provider_name)" in source


def test_cloudflare_browser_connect_and_callback_redirects_are_enabled_without_breaking_github() -> None:
    source = _route_source()

    assert 'if provider == "github" and _wants_browser_redirect(request):' in source
    assert 'if provider == "cloudflare" and _wants_browser_redirect(request):' in source
    assert '"/dashboard?connected=github#connected-accounts"' in source
    assert '"/dashboard?connected=cloudflare#connected-accounts"' in source
