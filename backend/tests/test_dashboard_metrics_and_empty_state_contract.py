from pathlib import Path


APP_JS = Path("frontend/dashboard/assets/app.js")
CSS = Path("frontend/dashboard/assets/brand-lock.css")


def test_dashboard_metrics_contract_is_present() -> None:
    app_js = APP_JS.read_text(encoding="utf-8")

    assert "Step 27C-3B dashboard metrics and deployment empty state" in app_js
    assert "Deploy Success %" in app_js
    assert "Last Deployment" in app_js
    assert "Framework Usage" in app_js
    assert "Platform Status" in app_js
    assert "Queue Status" in app_js


def test_deployment_empty_state_contract_is_present() -> None:
    app_js = APP_JS.read_text(encoding="utf-8")

    assert "No deployments yet." in app_js
    assert "Create a project &rarr; Connect GitHub &rarr; Deploy &rarr; Website Live" in app_js
    assert "deployment-empty-illustration" in app_js


def test_dashboard_metrics_and_empty_state_styles_are_present() -> None:
    css = CSS.read_text(encoding="utf-8")

    assert "Step 27C-3B dashboard metrics and deployment empty state" in css
    assert ".dashboard-metric-card" in css
    assert "transform: translateY(-2px);" in css
    assert ".deployment-empty-state" in css
    assert ".deployment-empty-illustration" in css
    assert ".deployment-empty-check" in css
