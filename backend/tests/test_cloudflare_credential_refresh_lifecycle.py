from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from pydantic import SecretStr

from backend.engines.auth_engine.connected_accounts_module.errors import (
    ProviderConnectionFailedError,
    ProviderTokenInvalidError,
)
from backend.engines.auth_engine.connected_accounts_module.internal import (
    service as service_module,
)
from backend.engines.auth_engine.connected_accounts_module.internal.credential_vault import (
    ConnectedAccountCredentialVault,
)
from backend.engines.auth_engine.connected_accounts_module.internal.service import (
    ConnectedAccountsInternalService,
)
from backend.engines.auth_engine.connected_accounts_module.schemas import (
    ConnectedAccountRecord,
)
from backend.providers.cloudflare_provider.errors import (
    CloudflareOAuthRefreshError,
    CloudflareProviderUnavailableError,
)
from backend.providers.cloudflare_provider.schemas import (
    CloudflareAccountValidation,
    CloudflareOAuthResponse,
)


REFERENCE = "cloudflare_oauth_account:account-1"


class FakeDb:
    def __init__(self) -> None:
        self.commit_count = 0

    async def commit(self) -> None:
        self.commit_count += 1


class RefreshRepository:
    def __init__(self, *, record: ConnectedAccountRecord, ciphertext: str) -> None:
        self.record = record
        self.ciphertext = ciphertext
        self.updated_ciphertext: str | None = None
        self.reconnect_calls = 0

    async def get_credential_storage(self, db, *, user_id: str, provider: str):
        assert user_id == self.record.user_id
        assert provider == "cloudflare"
        return self.record, self.ciphertext

    async def update_credential_storage(
        self,
        db,
        *,
        user_id: str,
        provider: str,
        token_ciphertext: str,
        token_key_version: str,
        scopes: list[str],
    ):
        assert user_id == self.record.user_id
        assert provider == "cloudflare"
        self.ciphertext = token_ciphertext
        self.updated_ciphertext = token_ciphertext
        self.record = self.record.model_copy(
            update={
                "status": "connected",
                "token_key_version": token_key_version,
                "scopes": scopes,
                "last_error_code": None,
            }
        )
        return self.record

    async def mark_reconnect_required(
        self,
        db,
        *,
        user_id: str,
        provider: str,
        error_code: str,
    ):
        assert user_id == self.record.user_id
        assert provider == "cloudflare"
        self.reconnect_calls += 1
        self.ciphertext = ""
        self.record = self.record.model_copy(
            update={
                "status": "reconnect_required",
                "token_key_version": None,
                "last_error_code": error_code,
            }
        )
        return self.record


class RefreshProvider:
    def __init__(
        self,
        *,
        response: CloudflareOAuthResponse | None = None,
        account_id: str = "account-1",
        refresh_error: Exception | None = None,
        validation_error: Exception | None = None,
    ) -> None:
        self.response = response
        self.account_id = account_id
        self.refresh_error = refresh_error
        self.validation_error = validation_error
        self.refresh_values: list[str] = []

    async def refresh_oauth_token(self, **kwargs) -> CloudflareOAuthResponse:
        self.refresh_values.append(kwargs["refresh_value"])
        if self.refresh_error is not None:
            raise self.refresh_error
        assert self.response is not None
        return self.response

    async def validate_oauth_access(
        self,
        *,
        bearer_value: str,
        scopes: list[str],
    ) -> CloudflareAccountValidation:
        if self.validation_error is not None:
            raise self.validation_error
        assert bearer_value
        return CloudflareAccountValidation(
            account_id=self.account_id,
            account_name="Vib Tools",
            scopes=scopes,
        )


def create_vault() -> ConnectedAccountCredentialVault:
    return ConnectedAccountCredentialVault(
        key_value="refresh-lifecycle-key-for-tests",
        key_version="test-v1",
    )


def create_record() -> ConnectedAccountRecord:
    return ConnectedAccountRecord(
        id="acct_cloudflare",
        user_id="user_1",
        provider="cloudflare",
        status="connected",
        provider_account_id="account-1",
        provider_account_name="Vib Tools",
        token_secret_ref=REFERENCE,
        token_key_version="test-v1",
        scopes=["account:read", "pages:write"],
    )


def create_expired_ciphertext(
    vault: ConnectedAccountCredentialVault,
    *,
    refresh_value: str | None = "old-refresh-value",
) -> str:
    payload = {
        "provider": "cloudflare",
        "token_reference": REFERENCE,
        "access_value": "expired-access-value",
        "refresh_value": refresh_value,
        "token_type": "bearer",
        "expires_at": (
            datetime.now(timezone.utc) - timedelta(minutes=5)
        ).isoformat(),
        "scopes": ["account:read", "pages:write"],
    }
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return vault._cipher.encrypt(encoded).decode("ascii")


def install_settings(monkeypatch) -> None:
    settings = SimpleNamespace(
        cloudflare_oauth_client_id="client-id",
        cloudflare_oauth_client_secret=SecretStr("client-secret-for-tests"),
    )
    monkeypatch.setattr(service_module, "get_settings", lambda: settings)


def create_response(*, refresh_value: str | None) -> CloudflareOAuthResponse:
    values = {
        "access_token": "new-access-value",
        "refresh_token": refresh_value,
        "token_type": "bearer",
        "expires_in": 3600,
        "scope": "account:read pages:write",
    }
    return CloudflareOAuthResponse.model_validate(values)


