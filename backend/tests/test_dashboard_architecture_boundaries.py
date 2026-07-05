from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_dashboard_static_files_do_not_import_backend_modules() -> None:
    dashboard_root = ROOT / "frontend" / "dashboard"
    forbidden = [
        "backend/",
        "engines/",
        "providers/",
        "sqlalchemy",
        "cloudflare_provider",
        "github_provider",
        "deployment_history_engine",
        "deploy_engine",
    ]
    for path in dashboard_root.rglob("*"):
        if path.is_file() and path.suffix in {".html", ".css", ".js"}:
            text = path.read_text(encoding="utf-8")
            for token in forbidden:
                assert token not in text, f"{path} contains forbidden backend/provider token {token}"


def test_dashboard_route_does_not_import_engines_or_providers() -> None:
    route_path = ROOT / "backend" / "app" / "routes" / "dashboard_routes.py"
    text = route_path.read_text(encoding="utf-8")
    forbidden = [
        "backend.engines",
        "backend.providers",
        "backend.core.database",
        "DeployService",
        "ProjectService",
    ]
    for token in forbidden:
        assert token not in text
