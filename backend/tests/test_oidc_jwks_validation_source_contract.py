from pathlib import Path


def _validate_id_token_source() -> str:
    source = Path("backend/engines/auth_engine/internal/oidc.py").read_text(encoding="utf-8")
    start = source.index("async def validate_id_token")
    end = source.index("async def userinfo", start)
    return source[start:end]


def test_oidc_validation_uses_httpx_jwks_cache_not_pyjwkclient_network_fetch() -> None:
    source = _validate_id_token_source()

    assert "await self._jwks_for_validation()" in source
    assert "PyJWKClient" not in source
    assert "get_signing_key_from_jwt" not in source


def test_oidc_validation_still_enforces_core_claims() -> None:
    source = _validate_id_token_source()

    assert "jwt.decode(" in source
    assert "audience=self._settings.keycloak_client_id" in source
    assert "issuer=self.issuer" in source
    assert "algorithms=self._settings.oidc_allowed_algorithms" in source
    assert 'claims.get("nonce") != nonce' in source
