from __future__ import annotations

import pytest

from backend.engines.auth_engine.connected_accounts_module.errors import ProviderNotSupportedError
from backend.engines.auth_engine.connected_accounts_module.internal.oauth_state import ConnectedAccountOAuthState
from backend.engines.auth_engine.connected_accounts_module.internal.service import ConnectedAccountsInternalService
from backend.engines.auth_engine.connected_accounts_module.schemas import ConnectedAccountRecord


class FakeRepository:
    def __init__(self) -> None:
        self.records: dict[tuple[str, str], ConnectedAccountRecord] = {}

    async def list_by_user(self, db, *, user_id: str):
        return []

    async def get_by_user_provider(self, db, *, user_id: str, provider: str):
        return self.records.get((user_id, provider))

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
        record = ConnectedAccountRecord(
            id=f"acct_{provider}",
            user_id=user_id,
            provider=provider,  # type: ignore[arg-type]
            status="connected",
            provider_account_id=provider_account_id,
            provider_account_name=provider_account_name,
            token_secret_ref=token_secret_ref,
            token_key_version=token_key_version,
            scopes=scopes,
        )
        self.records[(user_id, provider)] = record
        return record

    async def mark_disconnected(self, db, *, user_id: str, provider: str) -> ConnectedAccountRecord:
        record = ConnectedAccountRecord(
            id=f"acct_{provider}",
            user_id=user_id,
            provider=provider,  # type: ignore[arg-type]
            status="disconnected",
        )
        self.records[(user_id, provider)] = record
        return record

    async def mark_provider_error(self, db, *, user_id: str, provider: str, error_code: str) -> ConnectedAccountRecord:
        record = ConnectedAccountRecord(
            id=f"acct_{provider}",
            user_id=user_id,
            provider=provider,  # type: ignore[arg-type]
            status="error",
            last_error_code=error_code,
        )
        self.records[(user_id, provider)] = record
        return record

    def to_record(self, model):
        return model


class FakeProvider:
    def __init__(self, provider: str) -> None:
        self.provider = provider

    async def validate_account(self, token_ref: str) -> dict[str, str]:
        assert token_ref
        return {"provider": self.provider, "status": "validated", "account_name": f"{self.provider}-tester"}


class FakeDb:
    def __init__(self) -> None:
        self.committed = False

    async def commit(self) -> None:
        self.committed = True


@pytest.mark.asyncio
async def test_list_connected_accounts_returns_safe_default_summaries() -> None:
    service = ConnectedAccountsInternalService(repository=FakeRepository())  # type: ignore[arg-type]
    result = await service.list_connected_accounts(FakeDb(), user_id="user_1")  # type: ignore[arg-type]

    assert [item.provider for item in result.accounts] == ["github", "cloudflare"]
    assert all(item.connected is False for item in result.accounts)
    assert all(not hasattr(item, "token_secret_ref") for item in result.accounts)


@pytest.mark.asyncio
async def test_provider_callback_creates_safe_token_reference_not_api_token() -> None:
    repository = FakeRepository()
    service = ConnectedAccountsInternalService(
        repository=repository,  # type: ignore[arg-type]
        github_provider=FakeProvider("github"),  # type: ignore[arg-type]
        cloudflare_provider=FakeProvider("cloudflare"),  # type: ignore[arg-type]
    )
    state = ConnectedAccountOAuthState.new_state(user_id="user_1", provider="github")
    db = FakeDb()

    result = await service.handle_provider_callback(
        db,  # type: ignore[arg-type]
        user_id="user_1",
        provider="github",
        code="provider_auth_code",
        state=state,
        error=None,
        error_description=None,
    )

    assert result.connected is True
    assert result.account_name == "github-tester"
    record = repository.records[("user_1", "github")]
    assert record.token_secret_ref is not None
    assert "provider_auth_code" not in record.token_secret_ref
    assert db.committed is True
    assert "token" not in result.model_dump()


@pytest.mark.asyncio
async def test_disconnect_provider_marks_disconnected() -> None:
    repository = FakeRepository()
    repository.records[("user_1", "cloudflare")] = ConnectedAccountRecord(
        id="acct_cf",
        user_id="user_1",
        provider="cloudflare",
        status="connected",
        token_secret_ref="cloudflare_token_ref_safe",
    )
    service = ConnectedAccountsInternalService(repository=repository)  # type: ignore[arg-type]
    db = FakeDb()

    result = await service.disconnect_provider(db, user_id="user_1", provider="cloudflare")  # type: ignore[arg-type]

    assert result.connected is False
    assert result.status == "disconnected"
    assert db.committed is True


def test_unknown_provider_is_rejected() -> None:
    service = ConnectedAccountsInternalService(repository=FakeRepository())  # type: ignore[arg-type]
    with pytest.raises(ProviderNotSupportedError):
        service.parse_provider("gitlab")
