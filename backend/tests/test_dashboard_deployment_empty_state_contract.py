from pathlib import Path


INDEX_PATH = Path("frontend/dashboard/index.html")
APP_PATH = Path("frontend/dashboard/assets/app.js")
CSS_PATH = Path("frontend/dashboard/assets/brand-lock.css")


def test_deployment_page_has_guided_empty_state() -> None:
    app = APP_PATH.read_text(encoding="utf-8")

    assert "function deploymentEmptyState()" in app
    assert "No deployments yet." in app
    assert "Create a project" in app
    assert "Connect GitHub" in app
    assert ">Deploy<" in app
    assert "Website Live" in app
    assert "deployment-empty-illustration" in app
    assert "<svg" in app
    assert "No deployment history yet" not in app


def test_deployment_empty_actions_are_runtime_bound() -> None:
    app = APP_PATH.read_text(encoding="utf-8")

    assert 'data-deployment-empty-view="projects"' in app
    assert (
        'data-deployment-empty-view="connected-accounts"'
        in app
    )
    assert (
        'closest("[data-deployment-empty-view]")'
        in app
    )
    assert "setView(targetView)" in app


def test_sidebar_system_card_is_bottom_anchored() -> None:
    index = INDEX_PATH.read_text(encoding="utf-8")
    css = CSS_PATH.read_text(encoding="utf-8")

    assert (
        'class="sidebar-section sidebar-system-section"'
        in index
    )
    assert ".sidebar-system-section" in css
    assert "margin-top: auto !important" in css
    assert "flex-direction: column !important" in css


def test_ui_patch_is_responsive_and_scoped() -> None:
    css = CSS_PATH.read_text(encoding="utf-8")

    marker = (
        "/* Step 38E deployment empty state "
        "and sidebar system placement */"
    )
    assert css.count(marker) == 1

    block = css.split(marker, 1)[1]

    assert "@media (max-width: 1180px)" in block
    assert "@media (max-width: 860px)" in block
    assert ".deployment-empty-layout" in block
    assert ".deployment-empty-flow" in block

    assert ".topbar" not in block
    assert ".primary-button {" not in block
    assert ".status-badge" not in block
