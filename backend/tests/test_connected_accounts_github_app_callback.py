from __future__ import annotations

from types import SimpleNamespace

import pytest

from backend.engines.auth_engine.connected_accounts_module.errors import ProviderOAuthFailedError
from backend.engines.auth_engine.connected_accounts_module.internal import service as service_module
from backend.engines.auth_engine.connected_accounts_module.internal.oauth_state import (
    ConnectedAccountInstallState,
    ConnectedAccountOAuthState,
)
from backend.engines.auth_engine.connected_accounts_module.internal.service import ConnectedAccountsInternalService
from backend.engines.auth_engine.connected_accounts_module.schemas import ConnectedAccountRecord
from backend.providers.github_provider.schemas import GitHubAppInstallation


class FakeSecret:
    def __init__(self, value: str) -> None:
        self.value = value

    def get_secret_value(self) -> str:
        return self.value


class FakeDb:
    def __init__(self) -> None:
        self.committed = False

    async def commit(self) -> None:
        self.committed = True


class FakeRepository:
    def __init__(self) -> None:
        self.records: dict[tuple[str, str], ConnectedAccountRecord] = {}

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
            id="acct_test",
            user_id=user_id,
            provider=provider,
            status="connected",
            provider_account_id=provider_account_id,
            provider_account_name=provider_account_name,
            token_secret_ref=token_secret_ref,
            token_key_version=token_key_version,
            scopes=scopes,
        )
        self.records[(user_id, provider)] = record
        return record


class FakeGitHubProvider:
    def __init__(self) -> None:
        self.jwt_app_id: str | None = None
        self.pem_seen: str | None = None
        self.validated_installation_id: str | None = None

    def create_app_jwt(self, *, app_id: str, private_key_pem: str) -> str:
        self.jwt_app_id = app_id
        self.pem_seen = private_key_pem
        return "safe-app-jwt"

    async def get_app_installation(self, *, installation_id: str | int, app_jwt: str) -> GitHubAppInstallation:
        assert app_jwt == "safe-app-jwt"
        self.validated_installation_id = str(installation_id)
        return GitHubAppInstallation(
            installation_id=int(installation_id),
            account_id="1001",
            account_login="vibtools",
            account_type="Organization",
            target_type="Organization",
            repository_selection="selected",
        )


class FakeCloudflareProvider:
    async def validate_account(self, token_ref: str) -> dict[str, str]:
        return {
            "provider": "cloudflare",
            "status": "validated",
            "account_name": "cloudflare-tester",
            "account_id": "cf:user_1",
        }


def _settings() -> SimpleNamespace:
    settings = SimpleNamespace(github_app_id="12345")
    setattr(settings, "github_app_private_key", FakeSecret("unit-test-pem"))
    return settings


@pytest.mark.asyncio
async def test_github_app_callback_validates_installation_and_stores_safe_reference(monkeypatch: pytest.MonkeyPatch) -> None:
    repository = FakeRepository()
    github_provider = FakeGitHubProvider()
    db = FakeDb()
    monkeypatch.setattr(service_module, "get_settings", _settings)

    service = ConnectedAccountsInternalService(
        repository=repository,  # type: ignore[arg-type]
        github_provider=github_provider,  # type: ignore[arg-type]
        cloudflare_provider=FakeCloudflareProvider(),  # type: ignore[arg-type]
    )

    state = ConnectedAccountInstallState.new_state(user_id="user_1", provider="github")
    result = await service.handle_provider_callback(
        db,  # type: ignore[arg-type]
        user_id="user_1",
        provider="github",
        code=None,
        state=state,
        installation_id="98765",
        error=None,
        error_description=None,
    )

    assert result.provider == "github"
    assert result.connected is True
    assert result.account_name == "vibtools"
    assert db.committed is True
    assert github_provider.jwt_app_id == "12345"
    assert github_provider.pem_seen == "unit-test-pem"
    assert github_provider.validated_installation_id == "98765"

    record = repository.records[("user_1", "github")]
    assert record.provider_account_id == "98765"
    assert record.provider_account_name == "vibtools"
    assert record.token_secret_ref == "github_app_installation:98765"
    assert "access_token" not in record.token_secret_ref
    assert "installation_token" not in record.token_secret_ref
    assert record.scopes == ["github_app:installation", "repositories:selected"]


@pytest.mark.asyncio
async def test_github_app_callback_rejects_invalid_state_before_provider_call(monkeypatch: pytest.MonkeyPatch) -> None:
    github_provider = FakeGitHubProvider()
    monkeypatch.setattr(service_module, "get_settings", _settings)

    service = ConnectedAccountsInternalService(
        repository=FakeRepository(),  # type: ignore[arg-type]
        github_provider=github_provider,  # type: ignore[arg-type]
        cloudflare_provider=FakeCloudflareProvider(),  # type: ignore[arg-type]
    )

    with pytest.raises(ProviderOAuthFailedError):
        await service.handle_provider_callback(
            FakeDb(),  # type: ignore[arg-type]
            user_id="user_1",
            provider="github",
            code=None,
            state="ca.github.other_user.bad",
            installation_id="98765",
            error=None,
            error_description=None,
        )

    assert github_provider.validated_installation_id is None


@pytest.mark.asyncio
async def test_github_app_callback_requires_numeric_installation_id() -> None:
    service = ConnectedAccountsInternalService(
        repository=FakeRepository(),  # type: ignore[arg-type]
        github_provider=FakeGitHubProvider(),  # type: ignore[arg-type]
        cloudflare_provider=FakeCloudflareProvider(),  # type: ignore[arg-type]
    )
    state = ConnectedAccountInstallState.new_state(user_id="user_1", provider="github")

    with pytest.raises(ProviderOAuthFailedError):
        await service.handle_provider_callback(
            FakeDb(),  # type: ignore[arg-type]
            user_id="user_1",
            provider="github",
            code=None,
            state=state,
            installation_id=None,
            error=None,
            error_description=None,
        )

    with pytest.raises(ProviderOAuthFailedError):
        await service.handle_provider_callback(
            FakeDb(),  # type: ignore[arg-type]
            user_id="user_1",
            provider="github",
            code=None,
            state=state,
            installation_id="not_numeric",
            error=None,
            error_description=None,
        )


@pytest.mark.asyncio
async def test_cloudflare_callback_keeps_legacy_oauth_code_path() -> None:
    repository = FakeRepository()
    service = ConnectedAccountsInternalService(
        repository=repository,  # type: ignore[arg-type]
        github_provider=FakeGitHubProvider(),  # type: ignore[arg-type]
        cloudflare_provider=FakeCloudflareProvider(),  # type: ignore[arg-type]
    )
    state = ConnectedAccountOAuthState.new_state(user_id="user_1", provider="cloudflare")

    result = await service.handle_provider_callback(
        FakeDb(),  # type: ignore[arg-type]
        user_id="user_1",
        provider="cloudflare",
        code="provider_auth_code",
        state=state,
        installation_id=None,
        error=None,
        error_description=None,
    )

    assert result.provider == "cloudflare"
    assert result.connected is True
    assert repository.records[("user_1", "cloudflare")].provider_account_name == "cloudflare-tester"
