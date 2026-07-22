from pathlib import Path


HTML = Path("frontend/dashboard/index.html")
APP = Path("frontend/dashboard/assets/app.js")
CSS = Path("frontend/dashboard/assets/brand-lock.css")
BRAND = Path("frontend/dashboard/assets/brand")


def test_dashboard_loads_brand_lock_css_and_original_logo_assets() -> None:
    html = HTML.read_text(encoding="utf-8")

    assert "/dashboard/assets/brand-lock.css" in html
    assert "/dashboard/assets/brand/favicon.svg" in html
    assert "/dashboard/assets/brand/YGIT-Logo-For-Dark-Themes.png" in html
    assert (BRAND / "YGIT-Logo-For-Dark-Themes.png").exists()
    assert (BRAND / "YGIT_Icon.png").exists()
    assert (BRAND / "favicon.svg").exists()


def test_brand_lock_uses_compact_vibtools_ecosystem_tokens() -> None:
    css = CSS.read_text(encoding="utf-8").lower()

    assert "--ygit-primary: #2563eb" in css
    assert "--ygit-accent: #38bdf8" in css
    assert "--ygit-bg: #030712" in css
    assert "--ygit-card: #111827" in css
    assert "font-size: 20px" in css
    assert "font-size: 13px" in css
    assert "box-shadow: none" in css
    assert "0 1px 2px" in css


def test_project_cards_use_server_authoritative_deploy_review() -> None:
    app = APP.read_text(encoding="utf-8")
    card = app.split(
        "function projectCard(project) {",
        1,
    )[1].split(
        "function emptyProjectState() {",
        1,
    )[0]

    compact = " ".join(card.split())

    assert "function isProjectDeployReady(project)" in app
    assert 'project?.status === "deploy_ready"' in app
    assert 'const deployLabel = deployReady ? "Deploy" : "Review & Deploy";' in compact
    assert 'disabled aria-disabled="true"' not in card
    assert "Deploy locked" not in card
    assert "$$('[data-deploy-project]')" in app
    assert "loadProjectDeployReadiness(" in app


def test_dashboard_maps_deployment_errors_to_safe_messages() -> None:
    app = APP.read_text(encoding="utf-8")

    assert "function friendlyErrorMessage(error)" in app
    assert "DEPLOYMENT_PROJECT_NOT_READY" in app
    assert "DEPLOYMENT_ANALYSIS_REQUIRED" in app
    assert "DEPLOYMENT_GITHUB_NOT_CONNECTED" in app
    assert "DEPLOYMENT_CLOUDFLARE_NOT_CONNECTED" in app
    assert "Review the current deployment blockers" in app
    assert "showSystemAlert(error, \"warning\")" in app


def test_timeline_separates_analysis_ready_from_deploy_ready() -> None:
    app = APP.read_text(encoding="utf-8")

    assert "const hasAnalysis" in app
    assert "const hasDeployReady" in app
    assert "Analysis completed" in app
    assert "Deploy ready" in app
