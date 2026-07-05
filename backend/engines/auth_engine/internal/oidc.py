from __future__ import annotations

import time
from typing import Any
from urllib.parse import urlencode

import httpx

from backend.core.config import Settings
from backend.engines.auth_engine.errors import AuthOidcCallbackFailedError
from backend.engines.auth_engine.internal.pkce import code_challenge_s256
from backend.engines.auth_engine.schemas import OIDCProviderMetadata, OIDCUserClaims, TokenResponse


class OIDCClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._metadata: OIDCProviderMetadata | None = None
        self._jwks: dict[str, Any] | None = None

    @property
    def issuer(self) -> str:
        return str(self._settings.keycloak_issuer).rstrip("/")

    async def metadata(self) -> OIDCProviderMetadata:
        if self._metadata is not None:
            return self._metadata
        url = f"{self.issuer}/.well-known/openid-configuration"
        async with httpx.AsyncClient(timeout=self._settings.oidc_http_timeout_seconds) as client:
            response = await client.get(url)
            response.raise_for_status()
        self._metadata = OIDCProviderMetadata.model_validate(response.json())
        return self._metadata

    async def build_authorization_url(self, *, state: str, nonce: str, code_verifier: str) -> str:
        metadata = await self.metadata()
        params = {
            "client_id": self._settings.keycloak_client_id,
            "response_type": "code",
            "scope": self._settings.oidc_scope,
            "redirect_uri": self._settings.keycloak_redirect_uri,
            "state": state,
            "nonce": nonce,
            "code_challenge": code_challenge_s256(code_verifier),
            "code_challenge_method": "S256",
        }
        return f"{metadata.authorization_endpoint}?{urlencode(params)}"

    async def exchange_code(self, *, code: str, code_verifier: str) -> TokenResponse:
        metadata = await self.metadata()
        payload = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self._settings.keycloak_redirect_uri,
            "client_id": self._settings.keycloak_client_id,
            "client_secret": self._settings.keycloak_client_secret.get_secret_value(),
            "code_verifier": code_verifier,
        }
        async with httpx.AsyncClient(timeout=self._settings.oidc_http_timeout_seconds) as client:
            response = await client.post(metadata.token_endpoint, data=payload)
        if response.status_code >= 400:
            raise AuthOidcCallbackFailedError("OIDC token exchange failed.")
        return TokenResponse.model_validate(response.json())

    async def _jwks_for_validation(self) -> dict[str, Any]:
        if self._jwks is not None:
            return self._jwks
        metadata = await self.metadata()
        async with httpx.AsyncClient(timeout=self._settings.oidc_http_timeout_seconds) as client:
            response = await client.get(metadata.jwks_uri)
            response.raise_for_status()
        self._jwks = response.json()
        return self._jwks

    async def validate_id_token(self, id_token: str, *, nonce: str) -> dict[str, Any]:
        try:
            import jwt
            from jwt import PyJWKClient
        except ImportError as exc:  # pragma: no cover
            raise AuthOidcCallbackFailedError("PyJWT dependency is not installed.") from exc

        metadata = await self.metadata()
        jwks_client = PyJWKClient(metadata.jwks_uri)
        try:
            signing_key = jwks_client.get_signing_key_from_jwt(id_token)
            claims = jwt.decode(
                id_token,
                signing_key.key,
                algorithms=self._settings.oidc_allowed_algorithms,
                audience=self._settings.keycloak_client_id,
                issuer=self.issuer,
                options={"require": ["exp", "iat", "iss", "aud", "sub"]},
            )
        except Exception as exc:
            raise AuthOidcCallbackFailedError("OIDC ID token validation failed.") from exc

        if claims.get("nonce") != nonce:
            raise AuthOidcCallbackFailedError("OIDC nonce validation failed.")
        exp = claims.get("exp")
        if isinstance(exp, int) and exp < int(time.time()):
            raise AuthOidcCallbackFailedError("OIDC ID token has expired.")
        return claims

    async def userinfo(self, access_token: str) -> dict[str, Any] | None:
        metadata = await self.metadata()
        if not metadata.userinfo_endpoint:
            return None
        async with httpx.AsyncClient(timeout=self._settings.oidc_http_timeout_seconds) as client:
            response = await client.get(
                metadata.userinfo_endpoint,
                headers={"Authorization": f"Bearer {access_token}"},
            )
        if response.status_code >= 400:
            return None
        payload = response.json()
        return payload if isinstance(payload, dict) else None

    def build_logout_url(self, *, id_token_hint: str | None) -> str:
        # Keycloak supports this endpoint pattern even when discovery does not expose it.
        params = {"post_logout_redirect_uri": self._settings.keycloak_post_logout_redirect_uri}
        if id_token_hint:
            params["id_token_hint"] = id_token_hint
        return f"{self.issuer}/protocol/openid-connect/logout?{urlencode(params)}"

    def build_user_claims(
        self,
        *,
        claims: dict[str, Any],
        userinfo: dict[str, Any] | None = None,
    ) -> OIDCUserClaims:
        source = {**claims, **(userinfo or {})}
        roles = set()
        realm_access = source.get("realm_access")
        if isinstance(realm_access, dict) and isinstance(realm_access.get("roles"), list):
            roles.update(str(role) for role in realm_access["roles"])
        resource_access = source.get("resource_access")
        if isinstance(resource_access, dict):
            client_access = resource_access.get(self._settings.keycloak_client_id)
            if isinstance(client_access, dict) and isinstance(client_access.get("roles"), list):
                roles.update(str(role) for role in client_access["roles"])
        return OIDCUserClaims(
            subject=str(source["sub"]),
            email=str(source["email"]).lower(),
            email_verified=bool(source.get("email_verified", False)),
            name=source.get("name") or source.get("preferred_username"),
            avatar_url=source.get("picture"),
            roles=tuple(sorted(roles)),
            raw_claims=claims,
        )
