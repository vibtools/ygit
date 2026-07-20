from pathlib import Path


def test_sidebar_brand_is_compact_and_original_logo_stays_small() -> None:
    css = Path("frontend/dashboard/assets/brand-lock.css").read_text(encoding="utf-8")

    assert "height: 30px" in css
    assert "min-height: 30px" in css
    assert "width: 130px" in css


def test_sidebar_scrollbar_is_hidden_and_note_is_bottom_aligned() -> None:
    css = Path("frontend/dashboard/assets/brand-lock.css").read_text(encoding="utf-8")

    assert "scrollbar-width: none" in css
    assert "-ms-overflow-style: none" in css
    assert ".sidebar::-webkit-scrollbar" in css
    assert "margin-top: auto" in css
