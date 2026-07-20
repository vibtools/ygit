from pathlib import Path


CSS = Path("frontend/dashboard/assets/brand-lock.css")


def test_dashboard_cards_have_gradient_border_and_hover_lift() -> None:
    css = CSS.read_text(encoding="utf-8")

    assert "Step 27C-2S1 card surface polish" in css
    assert "linear-gradient(" in css
    assert "rgba(255,255,255,.03)" in css
    assert "rgba(255,255,255,.01)" in css
    assert "border: 1px solid rgba(255,255,255,.06)" in css
    assert "transform: translateY(-2px)" in css
    assert ".panel" in css
    assert ".metric-card" in css
    assert ".list-item" in css
