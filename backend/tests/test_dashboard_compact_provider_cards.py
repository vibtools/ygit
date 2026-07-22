from pathlib import Path


HTML = Path("frontend/dashboard/index.html")
APP = Path("frontend/dashboard/assets/app.js")
CSS = Path("frontend/dashboard/assets/styles.css")
SPEC = Path("DASHBOARD_COMPACT_PROVIDER_CARDS_SPEC.md")


def test_compact_provider_slot_is_inside_dashboard_hero() -> None:
    html = HTML.read_text(encoding="utf-8")
    hero = html.split(
        '<div class="hero-card dashboard-hero-card">',
        1,
    )[1].split(
        '<aside class="timeline"',
        1,
    )[0]

    assert 'id="dashboard-account-grid"' in hero
    assert 'class="dashboard-account-strip"' in hero
    assert hero.index("hero-actions") < hero.index(
        "dashboard-account-strip"
    )


def test_obsolete_narrow_provider_panel_is_removed_only_from_dashboard() -> None:
    html = HTML.read_text(encoding="utf-8")
    dashboard = html.split(
        '<section class="view" data-view-panel="dashboard">',
        1,
    )[1].split(
        '<section class="view hidden" data-view-panel="projects">',
        1,
    )[0]

    assert "Provider readiness" not in dashboard
    assert 'id="connected-account-grid"' in html
    assert 'data-view-panel="connected-accounts"' in html


def test_dashboard_uses_dedicated_compact_renderer() -> None:
    source = APP.read_text(encoding="utf-8")
    compact = "".join(source.split())

    assert "function dashboardAccountCard(provider)" in source
    assert (
        'constdashboardHtml=["github","cloudflare"]'
        '.map(dashboardAccountCard).join("");'
        in compact
    )
    assert (
        '$("#connected-account-grid").innerHTML=fullHtml;'
        in compact
    )


def test_github_card_contains_only_requested_fields() -> None:
    source = APP.read_text(encoding="utf-8")
    renderer = source.split(
        "function dashboardAccountCard(provider) {",
        1,
    )[1].split(
        "function accountCard(provider) {",
        1,
    )[0]

    for marker in (
        '"Username"',
        '"Repository Access"',
        '"Scopes"',
        '"Last Sync"',
        "Manage",
    ):
        assert marker in renderer

    assert "repositories:" in renderer


def test_cloudflare_card_contains_only_requested_fields() -> None:
    source = APP.read_text(encoding="utf-8")
    renderer = source.split(
        "function dashboardAccountCard(provider) {",
        1,
    )[1].split(
        "function accountCard(provider) {",
        1,
    )[0]

    for marker in (
        '"Account"',
        '"Token Status"',
        '"Permissions"',
        '"Last Sync"',
        "Manage",
    ):
        assert marker in renderer


def test_dashboard_cards_use_safe_existing_account_data_only() -> None:
    source = APP.read_text(encoding="utf-8")
    renderer = source.split(
        "function dashboardAccountCard(provider) {",
        1,
    )[1].split(
        "function accountCard(provider) {",
        1,
    )[0]

    assert "state.accounts.find(" in renderer
    assert "account?.scopes" in renderer
    assert "account?.last_checked_at" in renderer
    assert "fetchJson(" not in renderer
    assert "token_secret_ref" not in renderer
    assert "access_token" not in renderer
    assert "refresh_token" not in renderer


def test_manage_actions_open_existing_connected_accounts_view() -> None:
    source = APP.read_text(encoding="utf-8")

    assert "data-dashboard-account-manage" in source
    assert (
        'setView("connected-accounts")'
        in source
    )


def test_compact_size_contract_is_locked() -> None:
    css = CSS.read_text(encoding="utf-8")
    compact = " ".join(css.split())

    assert ".dashboard-account-strip" in css
    assert "height: 200px" in compact
    assert "grid-template-columns: repeat(2, minmax(0, 1fr))" in compact
    assert "gap: 22px" in compact
    assert "padding: 20px" in compact
    assert "border-radius: var(--radius)" in compact


def test_desktop_uses_existing_gap_and_responsive_layout_is_safe() -> None:
    css = CSS.read_text(encoding="utf-8")
    compact = " ".join(css.split())

    assert "position: absolute" in compact
    assert "top: calc(100% + 12px)" in compact
    assert "@media (max-width: 1180px)" in css
    assert "position: static" in compact
    assert "@media (max-width: 760px)" in css


def test_spec_locks_non_interference_boundary() -> None:
    source = SPEC.read_text(encoding="utf-8")

    assert "full Connected Accounts page remains unchanged" in source
    assert "must not contribute additional layout height" in source
    assert "Project Open UI" in source
    assert "Project Deploy UI" in source
    assert "No token value is displayed." in source
