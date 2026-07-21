from pathlib import Path


INDEX = Path(
    "frontend/dashboard/index.html"
).read_text(encoding="utf-8")

APP = Path(
    "frontend/dashboard/assets/app.js"
).read_text(encoding="utf-8")

CSS = Path(
    "frontend/dashboard/assets/brand-lock.css"
).read_text(encoding="utf-8")


METRICS = {
    "Projects": "metric-projects",
    "Deployments": "metric-deployments",
    "Deploy Success %": "metric-success-rate",
    "Connected Accounts": "metric-accounts",
    "Live Sites": "metric-live-sites",
    "Last Deployment": "metric-last-deployment",
    "Framework Usage": "metric-framework-usage",
    "Platform Status": "metric-platform-status",
    "Queue Status": "metric-queue-status",
}


def test_dashboard_operational_metrics_have_stable_markup() -> None:
    assert "data-dashboard-metrics" in INDEX
    assert 'aria-label="Dashboard operational metrics"' in INDEX

    for label, metric_id in METRICS.items():
        assert label in INDEX
        assert INDEX.count(f'id="{metric_id}"') == 1
        assert f'data-dashboard-metric=' in INDEX

    assert "Success Rate</span>" not in INDEX


def test_dashboard_operational_metrics_use_loaded_state() -> None:
    required_tokens = (
        "function latestDeploymentMetric()",
        "function frameworkUsageMetric()",
        "function platformStatusMetric()",
        "function queueStatusMetric()",
        "function setDashboardMetric(",
        "state.projects",
        "state.deployments",
        "state.accounts",
        "state.status",
        "terminalCount",
        "metric-last-deployment",
        "metric-framework-usage",
        "metric-platform-status",
        "metric-queue-status",
    )

    for token in required_tokens:
        assert token in APP

    assert '"+0 this week"' not in APP


def test_dashboard_operational_metric_layout_is_responsive() -> None:
    assert "Step 31A dashboard operational metrics" in CSS
    assert "minmax(190px, 1fr)" in CSS
    assert ".dashboard-metric-card" in CSS
    assert ".dashboard-metric-value.is-warning" in CSS
    assert ".dashboard-metric-value.is-error" in CSS
    assert "@media (max-width: 520px)" in CSS
