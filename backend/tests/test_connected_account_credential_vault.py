from __future__ import annotations

from types import SimpleNamespace

import pytest
from pydantic import SecretStr

from backend.engines.auth_engine.connected_accounts_module.errors import (
    ProviderTokenInvalidError,
)
from backend.engines.auth_engine.connected_accounts_module.internal import (
    service as service_module,
)
from backend.engines.auth_engine.connected_accounts_module.internal.credential_vault import (
    ConnectedAccountCredentialVault,
)
from backend.engines.auth_engine.connected_accounts_module.internal.oauth_state import (
    ConnectedAccountOAuthState,
)
from backend.engines.auth_engine.connected_accounts_module.internal.service import (
    ConnectedAccountsInternalService,
)
from backend.engines.auth_engine.connected_accounts_module.schemas import (
    ConnectedAccountRecord,
)
from backend.providers.cloudflare_provider.schemas import (
    CloudflareAccountValidation,
    CloudflareOAuthResponse,
)


REFERENCE = (
    "cloudflare_oauth_account:"
    "account-1"
)


class FakeDb:
    def __init__(self) -> None:
        self.committed = False

    async def commit(self) -> None:
        self.committed = True


class VaultRepository:
    def __init__(self) -> None:
        self.record: ConnectedAccountRecord | None = None
        self.ciphertext: str | None = None

    async def get_by_user_provider(
        self,
        db,
        *,
        user_id: str,
        provider: str,
    ):
        return self.record

    async def get_credential_storage(
        self,
        db,
        *,
        user_id: str,
        provider: str,
    ):
        if self.record is None:
            return None

        return (
            self.record,
            self.ciphertext,
        )

    async def upsert_connected(
        self,
        db,
        *,
        user_id: str,
        provider: str,
        provider_account_id: str | None,
        provider_account_name: str | None,
        token_secret_ref: str,
        token_key_version: str,
        scopes: list[str],
        token_ciphertext: str | None = None,
    ) -> ConnectedAccountRecord:
        self.record = ConnectedAccountRecord(
            id="acct_cloudflare",
            user_id=user_id,
            provider=provider,
            status="connected",
            provider_account_id=provider_account_id,
            provider_account_name=provider_account_name,
            token_secret_ref=token_secret_ref,
            token_key_version=token_key_version,
            scopes=scopes,
        )
        self.ciphertext = token_ciphertext
        return self.record


class LegacyRepository:
    def __init__(self) -> None:
        self.record: ConnectedAccountRecord | None = None

    async def upsert_connected(
        self,
        db,
        *,
        user_id: str,
        provider: str,
        provider_account_id: str | None,
        provider_account_name: str | None,
        token_secret_ref: str,
        token_key_version: str,
        scopes: list[str],
    ) -> ConnectedAccountRecord:
        self.record = ConnectedAccountRecord(
            id="acct_legacy",
            user_id=user_id,
            provider=provider,
            status="connected",
            provider_account_id=provider_account_id,
            provider_account_name=provider_account_name,
            token_secret_ref=token_secret_ref,
            token_key_version=token_key_version,
            scopes=scopes,
        )
        return self.record


class OAuthProvider:
    async def exchange_oauth_code(
        self,
        **kwargs,
    ) -> CloudflareOAuthResponse:
        assert kwargs["code_value"] == "provider_auth_code"

        return CloudflareOAuthResponse(
            access_token="cloudflare-access-value",
            refresh_token="cloudflare-refresh-value",
            token_type="bearer",
            expires_in=3600,
            scope="account:read pages:write",
        )

    async def validate_oauth_access(
        self,
        *,
        bearer_value: str,
        scopes: list[str],
    ) -> CloudflareAccountValidation:
        assert bearer_value == "cloudflare-access-value"

        return CloudflareAccountValidation(
            account_id="account-1",
            account_name="Vib Tools",
            scopes=scopes,
        )


class LegacyProvider:
    async def validate_account(
        self,
        token_ref: str,
    ) -> dict[str, str]:
        assert token_ref

        return {
            "account_id": "legacy-account",
            "account_name": "Legacy Account",
        }


def create_vault() -> ConnectedAccountCredentialVault:
    return ConnectedAccountCredentialVault(
        key_value="credential-vault-key-for-tests",
        key_version="test-v1",
    )


def create_ciphertext(
    vault: ConnectedAccountCredentialVault,
) -> str:
    return vault.seal_cloudflare_oauth(
        token_reference=REFERENCE,
        access_value="cloudflare-access-value",
        refresh_value="cloudflare-refresh-value",
        token_type="bearer",
        expires_in=3600,
        scopes=[
            "account:read",
            "pages:write",
        ],
    )


