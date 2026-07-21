from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest

from backend.engines.auth_engine.connected_accounts_module.errors import (
    ProviderCredentialExpiredError,
    ProviderTokenInvalidError,
)
from backend.engines.auth_engine.connected_accounts_module.internal.credential_vault import (
    ConnectedAccountCredentialVault,
)
from backend.engines.auth_engine.connected_accounts_module.internal.service import (
    ConnectedAccountsInternalService,
)
from backend.engines.auth_engine.connected_accounts_module.public import (
    ConnectedAccountsPublicService,
)
from backend.engines.auth_engine.connected_accounts_module.schemas import (
    ResolvedProviderCredential,
)

REFERENCE = "cloudflare_oauth_account:account-1"


def create_vault() -> ConnectedAccountCredentialVault:
    return ConnectedAccountCredentialVault(
        key_value="deployment-acquisition-key-for-tests",
        key_version="test-v1",
    )


def valid_credential(
    vault: ConnectedAccountCredentialVault,
) -> ResolvedProviderCredential:
    ciphertext = vault.seal_cloudflare_oauth(
        token_reference=REFERENCE,
        access_value="valid-access-value",
        refresh_value="valid-refresh-value",
        token_type="bearer",
        expires_in=3600,
        scopes=["account:read", "pages:write"],
    )
    return vault.resolve_cloudflare(
        ciphertext=ciphertext,
        stored_key_version="test-v1",
        token_reference=REFERENCE,
    )


def expired_ciphertext(
    vault: ConnectedAccountCredentialVault,
) -> str:
    payload = {
        "provider": "cloudflare",
        "token_reference": REFERENCE,
        "access_value": "expired-access-value",
        "refresh_value": "refresh-value",
        "token_type": "bearer",
        "expires_at": (
            datetime.now(timezone.utc)
            - timedelta(minutes=5)
        ).isoformat(),
        "scopes": ["account:read", "pages:write"],
    }
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return vault._cipher.encrypt(encoded).decode("ascii")


class AcquisitionInternal(ConnectedAccountsInternalService):
    def __init__(
        self,
        *,
        credential: ResolvedProviderCredential,
        resolve_error: Exception | None = None,
    ) -> None:
        self.credential = credential
        self.resolve_error = resolve_error
        self.resolve_calls = 0
        self.refresh_calls = 0

    async def resolve_cloudflare_credential(
        self,
        db,
        *,
        user_id: str,
        token_secret_ref: str,
    ) -> ResolvedProviderCredential:
        self.resolve_calls += 1
        if self.resolve_error is not None:
            raise self.resolve_error
        return self.credential

    async def refresh_cloudflare_credential(
        self,
        db,
        *,
        user_id: str,
        token_secret_ref: str,
    ) -> ResolvedProviderCredential:
        self.refresh_calls += 1
        return self.credential


class PublicInternal:
    def __init__(self, credential: ResolvedProviderCredential) -> None:
        self.credential = credential
        self.calls = 0

    async def acquire_cloudflare_deployment_credential(
        self,
        db,
        *,
        user_id: str,
        token_secret_ref: str,
    ) -> ResolvedProviderCredential:
        self.calls += 1
        assert user_id == "user_1"
        assert token_secret_ref == REFERENCE
        return self.credential


def test_vault_uses_typed_expiry_error() -> None:
    vault = create_vault()
    with pytest.raises(ProviderCredentialExpiredError):
        vault.resolve_cloudflare(
            ciphertext=expired_ciphertext(vault),
            stored_key_version="test-v1",
            token_reference=REFERENCE,
        )


@pytest.mark.asyncio
async def test_acquisition_returns_valid_credential_without_refresh() -> None:
    credential = valid_credential(create_vault())
    service = AcquisitionInternal(credential=credential)

    result = await service.acquire_cloudflare_deployment_credential(
        object(),
        user_id="user_1",
        token_secret_ref=REFERENCE,
    )

    assert result is credential
    assert service.resolve_calls == 1
    assert service.refresh_calls == 0


@pytest.mark.asyncio
async def test_acquisition_refreshes_only_expired_credential() -> None:
    credential = valid_credential(create_vault())
    service = AcquisitionInternal(
        credential=credential,
        resolve_error=ProviderCredentialExpiredError(),
    )

    result = await service.acquire_cloudflare_deployment_credential(
        object(),
        user_id="user_1",
        token_secret_ref=REFERENCE,
    )

    assert result is credential
    assert service.resolve_calls == 1
    assert service.refresh_calls == 1


@pytest.mark.asyncio
async def test_acquisition_does_not_refresh_invalid_reference() -> None:
    credential = valid_credential(create_vault())
    service = AcquisitionInternal(
        credential=credential,
        resolve_error=ProviderTokenInvalidError(),
    )

    with pytest.raises(ProviderTokenInvalidError):
        await service.acquire_cloudflare_deployment_credential(
            object(),
            user_id="user_1",
            token_secret_ref="cloudflare_oauth_account:wrong",
        )

    assert service.resolve_calls == 1
    assert service.refresh_calls == 0


@pytest.mark.asyncio
async def test_public_acquisition_boundary_masks_secret_values() -> None:
    credential = valid_credential(create_vault())
    internal = PublicInternal(credential)
    service = ConnectedAccountsPublicService(internal=internal)

    result = await service.acquire_cloudflare_deployment_credential(
        object(),
        user_id="user_1",
        token_secret_ref=REFERENCE,
    )

    serialized = result.model_dump_json()

    assert internal.calls == 1
    assert "valid-access-value" not in serialized
    assert "valid-refresh-value" not in serialized
