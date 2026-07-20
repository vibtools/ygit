from pathlib import Path


CSS = Path("frontend/dashboard/assets/brand-lock.css")


def test_dashboard_color_system_tokens_are_locked() -> None:
    css = CSS.read_text(encoding="utf-8")

    assert "Step 27C-2S2 color system polish" in css
    assert "--ygit-primary: #3B82F6" in css
    assert "--ygit-success: #10B981" in css
    assert "--ygit-warning: #F59E0B" in css
    assert "--ygit-error: #EF4444" in css
    assert "--ygit-muted: #94A3B8" in css
    assert "--ygit-bg: #020817" in css
    assert "--ygit-surface: #081121" in css


def test_dashboard_color_system_applies_to_core_ui_states() -> None:
    css = CSS.read_text(encoding="utf-8")

    assert ".primary-button" in css
    assert ".pill.success" in css
    assert ".pill.warning" in css
    assert ".pill.danger" in css
    assert "body" in css
    assert ".timeline-copy span" in css
