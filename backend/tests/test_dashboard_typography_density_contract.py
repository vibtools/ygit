from pathlib import Path


CSS = Path("frontend/dashboard/assets/brand-lock.css")


def test_sidebar_width_and_logo_density_are_brand_locked() -> None:
    css = CSS.read_text(encoding="utf-8")

    assert "--ygit-sidebar-width: 240px" in css
    assert "width: var(--ygit-sidebar-width)" in css
    assert "flex: 0 0 var(--ygit-sidebar-width)" in css
    assert "height: 30px" in css
    assert "width: 130px" in css


def test_typography_density_tokens_match_ygit_ui_lock() -> None:
    css = CSS.read_text(encoding="utf-8")

    assert "--ygit-page-h1: 28px" in css
    assert "--ygit-page-h2: 20px" in css
    assert "--ygit-description: 14px" in css
    assert "--ygit-card-title: 15px" in css
    assert "--ygit-card-body: 13px" in css
    assert "--ygit-meta: 12px" in css


def test_sidebar_typography_is_compact_and_professional() -> None:
    css = CSS.read_text(encoding="utf-8")

    assert ".brand-title" in css
    assert "font-size: 14px" in css
    assert "font-weight: 600" in css
    assert ".nav a" in css
    assert "font-weight: 500" in css
    assert "text-transform: uppercase" in css


def test_spacing_and_controls_are_more_dense() -> None:
    css = CSS.read_text(encoding="utf-8")

    assert "gap: 14px" in css
    assert "padding: 13px" in css
    assert "min-height: 38px" in css
    assert "height: 38px" in css
