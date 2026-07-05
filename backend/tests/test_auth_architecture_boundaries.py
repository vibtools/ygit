from pathlib import Path


def test_non_auth_layers_do_not_import_auth_internal_modules() -> None:
    roots = [Path("backend/app"), Path("backend/workers"), Path("backend/pipelines"), Path("backend/providers")]
    sources = "\n".join(path.read_text() for root in roots for path in root.rglob("*.py"))
    assert "backend.engines.auth_engine.internal" not in sources
    assert "backend.engines.auth_engine.repository" not in sources
    assert "backend.engines.auth_engine.models" not in sources


def test_auth_engine_public_api_exists() -> None:
    public_file = Path("backend/engines/auth_engine/public.py")
    assert public_file.exists()
    content = public_file.read_text()
    assert "class AuthPublicService" in content
    assert "auth_service" in content
