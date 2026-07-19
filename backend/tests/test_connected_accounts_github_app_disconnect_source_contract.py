from pathlib import Path


def _github_provider_source() -> str:
    return Path("backend/providers/github_provider/client.py").read_text(encoding="utf-8")


def _connected_accounts_service_source() -> str:
    return Path("backend/engines/auth_engine/connected_accounts_module/internal/service.py").read_text(encoding="utf-8")


def test_github_provider_can_delete_app_installation() -> None:
    source = _github_provider_source()

    assert "async def delete_app_installation(" in source
    assert "/app/installations/{installation_id}" in source
    assert "client.delete(url)" in source
    assert "response.status_code in {204, 404}" in source


def test_github_disconnect_uninstalls_installation_before_local_disconnect() -> None:
    source = _connected_accounts_service_source()

    assert "async def _delete_github_app_installation(" in source
    assert 'prefix = "github_app_installation:"' in source
    assert "self.github_provider.create_app_jwt(" in source
    assert "self.github_provider.delete_app_installation(" in source
    assert 'if provider_name == "github":' in source
    assert "await self._delete_github_app_installation(existing_record.token_secret_ref)" in source
    assert "await self.repository.mark_disconnected" in source