def test_vault_round_trip_masks_secret_values() -> None:
    vault = create_vault()
    ciphertext = create_ciphertext(vault)

    assert "cloudflare-access-value" not in ciphertext
    assert "cloudflare-refresh-value" not in ciphertext

    resolved = vault.resolve_cloudflare(
        ciphertext=ciphertext,
        stored_key_version="test-v1",
        token_reference=REFERENCE,
    )

    assert (
        resolved.access_token.get_secret_value()
        == "cloudflare-access-value"
    )
    assert resolved.refresh_token is not None
    assert (
        resolved.refresh_token.get_secret_value()
        == "cloudflare-refresh-value"
    )

    serialized = resolved.model_dump_json()

    assert "cloudflare-access-value" not in serialized
    assert "cloudflare-refresh-value" not in serialized


def test_vault_rejects_modified_ciphertext() -> None:
    vault = create_vault()
    ciphertext = create_ciphertext(vault)

    replacement = (
        "A"
        if ciphertext[-1] != "A"
        else "B"
    )
    altered = ciphertext[:-1] + replacement

    with pytest.raises(ProviderTokenInvalidError):
        vault.resolve_cloudflare(
            ciphertext=altered,
            stored_key_version="test-v1",
            token_reference=REFERENCE,
        )


def test_vault_rejects_unknown_key_version() -> None:
    vault = create_vault()
    ciphertext = create_ciphertext(vault)

    with pytest.raises(ProviderTokenInvalidError):
        vault.resolve_cloudflare(
            ciphertext=ciphertext,
            stored_key_version="test-v2",
            token_reference=REFERENCE,
        )


def test_vault_binds_ciphertext_to_safe_reference() -> None:
    vault = create_vault()
    ciphertext = create_ciphertext(vault)

    with pytest.raises(ProviderTokenInvalidError):
        vault.resolve_cloudflare(
            ciphertext=ciphertext,
            stored_key_version="test-v1",
            token_reference=(
                "cloudflare_oauth_account:"
                "account-2"
            ),
        )


@pytest.mark.asyncio
async def test_oauth_callback_persists_and_resolves_ciphertext(
    monkeypatch,
) -> None:
    settings = SimpleNamespace(
        cloudflare_oauth_client_id="client-id",
        cloudflare_oauth_client_secret=SecretStr(
            "client-value-for-test"
        ),
        cloudflare_oauth_redirect_uri=(
            "http://localhost/callback"
        ),
        cloudflare_oauth_scopes=(
            "account:read pages:write"
        ),
    )

    monkeypatch.setattr(
        service_module,
        "get_settings",
        lambda: settings,
    )

    repository = VaultRepository()
    vault = create_vault()
    service = ConnectedAccountsInternalService(
        repository=repository,
        cloudflare_provider=OAuthProvider(),
        credential_vault=vault,
    )

    state = ConnectedAccountOAuthState.new_state(
        user_id="user_1",
        provider="cloudflare",
    )
    db = FakeDb()

    await service.handle_provider_callback(
        db,
        user_id="user_1",
        provider="cloudflare",
        code="provider_auth_code",
        state=state,
    )

    assert db.committed is True
    assert repository.record is not None
    assert repository.ciphertext is not None
    assert (
        "cloudflare-access-value"
        not in repository.ciphertext
    )
    assert (
        "cloudflare-refresh-value"
        not in repository.ciphertext
    )

    resolved = await service.resolve_cloudflare_credential(
        db,
        user_id="user_1",
        token_secret_ref=(
            repository.record.token_secret_ref
            or ""
        ),
    )

    assert (
        resolved.access_token.get_secret_value()
        == "cloudflare-access-value"
    )


@pytest.mark.asyncio
async def test_unconfigured_fallback_keeps_legacy_repository_signature(
    monkeypatch,
) -> None:
    settings = SimpleNamespace(
        cloudflare_oauth_client_id="",
        cloudflare_oauth_client_secret=SecretStr(""),
        cloudflare_oauth_redirect_uri=(
            "http://localhost/callback"
        ),
        cloudflare_oauth_scopes="",
    )

    monkeypatch.setattr(
        service_module,
        "get_settings",
        lambda: settings,
    )

    repository = LegacyRepository()
    service = ConnectedAccountsInternalService(
        repository=repository,
        cloudflare_provider=LegacyProvider(),
    )

    state = ConnectedAccountOAuthState.new_state(
        user_id="user_1",
        provider="cloudflare",
    )

    result = await service.handle_provider_callback(
        FakeDb(),
        user_id="user_1",
        provider="cloudflare",
        code="provider_auth_code",
        state=state,
    )

    assert result.connected is True
    assert repository.record is not None
    assert (
        repository.record.provider_account_id
        == "legacy-account"
    )
