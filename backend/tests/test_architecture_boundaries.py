from pathlib import Path

def test_no_forbidden_direct_provider_imports_in_routes() -> None:
    route_dir = Path("backend/app/routes")
    route_sources = "\n".join(path.read_text() for path in route_dir.glob("*.py"))
    assert "providers.github_provider" not in route_sources
    assert "providers.cloudflare_provider" not in route_sources

def test_shared_layer_has_no_business_logic_directories() -> None:
    shared_dir = Path("backend/shared")
    forbidden = {"project_logic", "deploy_logic", "provider_logic", "business_rules", "repository_analysis_rules"}
    existing = {path.name for path in shared_dir.iterdir() if path.is_dir()}
    assert forbidden.isdisjoint(existing)
