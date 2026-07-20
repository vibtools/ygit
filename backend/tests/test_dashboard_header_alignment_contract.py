from pathlib import Path


HTML = Path("frontend/dashboard/index.html")
APP = Path("frontend/dashboard/assets/app.js")
CSS = Path("frontend/dashboard/assets/brand-lock.css")


def test_header_uses_notifications_workspace_dropdown_and_profile() -> None:
    html = HTML.read_text(encoding="utf-8")

    assert 'class="search"' in html
    assert 'id="notifications-button"' in html
    assert 'class="workspace-switcher"' in html
    assert "<select>" in html
    assert "VibTools" in html
    assert 'id="new-project-button"' in html
    assert 'class="profile-button"' in html
    assert ">Workspace</button>" not in html


def test_header_alignment_css_is_compact_and_ordered() -> None:
    css = CSS.read_text(encoding="utf-8")

    assert "Step 27C header alignment polish" in css
    assert "grid-template-columns: 320px 40px minmax(148px, auto) auto 40px" in css
    assert "width: 320px" in css
    assert ".workspace-switcher" in css
    assert ".profile-button" in css


def test_notifications_listener_does_not_depend_on_removed_theme_toggle() -> None:
    app = APP.read_text(encoding="utf-8")

    assert "notificationsButton" in app
    assert "No new notifications." in app
    assert "const themeToggle = $(\"#theme-toggle\");" in app or "$(\"#theme-toggle\")" not in app
