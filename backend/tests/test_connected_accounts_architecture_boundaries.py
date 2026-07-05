from pathlib import Path


def test_connected_accounts_route_does_not_import_provider_directly() -> None:
    source = Path("backend/app/routes/connected_accounts_routes.py").read_text()
    assert "providers.github_provider" not in source
    assert "providers.cloudflare_provider" not in source


def test_connected_accounts_internal_module_stays_under_auth_engine() -> None:
    module_dir = Path("backend/engines/auth_engine/connected_accounts_module")
    assert module_dir.exists()
    assert (module_dir / "public.py").exists()
    assert (module_dir / "internal" / "service.py").exists()


def test_connected_accounts_migration_exists() -> None:
    assert Path("backend/migrations/versions/0005_connected_accounts_module.py").exists()
