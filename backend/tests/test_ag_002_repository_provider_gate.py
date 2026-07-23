from __future__ import annotations

from pathlib import Path

import pytest

from backend.engines.repository_engine.repository_provider_gate import (
    DEFAULT_REPOSITORY_PROVIDER,
    resolve_repository_provider,
)


def test_missing_provider_defaults_to_github() -> None:
    assert resolve_repository_provider(None) == DEFAULT_REPOSITORY_PROVIDER


def test_empty_provider_defaults_to_github() -> None:
    assert resolve_repository_provider("") == DEFAULT_REPOSITORY_PROVIDER


def test_whitespace_provider_defaults_to_github() -> None:
    assert resolve_repository_provider("   ") == DEFAULT_REPOSITORY_PROVIDER


@pytest.mark.parametrize(
    "provider",
    ["github", "gitlab", "bitbucket", "azure_devops"],
)
def test_explicit_provider_remains_selected(provider: str) -> None:
    assert resolve_repository_provider(provider) == provider


def test_gate_has_no_provider_database_worker_or_pipeline_dependency() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "engines"
        / "repository_engine"
        / "repository_provider_gate.py"
    )
    source = module_path.read_text(encoding="utf-8")
    forbidden_imports = (
        "backend.providers",
        "sqlalchemy",
        "backend.worker",
        "backend.pipelines",
        "httpx",
    )
    for forbidden_import in forbidden_imports:
        assert forbidden_import not in source


def test_current_repository_service_is_not_runtime_wired_to_ag002() -> None:
    service_path = (
        Path(__file__).resolve().parents[1]
        / "engines"
        / "repository_engine"
        / "internal"
        / "service.py"
    )
    source = service_path.read_text(encoding="utf-8")
    assert "repository_provider_gate" not in source
    assert "GitHubProviderClient" in source
