from pathlib import Path


CSS_PATH = Path(
    "frontend/dashboard/assets/brand-lock.css"
)
MARKER = "/* Step 38C UI title weight refinement */"


def title_weight_block() -> str:
    css = CSS_PATH.read_text(encoding="utf-8")
    assert css.count(MARKER) == 1
    return css.split(MARKER, 1)[1]


def test_dashboard_title_weight_scale_is_professional() -> None:
    block = title_weight_block()

    assert "--ygit-title-weight-xl: 520" in block
    assert "--ygit-title-weight-lg: 500" in block
    assert "--ygit-title-weight-md: 500" in block
    assert "--ygit-title-weight-label: 450" in block

    assert "font-weight: 600" not in block
    assert "font-weight: 650" not in block
    assert "font-weight: 670" not in block
    assert "font-weight: 700" not in block
    assert "font-weight: 720" not in block


def test_dashboard_title_selectors_use_refined_weights() -> None:
    block = title_weight_block()

    assert "#view-title" in block
    assert ".page-title" in block
    assert ".view h1" in block
    assert "var(--ygit-title-weight-xl)" in block

    assert ".hero-card h2" in block
    assert ".panel h2" in block
    assert "var(--ygit-title-weight-lg)" in block

    assert ".timeline h3" in block
    assert ".deployment-empty-copy h3" in block
    assert "var(--ygit-title-weight-md)" in block

    assert ".sidebar-section > p" in block
    assert ".eyebrow" in block
    assert "var(--ygit-title-weight-label)" in block


def test_dashboard_controls_are_not_reweighted() -> None:
    block = title_weight_block()

    assert ".primary-button" not in block
    assert ".secondary-button" not in block
    assert ".danger-button" not in block
    assert ".status-badge" not in block
