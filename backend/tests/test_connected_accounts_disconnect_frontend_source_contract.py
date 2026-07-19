from pathlib import Path


def _dashboard_app_source() -> str:
    return Path("frontend/dashboard/assets/app.js").read_text(encoding="utf-8")


def _dashboard_css_source() -> str:
    return Path("frontend/dashboard/assets/styles.css").read_text(encoding="utf-8")


def test_connected_accounts_connected_card_has_app_side_disconnect() -> None:
    source = _dashboard_app_source()

    assert 'data-disconnect-provider="${provider}"' in source
    assert "async function disconnectProvider(provider)" in source
    assert 'method: "DELETE"' in source
    assert "window.location.reload()" in source


def test_disconnect_uses_confirmation_and_keeps_provider_management_separate() -> None:
    source = _dashboard_app_source()

    assert "window.confirm" in source
    assert "This removes the YGIT connection only" in source
    assert "It does not uninstall the provider app" in source
    assert "https://github.com/settings/installations" in source
    assert "Manage on GitHub" in source


def test_disconnect_button_has_dashboard_styles() -> None:
    css = _dashboard_css_source()

    assert ".danger-button" in css
    assert ".account-actions" in css
    assert ".provider-manage-link" in css
