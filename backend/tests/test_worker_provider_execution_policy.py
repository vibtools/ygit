from __future__ import annotations

from dataclasses import FrozenInstanceError
from inspect import signature
from pathlib import Path
from types import SimpleNamespace

import pytest

from backend.core.config import Settings
from backend.workers.provider_execution_policy import (
    CURRENT_PROVIDER_EXECUTION_MODE,
    DEFAULT_PROVIDER_EXECUTION_MODE,
    WorkerProviderExecutionPolicy,
    WorkerProviderExecutionPolicyError,
    provider_execution_enabled_by_policy,
    resolve_worker_provider_execution_policy,
)


def test_settings_default_provider_execution_mode_is_disabled(
) -> None:
    field = Settings.model_fields[
        "worker_provider_execution_mode"
    ]

    assert field.default == "disabled"


def test_disabled_server_setting_returns_disabled_policy(
) -> None:
    policy = (
        resolve_worker_provider_execution_policy(
            SimpleNamespace(
                worker_provider_execution_mode=(
                    "disabled"
                )
            )
        )
    )

    assert policy == WorkerProviderExecutionPolicy(
        mode="disabled",
        enabled=False,
        provider=None,
        source="server_settings",
    )


def test_blank_server_setting_fails_to_disabled_default(
) -> None:
    policy = (
        resolve_worker_provider_execution_policy(
            SimpleNamespace(
                worker_provider_execution_mode="  "
            )
        )
    )

    assert policy.enabled is False
    assert policy.mode == "disabled"
    assert policy.provider is None


def test_explicit_cloudflare_server_setting_returns_enabled_policy(
) -> None:
    policy = (
        resolve_worker_provider_execution_policy(
            SimpleNamespace(
                worker_provider_execution_mode=(
                    "  CLOUDFLARE  "
                )
            )
        )
    )

    assert policy.enabled is True
    assert policy.mode == "cloudflare"
    assert policy.provider == "cloudflare"
    assert policy.source == "server_settings"


def test_unknown_server_setting_fails_closed(
) -> None:
    with pytest.raises(
        WorkerProviderExecutionPolicyError,
        match=(
            "Worker provider execution policy "
            "could not be resolved"
        ),
    ) as raised:
        resolve_worker_provider_execution_policy(
            SimpleNamespace(
                worker_provider_execution_mode=(
                    "unknown-provider"
                )
            )
        )

    assert (
        raised.value.mode
        == "unknown-provider"
    )


def test_policy_error_does_not_expose_mode_in_message(
) -> None:
    with pytest.raises(
        WorkerProviderExecutionPolicyError
    ) as raised:
        resolve_worker_provider_execution_policy(
            SimpleNamespace(
                worker_provider_execution_mode=(
                    "internal-value"
                )
            )
        )

    assert (
        "internal-value"
        not in str(raised.value)
    )


def test_policy_is_immutable(
) -> None:
    policy = (
        resolve_worker_provider_execution_policy(
            SimpleNamespace(
                worker_provider_execution_mode=(
                    "disabled"
                )
            )
        )
    )

    with pytest.raises(
        FrozenInstanceError
    ):
        policy.enabled = True


def test_policy_resolver_has_no_payload_parameter(
) -> None:
    parameters = signature(
        resolve_worker_provider_execution_policy
    ).parameters

    assert tuple(parameters) == ("settings",)


def test_policy_constants_are_exact(
) -> None:
    assert (
        DEFAULT_PROVIDER_EXECUTION_MODE
        == "disabled"
    )
    assert (
        CURRENT_PROVIDER_EXECUTION_MODE
        == "cloudflare"
    )


def test_policy_module_preserves_worker_boundaries(
) -> None:
    source = Path(
        "backend/workers/"
        "provider_execution_policy.py"
    ).read_text(
        encoding="utf-8"
    )

    for forbidden in (
        "backend.providers",
        "backend.pipelines",
        "backend.engines",
        "backend.workers.jobs",
        "sqlalchemy",
        "os.getenv(",
        "get_settings(",
        "deployment_history",
        "build_provider_pipeline_binding",
        "resolve_deploy_provider",
        "app_engine",
        "AppEngine",
    ):
        assert forbidden not in source



def test_none_policy_keeps_provider_execution_disabled(
) -> None:
    assert (
        provider_execution_enabled_by_policy(
            None
        )
        is False
    )


def test_disabled_policy_keeps_provider_execution_disabled(
) -> None:
    policy = WorkerProviderExecutionPolicy(
        mode="disabled",
        enabled=False,
        provider=None,
        source="server_settings",
    )

    assert (
        provider_execution_enabled_by_policy(
            policy
        )
        is False
    )


def test_cloudflare_policy_enables_existing_provider_binding(
) -> None:
    policy = WorkerProviderExecutionPolicy(
        mode="cloudflare",
        enabled=True,
        provider="cloudflare",
        source="server_settings",
    )

    assert (
        provider_execution_enabled_by_policy(
            policy
        )
        is True
    )


@pytest.mark.parametrize(
    "policy",
    [
        WorkerProviderExecutionPolicy(
            mode="disabled",
            enabled=True,
            provider=None,
            source="server_settings",
        ),
        WorkerProviderExecutionPolicy(
            mode="cloudflare",
            enabled=False,
            provider="cloudflare",
            source="server_settings",
        ),
        WorkerProviderExecutionPolicy(
            mode="cloudflare",
            enabled=True,
            provider=None,
            source="server_settings",
        ),
    ],
)
def test_inconsistent_policy_object_fails_closed(
    policy,
) -> None:
    with pytest.raises(
        WorkerProviderExecutionPolicyError
    ):
        provider_execution_enabled_by_policy(
            policy
        )


def test_handlers_accept_policy_without_resolving_settings(
) -> None:
    for path in (
        Path(
            "backend/workers/jobs/"
            "deploy_project.py"
        ),
        Path(
            "backend/workers/jobs/"
            "redeploy_project.py"
        ),
    ):
        source = path.read_text(
            encoding="utf-8"
        )

        assert (
            "WorkerProviderExecutionPolicy"
            in source
        )
        assert (
            "provider_execution_enabled_by_policy"
            in source
        )
        assert (
            "resolve_worker_provider_execution_policy"
            not in source
        )
        assert "get_settings(" not in source
        assert "os.getenv(" not in source
        assert (
            "provider_execution_enabled=True"
            not in source
        )


def test_policy_document_records_default_disabled_boundary(
) -> None:
    document = Path(
        "backend/workers/"
        "PROVIDER_EXECUTION_POLICY.md"
    ).read_text(
        encoding="utf-8"
    )

    assert (
        "The default is `disabled`."
        in document
    )
    assert (
        "Dispatcher policy handoff: implemented"
        in document
    )
    assert (
        "They remain separate contracts"
        in document
    )
    assert (
        "does not create a YGIT App Engine"
        in document
    )
