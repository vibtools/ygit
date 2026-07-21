from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from backend.engines.auth_engine.connected_accounts_module.internal.service import (
    ConnectedAccountsInternalService,
)
from backend.engines.auth_engine.connected_accounts_module.schemas import (
    ConnectedAccountRecord,
)


NOW = datetime.now(timezone.utc)


def test_connected_account_summary_exposes_safe_ui_metadata() -> None:
    service = object.__new__(
        ConnectedAccountsInternalService
    )
    record = ConnectedAccountRecord(
        id="account-1",
        user_id="user-1",
        provider="github",
        status="connected",
        provider_account_id="installation-1",
        provider_account_name="vibtools",
        token_secret_ref=(
            "github_app_installation:installation-1"
        ),
        scopes=[
            "github_app:installation",
            "repositories:selected",
        ],
        last_checked_at=NOW,
        connected_at=NOW,
    )

    summary = service.to_summary(
        record,
        provider="github",
    )

    assert summary.connected is True
    assert summary.account_name == "vibtools"
    assert summary.connected_at == NOW
    assert summary.last_checked_at == NOW
    assert summary.scopes == [
        "github_app:installation",
        "repositories:selected",
    ]

    serialized = summary.model_dump_json()
    assert "token_secret_ref" not in serialized
    assert "installation-1" not in serialized


def test_disconnected_summary_does_not_expose_stale_metadata() -> None:
    service = object.__new__(
        ConnectedAccountsInternalService
    )
    record = ConnectedAccountRecord(
        id="account-1",
        user_id="user-1",
        provider="github",
        status="disconnected",
        provider_account_name="vibtools",
        scopes=["repositories:selected"],
        last_checked_at=NOW,
        connected_at=NOW,
    )

    summary = service.to_summary(
        record,
        provider="github",
    )

    assert summary.connected is False
    assert summary.account_name is None
    assert summary.connected_at is None
    assert summary.last_checked_at is None
    assert summary.scopes == []


def test_dashboard_connected_accounts_metadata_source_contract() -> None:
    index = Path(
        "frontend/dashboard/index.html"
    ).read_text(encoding="utf-8")
    app = Path(
        "frontend/dashboard/assets/app.js"
    ).read_text(encoding="utf-8")
    styles = Path(
        "frontend/dashboard/assets/styles.css"
    ).read_text(encoding="utf-8")

    for marker in (
        'data-view-panel="github-repositories"',
        'id="github-repository-list"',
        "Imported GitHub repositories",
    ):
        assert marker in index

    for marker in (
        "function providerAvatar(",
        "function formatRelativeTime(",
        "function githubImportedRepositories(",
        "data-view-github-repositories",
        "data-use-repository-url",
        "Use this repository",
        "Connection date",
        "Last sync",
        "Scopes",
        "Status: Connected",
        'aria-label="${escapeHtml(statusCopy)}"',
    ):
        assert marker in app

    for marker in (
        "YGIT_CONNECTED_ACCOUNTS_METADATA_UI_START",
        ".provider-avatar",
        ".account-status-badge",
        ".scope-chip",
        ".repository-browser-card",
    ):
        assert marker in styles


def test_repository_browser_uses_imported_projects_without_provider_call() -> None:
    app = Path(
        "frontend/dashboard/assets/app.js"
    ).read_text(encoding="utf-8")

    assert "githubImportedRepositories" in app
    assert "state.projects.forEach" in app
    assert 'fetchJson("/github' not in app
    assert "installation/access_tokens" not in app
    assert "access_token" not in app
    assert "5 min ago" not in app