@pytest.mark.asyncio
async def test_refresh_rotates_and_reseals_credentials(monkeypatch) -> None:
    install_settings(monkeypatch)
    vault = create_vault()
    repository = RefreshRepository(
        record=create_record(),
        ciphertext=create_expired_ciphertext(vault),
    )
    provider = RefreshProvider(
        response=create_response(refresh_value="new-refresh-value")
    )
    service = ConnectedAccountsInternalService(
        repository=repository,
        cloudflare_provider=provider,
        credential_vault=vault,
    )
    db = FakeDb()

    resolved = await service.refresh_cloudflare_credential(
        db,
        user_id="user_1",
        token_secret_ref=REFERENCE,
    )

    assert db.commit_count == 1
    assert repository.reconnect_calls == 0
    assert repository.updated_ciphertext is not None
    assert "new-access-value" not in repository.updated_ciphertext
    assert "new-refresh-value" not in repository.updated_ciphertext
    assert resolved.access_token.get_secret_value() == "new-access-value"
    assert resolved.refresh_token is not None
    assert resolved.refresh_token.get_secret_value() == "new-refresh-value"


@pytest.mark.asyncio
async def test_refresh_preserves_existing_refresh_value(monkeypatch) -> None:
    install_settings(monkeypatch)
    vault = create_vault()
    repository = RefreshRepository(
        record=create_record(),
        ciphertext=create_expired_ciphertext(vault),
    )
    provider = RefreshProvider(response=create_response(refresh_value=None))
    service = ConnectedAccountsInternalService(
        repository=repository,
        cloudflare_provider=provider,
        credential_vault=vault,
    )

    resolved = await service.refresh_cloudflare_credential(
        FakeDb(),
        user_id="user_1",
        token_secret_ref=REFERENCE,
    )

    assert resolved.refresh_token is not None
    assert resolved.refresh_token.get_secret_value() == "old-refresh-value"


@pytest.mark.asyncio
async def test_permanent_refresh_rejection_requires_reconnect(monkeypatch) -> None:
    install_settings(monkeypatch)
    vault = create_vault()
    repository = RefreshRepository(
        record=create_record(),
        ciphertext=create_expired_ciphertext(vault),
    )
    provider = RefreshProvider(
        refresh_error=CloudflareOAuthRefreshError("refresh rejected")
    )
    service = ConnectedAccountsInternalService(
        repository=repository,
        cloudflare_provider=provider,
        credential_vault=vault,
    )
    db = FakeDb()

    with pytest.raises(ProviderTokenInvalidError):
        await service.refresh_cloudflare_credential(
            db,
            user_id="user_1",
            token_secret_ref=REFERENCE,
        )

    assert db.commit_count == 1
    assert repository.reconnect_calls == 1
    assert repository.record.status == "reconnect_required"
    assert repository.ciphertext == ""


@pytest.mark.asyncio
async def test_refreshed_account_mismatch_requires_reconnect(monkeypatch) -> None:
    install_settings(monkeypatch)
    vault = create_vault()
    repository = RefreshRepository(
        record=create_record(),
        ciphertext=create_expired_ciphertext(vault),
    )
    provider = RefreshProvider(
        response=create_response(refresh_value="rotated-refresh"),
        account_id="account-2",
    )
    service = ConnectedAccountsInternalService(
        repository=repository,
        cloudflare_provider=provider,
        credential_vault=vault,
    )
    db = FakeDb()

    with pytest.raises(ProviderTokenInvalidError):
        await service.refresh_cloudflare_credential(
            db,
            user_id="user_1",
            token_secret_ref=REFERENCE,
        )

    assert db.commit_count == 1
    assert repository.reconnect_calls == 1
    assert repository.record.status == "reconnect_required"


@pytest.mark.asyncio
async def test_provider_outage_does_not_destroy_credentials(monkeypatch) -> None:
    install_settings(monkeypatch)
    vault = create_vault()
    original_ciphertext = create_expired_ciphertext(vault)
    repository = RefreshRepository(
        record=create_record(),
        ciphertext=original_ciphertext,
    )
    provider = RefreshProvider(
        refresh_error=CloudflareProviderUnavailableError("temporary outage")
    )
    service = ConnectedAccountsInternalService(
        repository=repository,
        cloudflare_provider=provider,
        credential_vault=vault,
    )
    db = FakeDb()

    with pytest.raises(ProviderConnectionFailedError):
        await service.refresh_cloudflare_credential(
            db,
            user_id="user_1",
            token_secret_ref=REFERENCE,
        )

    assert db.commit_count == 0
    assert repository.reconnect_calls == 0
    assert repository.ciphertext == original_ciphertext
    assert repository.record.status == "connected"


@pytest.mark.asyncio
async def test_missing_refresh_value_requires_reconnect(monkeypatch) -> None:
    install_settings(monkeypatch)
    vault = create_vault()
    repository = RefreshRepository(
        record=create_record(),
        ciphertext=create_expired_ciphertext(vault, refresh_value=None),
    )
    provider = RefreshProvider(
        response=create_response(refresh_value="unused-refresh")
    )
    service = ConnectedAccountsInternalService(
        repository=repository,
        cloudflare_provider=provider,
        credential_vault=vault,
    )
    db = FakeDb()

    with pytest.raises(ProviderTokenInvalidError):
        await service.refresh_cloudflare_credential(
            db,
            user_id="user_1",
            token_secret_ref=REFERENCE,
        )

    assert db.commit_count == 1
    assert repository.reconnect_calls == 1
    assert provider.refresh_values == []
