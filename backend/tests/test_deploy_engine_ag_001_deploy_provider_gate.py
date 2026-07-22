from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from backend.engines.deploy_engine.extension_gates.ag_001_deploy_provider_gate import (
    AG_001_GATE_ID,
    AG_001_PHASE,
    DEFAULT_DEPLOY_PROVIDER,
    DeployProviderGateDecision,
    DeployProviderGateResolutionError,
    resolve_deploy_provider,
)


def test_ag_001_defaults_to_cloudflare_without_build_target(
) -> None:
    decision = resolve_deploy_provider()

    assert decision == DeployProviderGateDecision(
        gate_id="AG-001",
        phase="before_deploy_completion",
        provider="cloudflare",
        build_target=None,
        resolution_source="default",
    )
    assert (
        decision.provider
        == DEFAULT_DEPLOY_PROVIDER
    )


@pytest.mark.parametrize(
    "build_target",
    [
        "",
        "   ",
        None,
    ],
)
def test_ag_001_blank_target_keeps_cloudflare_default(
    build_target,
) -> None:
    decision = resolve_deploy_provider(
        build_target
    )

    assert decision.provider == "cloudflare"
    assert decision.build_target is None
    assert (
        decision.resolution_source
        == "default"
    )


def test_ag_001_explicit_cloudflare_uses_core_resolution(
) -> None:
    decision = resolve_deploy_provider(
        "  CLOUDFLARE  "
    )

    assert decision.provider == "cloudflare"
    assert decision.build_target == "cloudflare"
    assert decision.resolution_source == "core"


def test_ag_001_custom_target_uses_injected_extension_resolver(
) -> None:
    received: list[str] = []

    def resolver(
        build_target: str,
    ) -> str:
        received.append(build_target)
        return "  example-provider  "

    decision = resolve_deploy_provider(
        "  Example-Target  ",
        resolver=resolver,
    )

    assert received == ["example-target"]
    assert (
        decision.provider
        == "example-provider"
    )
    assert (
        decision.build_target
        == "example-target"
    )
    assert (
        decision.resolution_source
        == "extension"
    )


def test_ag_001_custom_target_without_resolver_fails_closed(
) -> None:
    with pytest.raises(
        DeployProviderGateResolutionError,
        match=(
            "Deploy provider could not "
            "be resolved"
        ),
    ) as raised:
        resolve_deploy_provider(
            "future-target"
        )

    assert (
        raised.value.build_target
        == "future-target"
    )


@pytest.mark.parametrize(
    "resolver",
    [
        lambda value: None,
        lambda value: "",
        lambda value: "   ",
    ],
)
def test_ag_001_blank_extension_resolution_fails_closed(
    resolver,
) -> None:
    with pytest.raises(
        DeployProviderGateResolutionError
    ):
        resolve_deploy_provider(
            "future-target",
            resolver=resolver,
        )


def test_ag_001_resolver_exception_is_sanitized(
) -> None:
    def resolver(
        build_target: str,
    ) -> str:
        _ = build_target
        raise RuntimeError(
            "extension-internal-detail"
        )

    with pytest.raises(
        DeployProviderGateResolutionError
    ) as raised:
        resolve_deploy_provider(
            "future-target",
            resolver=resolver,
        )

    assert (
        "extension-internal-detail"
        not in str(raised.value)
    )
    assert raised.value.__cause__ is None


def test_ag_001_decision_is_immutable(
) -> None:
    decision = resolve_deploy_provider()

    with pytest.raises(
        FrozenInstanceError
    ):
        decision.provider = "changed"


def test_ag_001_contract_constants_are_exact(
) -> None:
    assert AG_001_GATE_ID == "AG-001"
    assert (
        AG_001_PHASE
        == "before_deploy_completion"
    )
    assert (
        DEFAULT_DEPLOY_PROVIDER
        == "cloudflare"
    )


def test_ag_001_source_preserves_engine_boundaries(
) -> None:
    source = Path(
        "backend/engines/deploy_engine/"
        "extension_gates/"
        "ag_001_deploy_provider_gate.py"
    ).read_text(
        encoding="utf-8"
    )

    for forbidden in (
        "backend.providers",
        "backend.pipelines",
        "backend.workers",
        "sqlalchemy",
        "get_settings(",
        "os.getenv(",
        "create_pages_deployment",
        "deployment_history",
        "AppEngine",
        "app_engine",
    ):
        assert forbidden not in source


def test_ag_001_document_records_runtime_boundary(
) -> None:
    document = Path(
        "backend/engines/deploy_engine/"
        "extension_gates/"
        "AG_001_DEPLOY_PROVIDER_GATE.md"
    ).read_text(
        encoding="utf-8"
    )

    assert (
        "Default provider: cloudflare"
        in document
    )
    assert (
        "The gate itself never performs deployment."
        in document
    )
    assert (
        "Current Deploy Engine flow: unchanged"
        in document
    )
    assert (
        "YGIT App Engine: not created"
        in document
    )
