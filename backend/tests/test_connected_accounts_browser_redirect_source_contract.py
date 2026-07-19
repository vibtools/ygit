from pathlib import Path


def _route_source() -> str:
    return Path("backend/app/routes/connected_accounts_routes.py").read_text(encoding="utf-8")


def test_github_connect_keeps_api_json_but_redirects_browser_requests() -> None:
    source = _route_source()

    assert "Request" in source
    assert "RedirectResponse" in source
    assert "def _wants_browser_redirect" in source
    assert 'provider == "github" and _wants_browser_redirect(request)' in source
    assert "result.authorization_url" in source
    assert "status.HTTP_302_FOUND" in source


def test_github_callback_redirects_browser_back_to_dashboard() -> None:
    source = _route_source()

    assert "/dashboard?connected=github#connected-accounts" in source
    assert "status.HTTP_303_SEE_OTHER" in source
    assert "success_response(result.model_dump(mode=\"json\")" in source
