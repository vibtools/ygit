from __future__ import annotations

from types import SimpleNamespace

import pytest
from pydantic import SecretStr

from backend.engines.auth_engine.connected_accounts_module.internal import (
    service as service_module,
)
from backend.engines.auth_engine.connected_accounts_module.internal.oauth_state import (
    ConnectedAccountInstallState,
)
from backend.engines.auth_engine.connected_accounts_module.internal.service import (
    ConnectedAccountsInternalService,
)
from backend.providers.github_provider.client import GitHubProviderClient
from backend.providers.github_provider.schemas import GitHubAppInstallation


class FakeGitHubProvider:
    def __init__(
        self,
        permissions: dict[str, str],
    ) -> None:
        self.permissions = permissions

    def create_app_jwt(
        self,
        *,
        app_id: str,
        private_key_pem: str,
    ) -> str:
        assert app_id == "123"
        assert private_key_pem == "test-private-key"
        return "safe-app-jwt-reference"

    async def get_app_installation(
        self,
        *,
        installation_id: int | str,
        app_jwt: str,
    ) -> GitHubAppInstallation:
        assert str(installation_id) == "456"
        assert app_jwt == "safe-app-jwt-reference"
        return GitHubAppInstallation(
            installation_id=456,
            account_id="789",
            account_login="vibtools",
            repository_selection="selected",
            permissions=self.permissions,
        )


class FakeRepository:
    def __init__(self) -> None:
        self.upsert_payload: dict[str, object] | None = None

    async def upsert_connected(
        self,
        db,
        **kwargs,
    ):
        self.upsert_payload = kwargs
        return SimpleNamespace(
            provider="github",
            status="connected",
            provider_account_name="vibtools",
        )


class FakeDb:
    def __init__(self) -> None:
        self.committed = False

    async def commit(self) -> None:
        self.committed = True


def test_installation_schema_defaults_permissions_to_empty_map() -> None:
    installation = GitHubAppInstallation(
        installation_id=1,
        account_id="2",
        account_login="example",
    )

    assert installation.permissions == {}


def test_installation_payload_captures_actual_permissions() -> None:
    installation = GitHubProviderClient()._installation_from_payload(
        {
            "id": 1,
            "account": {
                "id": 2,
                "login": "example",
            },
            "repository_selection": "selected",
            "permissions": {
                "metadata": "read",
                "contents": "read",
                "actions": "write",
            },
        }
    )

    assert installation.permissions == {
        "metadata": "read",
        "contents": "read",
        "actions": "write",
    }


def test_installation_payload_ignores_null_permission_entries() -> None:
    installation = GitHubProviderClient()._installation_from_payload(
        {
            "id": 1,
            "account": {
                "id": 2,
                "login": "example",
            },
            "permissions": {
                "metadata": "read",
                "contents": None,
                None: "write",
            },
        }
    )

    assert installation.permissions == {
        "metadata": "read",
    }


def test_installation_payload_normalizes_permission_values() -> None:
    installation = GitHubProviderClient()._installation_from_payload(
        {
            "id": 1,
            "account": {
                "id": 2,
                "login": "example",
            },
            "permissions": {
                "metadata": "read",
                "contents": "write",
            },
        }
    )

    assert all(
        isinstance(name, str)
        and isinstance(access, str)
        for name, access
        in installation.permissions.items()
    )


@pytest.mark.asyncio
async def test_callback_persists_sorted_permission_scopes(
    monkeypatch,
) -> None:
    repository = FakeRepository()
    provider = FakeGitHubProvider(
        {
            "metadata": "read",
            "contents": "read",
            "actions": "write",
        }
    )
    db = FakeDb()

    monkeypatch.setattr(
        service_module,
        "get_settings",
        lambda: SimpleNamespace(
            github_app_id="123",
            github_app_private_key=SecretStr(
                "test-private-key"
            ),
        ),
    )
    monkeypatch.setattr(
        ConnectedAccountInstallState,
        "validate_state",
        staticmethod(lambda **_: True),
    )

    service = ConnectedAccountsInternalService(
        repository=repository,
        github_provider=provider,
    )

    result = await service._handle_github_app_callback(
        db,
        user_id="user_1",
        state="valid-state",
        installation_id="456",
    )

    assert result.connected is True
    assert db.committed is True
    assert repository.upsert_payload is not None
    assert repository.upsert_payload["scopes"] == [
        "github_app:installation",
        "repositories:selected",
        "actions:write",
        "contents:read",
        "metadata:read",
    ]


@pytest.mark.asyncio
async def test_callback_ignores_non_read_write_access_levels(
    monkeypatch,
) -> None:
    repository = FakeRepository()
    provider = FakeGitHubProvider(
        {
            "metadata": "read",
            "contents": "read",
            "issues": "none",
            "pull_requests": "unknown",
        }
    )
    db = FakeDb()

    monkeypatch.setattr(
        service_module,
        "get_settings",
        lambda: SimpleNamespace(
            github_app_id="123",
            github_app_private_key=SecretStr(
                "test-private-key"
            ),
        ),
    )
    monkeypatch.setattr(
        ConnectedAccountInstallState,
        "validate_state",
        staticmethod(lambda **_: True),
    )

    service = ConnectedAccountsInternalService(
        repository=repository,
        github_provider=provider,
    )

    await service._handle_github_app_callback(
        db,
        user_id="user_1",
        state="valid-state",
        installation_id="456",
    )

    assert repository.upsert_payload is not None
    scopes = repository.upsert_payload["scopes"]
    assert "metadata:read" in scopes
    assert "contents:read" in scopes
    assert "issues:none" not in scopes
    assert "pull_requests:unknown" not in scopes


def test_permission_capture_spec_locks_scope_boundary() -> None:
    from pathlib import Path

    source = Path(
        "GITHUB_APP_PERMISSION_CAPTURE_SPEC.md"
    ).read_text(encoding="utf-8")

    assert "metadata:read" in source
    assert "contents:read" in source
    assert "does not" in source
    assert "request additional permissions" in source
    assert "later independent UI patch" in source
