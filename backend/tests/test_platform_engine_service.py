from __future__ import annotations

import pytest

from backend.engines.platform_engine.public import platform_service


@pytest.mark.asyncio
async def test_platform_service_version_contract() -> None:
    version = await platform_service.get_version()
    assert version.app == "ygit"
    assert version.api_contract == "1.0"
    assert version.engine_contract == "1.0"
    assert version.database_architecture == "1.0"
    assert version.architecture_freeze == "1.1"
    assert version.platform_engine == "0.1.0"


@pytest.mark.asyncio
async def test_platform_service_feature_flags_are_safe_defaults() -> None:
    flags = await platform_service.get_feature_flags()
    assert flags.flags["templates_beta"] is True
    assert flags.flags["marketplace_preview"] is False
    assert flags.flags["ai_builder_preview"] is False
    assert all("token" not in item.model_dump_json().lower() for item in flags.items)


@pytest.mark.asyncio
async def test_platform_service_settings_summary_is_secret_safe() -> None:
    settings = await platform_service.get_settings_summary()
    payload = settings.model_dump_json().lower()
    assert settings.registration_enabled is True
    assert settings.allowed_repository_providers == ["github"]
    assert settings.allowed_deployment_providers == ["cloudflare"]
    assert "token" not in payload
    assert "password" not in payload
    assert "environment / secret store" in payload
