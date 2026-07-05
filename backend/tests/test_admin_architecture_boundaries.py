from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_admin_engine_directory_is_not_created() -> None:
    assert not (ROOT / "engines" / "admin_engine").exists()


def test_admin_surface_does_not_import_providers_or_engine_internals() -> None:
    checked_paths = [
        "app/admin_surface/service.py",
        "app/routes/admin_routes.py",
        "app/routes/admin_panel_routes.py",
    ]
    forbidden = [
        "backend.providers.github_provider",
        "backend.providers.cloudflare_provider",
        ".internal",
        "backend.engines.project_engine.repository",
        "backend.engines.deploy_engine.repository",
        "backend.workers.repository",
        "backend.pipelines.deploy_pipeline.internal",
    ]
    for path in checked_paths:
        content = _read(path)
        for marker in forbidden:
            assert marker not in content, f"{path} imported forbidden marker {marker}"


def test_admin_frontend_calls_api_only() -> None:
    js = _read("../frontend/admin/assets/app.js")
    assert 'const API = "/api/v1"' in js
    forbidden = ["backend.", "providers/", "engines/", "postgres", "cloudflare_provider", "github_provider"]
    for marker in forbidden:
        assert marker not in js
