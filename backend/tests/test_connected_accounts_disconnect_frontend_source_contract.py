from pathlib import Path


def _dashboard_app_source() -> str:
    return Path("frontend/dashboard/assets/app.js").read_text(encoding="utf-8")


def _dashboard_css_source() -> str:
    return Path("frontend/dashboard/assets/styles.css").read_text(encoding="utf-8")


def _connected_branch(source: str) -> str:
    return source.split("const actions = connected", 1)[1].split(": `<div", 1)[0]


def test_connected_accounts_connected_card_has_single_disconnect_action() -> None:
    source = _dashboard_app_source()
    connected_branch = _connected_branch(source)

    assert 'Status: Connected' in source
    assert 'data-disconnect-provider="${provider}"' in connected_branch
    assert "Disconnect" in connected_branch
    assert "Manage on GitHub" in source
    assert "Reconnect" not in connected_branch


def test_disconnected_card_uses_connect_or_reconnect() -> None:
    source = _dashboard_app_source()

    assert 'const connectLabel = !connected && account ? "Reconnect" : "Connect";' in source
    assert '${connectLabel}' in source


def test_disconnect_confirmation_mentions_github_uninstall() -> None:
    source = _dashboard_app_source()

    assert "window.confirm" in source
    assert "also uninstalls the GitHub App" in source


def test_disconnect_button_has_dashboard_styles() -> None:
    css = _dashboard_css_source()

    assert ".danger-button" in css
    assert ".account-actions" in css
    assert ".provider-manage-link" in css
