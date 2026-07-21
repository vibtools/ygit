from __future__ import annotations

import base64
import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone

from cryptography.fernet import Fernet, InvalidToken
from pydantic import SecretStr

from backend.core.config import get_settings
from backend.engines.auth_engine.connected_accounts_module.errors import (
    ProviderCredentialExpiredError,
    ProviderTokenInvalidError,
)
from backend.engines.auth_engine.connected_accounts_module.schemas import (
    ResolvedProviderCredential,
)


class ConnectedAccountCredentialVault:
    def __init__(
        self,
        *,
        key_value: str,
        key_version: str,
    ) -> None:
        normalized_key = key_value.strip()
        normalized_version = key_version.strip()

        if not normalized_key or not normalized_version:
            raise ValueError(
                "Credential vault configuration is incomplete."
            )

        digest = hashlib.sha256(
            normalized_key.encode("utf-8")
        ).digest()

        self._key_version = normalized_version
        self._cipher = Fernet(
            base64.urlsafe_b64encode(digest)
        )

    @classmethod
    def from_settings(
        cls,
    ) -> "ConnectedAccountCredentialVault":
        settings = get_settings()

        return cls(
            key_value=(
                settings.token_encryption_key
                .get_secret_value()
            ),
            key_version=(
                settings.token_encryption_key_version
            ),
        )

    @property
    def key_version(self) -> str:
        return self._key_version

    def seal_cloudflare_oauth(
        self,
        *,
        token_reference: str,
        access_value: str,
        refresh_value: str | None,
        token_type: str,
        expires_in: int | None,
        scopes: list[str],
    ) -> str:
        normalized_reference = token_reference.strip()
        normalized_access = access_value.strip()

        if (
            not normalized_reference.startswith(
                "cloudflare_oauth_account:"
            )
            or not normalized_access
        ):
            raise ProviderTokenInvalidError()

        expires_at: datetime | None = None

        if expires_in is not None:
            if expires_in <= 0:
                raise ProviderTokenInvalidError()

            expires_at = (
                datetime.now(timezone.utc)
                + timedelta(seconds=expires_in)
            )

        payload = {
            "provider": "cloudflare",
            "token_reference": normalized_reference,
            "access_value": normalized_access,
            "refresh_value": (
                refresh_value.strip()
                if refresh_value
                else None
            ),
            "token_type": token_type.strip() or "bearer",
            "expires_at": (
                expires_at.isoformat()
                if expires_at
                else None
            ),
            "scopes": [
                str(scope).strip()
                for scope in scopes
                if str(scope).strip()
            ],
        }

        encoded = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        return self._cipher.encrypt(
            encoded
        ).decode("ascii")

    def resolve_cloudflare(
        self,
        *,
        ciphertext: str,
        stored_key_version: str,
        token_reference: str,
    ) -> ResolvedProviderCredential:
        normalized_reference = token_reference.strip()

        if (
            not ciphertext
            or not hmac.compare_digest(
                stored_key_version,
                self._key_version,
            )
            or not normalized_reference.startswith(
                "cloudflare_oauth_account:"
            )
        ):
            raise ProviderTokenInvalidError()

        try:
            decoded = self._cipher.decrypt(
                ciphertext.encode("ascii")
            )
            payload = json.loads(
                decoded.decode("utf-8")
            )
        except (
            InvalidToken,
            UnicodeDecodeError,
            json.JSONDecodeError,
            TypeError,
            ValueError,
        ) as exc:
            raise ProviderTokenInvalidError() from exc

        stored_reference = str(
            payload.get("token_reference")
            or ""
        ).strip()

        if (
            payload.get("provider") != "cloudflare"
            or not hmac.compare_digest(
                stored_reference,
                normalized_reference,
            )
        ):
            raise ProviderTokenInvalidError()

        access_value = str(
            payload.get("access_value")
            or ""
        ).strip()

        if not access_value:
            raise ProviderTokenInvalidError()

        expires_value = payload.get("expires_at")

        try:
            expires_at = (
                datetime.fromisoformat(
                    str(expires_value)
                )
                if expires_value
                else None
            )
        except ValueError as exc:
            raise ProviderTokenInvalidError() from exc

        if (
            expires_at is not None
            and expires_at.tzinfo is None
        ):
            raise ProviderTokenInvalidError()

        if (
            expires_at is not None
            and expires_at
            <= datetime.now(timezone.utc)
        ):
            raise ProviderCredentialExpiredError()

        raw_scopes = payload.get("scopes")

        if not isinstance(raw_scopes, list):
            raise ProviderTokenInvalidError()

        result_data = {
            "provider": "cloudflare",
            "token_secret_ref": normalized_reference,
            "access_token": SecretStr(access_value),
            "refresh_token": (
                SecretStr(
                    str(payload.get("refresh_value"))
                )
                if payload.get("refresh_value")
                else None
            ),
            "token_type": str(
                payload.get("token_type")
                or "bearer"
            ),
            "expires_at": expires_at,
            "scopes": [
                str(scope)
                for scope in raw_scopes
            ],
        }

        return ResolvedProviderCredential.model_validate(
            result_data
        )

    def resolve_cloudflare_for_refresh(
        self,
        *,
        ciphertext: str,
        stored_key_version: str,
        token_reference: str,
    ) -> ResolvedProviderCredential:
        normalized_reference = token_reference.strip()

        if (
            not ciphertext
            or not hmac.compare_digest(
                stored_key_version,
                self._key_version,
            )
            or not normalized_reference.startswith(
                "cloudflare_oauth_account:"
            )
        ):
            raise ProviderTokenInvalidError()

        try:
            decoded = self._cipher.decrypt(
                ciphertext.encode("ascii")
            )
            payload = json.loads(
                decoded.decode("utf-8")
            )
        except (
            InvalidToken,
            UnicodeDecodeError,
            json.JSONDecodeError,
            TypeError,
            ValueError,
        ) as exc:
            raise ProviderTokenInvalidError() from exc

        stored_reference = str(
            payload.get("token_reference")
            or ""
        ).strip()

        if (
            payload.get("provider") != "cloudflare"
            or not hmac.compare_digest(
                stored_reference,
                normalized_reference,
            )
        ):
            raise ProviderTokenInvalidError()

        access_value = str(
            payload.get("access_value")
            or ""
        ).strip()
        refresh_value = str(
            payload.get("refresh_value")
            or ""
        ).strip()

        if not access_value or not refresh_value:
            raise ProviderTokenInvalidError()

        expires_value = payload.get("expires_at")

        try:
            expires_at = (
                datetime.fromisoformat(
                    str(expires_value)
                )
                if expires_value
                else None
            )
        except ValueError as exc:
            raise ProviderTokenInvalidError() from exc

        if (
            expires_at is not None
            and expires_at.tzinfo is None
        ):
            raise ProviderTokenInvalidError()

        raw_scopes = payload.get("scopes")

        if not isinstance(raw_scopes, list):
            raise ProviderTokenInvalidError()

        result_data = {
            "provider": "cloudflare",
            "token_secret_ref": normalized_reference,
            "access_token": SecretStr(access_value),
            "refresh_token": SecretStr(refresh_value),
            "token_type": str(
                payload.get("token_type")
                or "bearer"
            ),
            "expires_at": expires_at,
            "scopes": [
                str(scope)
                for scope in raw_scopes
            ],
        }

        return ResolvedProviderCredential.model_validate(
            result_data
        )
