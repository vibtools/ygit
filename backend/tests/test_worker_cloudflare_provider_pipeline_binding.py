from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import SecretStr

from backend.engines.auth_engine.connected_accounts_module.schemas import (
    ResolvedProviderCredential,
)
from backend.pipelines.deploy_pipeline.public import (
    DeployPipeline,
    DeploymentPipelineContext,
    ProviderTokenReference,
    deploy_pipeline,
)
from backend.workers.errors import (
    WorkerCloudflareCredentialAcquisitionBlockedError,
)
from backend.workers.jobs.deployment_runtime import (
    build_provider_pipeline_binding,
    deployment_pipeline_context,
)


REFERENCE_VALUE = (
    "cloudflare_oauth_account:account-1"
)
ACCESS_VALUE = "resolved-" + "access-value"
REFRESH_VALUE = "resolved-" + "refresh-value"


class FakeDB:
    pass


class FakeConnectedAccounts:
    def __init__(self) -> None:
        self.calls: list[
            tuple[object, str, str]
        ] = []

    async def acquire_cloudflare_deployment_credential(
        self,
        db,
        *,
        user_id: str,
        token_secret_ref: str,
    ) -> ResolvedProviderCredential:
        self.calls.append(
            (
                db,
                user_id,
                token_secret_ref,
            )
        )
        return ResolvedProviderCredential(
            provider="cloudflare",
            token_secret_ref=REFERENCE_VALUE,
            access_token=SecretStr(
                ACCESS_VALUE
            ),
            refresh_token=SecretStr(
                REFRESH_VALUE
            ),
            token_type="bearer",
            expires_at=datetime.now(
                timezone.utc
            ),
            scopes=["pages:write"],
        )


def ready_context(
    *,
    execution_mode: str = "contract_skeleton",
) -> DeploymentPipelineContext:
    reference = ProviderTokenReference(
        provider="cloudflare",
        token_secret_ref=REFERENCE_VALUE,
        account_id="account-1",
        account_name="Primary Account",
    )
    return DeploymentPipelineContext.model_validate(
        {
            "deployment_id": "deployment-1",
            "project_id": "project-1",
            "cloudflare_project_name": (
                "portfolio-site"
            ),
            "user_id": "user-1",
            "artifact_path": (
                "D:/workspace/deployment-1/dist"
            ),
            "branch": "main",
            "cloudflare_token_ref": (
                reference.model_dump()
            ),
            "execution_mode": execution_mode,
        }
    )


@pytest.mark.asyncio
async def test_default_binding_retains_skeleton_without_credential_acquisition(
) -> None:
    db = FakeDB()
    accounts = FakeConnectedAccounts()
    context = ready_context()

    binding = (
        await build_provider_pipeline_binding(
            db,
            context,
            connected_accounts=accounts,
        )
    )

    assert binding.pipeline is deploy_pipeline
    assert binding.context is context
    assert (
        binding.context.execution_mode
        == "contract_skeleton"
    )
    assert (
        binding.provider_execution_enabled
        is False
    )
    assert accounts.calls == []


@pytest.mark.asyncio
async def test_trusted_enablement_acquires_secret_and_builds_isolated_pipeline(
) -> None:
    db = FakeDB()
    accounts = FakeConnectedAccounts()
    context = ready_context()
    gateway_calls: list[SecretStr] = []
    pipeline_calls: list[object] = []
    gateway = object()
    isolated_pipeline = DeployPipeline()

    def gateway_factory(
        *,
        bearer_value: SecretStr,
    ) -> object:
        gateway_calls.append(
            bearer_value
        )
        return gateway

    def pipeline_factory(
        *,
        provider_gateway: object,
    ) -> DeployPipeline:
        pipeline_calls.append(
            provider_gateway
        )
        return isolated_pipeline

    binding = (
        await build_provider_pipeline_binding(
            db,
            context,
            provider_execution_enabled=True,
            connected_accounts=accounts,
            gateway_factory=gateway_factory,
            pipeline_factory=pipeline_factory,
        )
    )

    assert accounts.calls == [
        (
            db,
            "user-1",
            REFERENCE_VALUE,
        )
    ]
    assert len(gateway_calls) == 1
    assert isinstance(
        gateway_calls[0],
        SecretStr,
    )
    assert (
        gateway_calls[0].get_secret_value()
        == ACCESS_VALUE
    )
    assert pipeline_calls == [gateway]
    assert (
        binding.pipeline
        is isolated_pipeline
    )
    assert (
        binding.context.execution_mode
        == "provider_enabled"
    )
    assert (
        context.execution_mode
        == "contract_skeleton"
    )
    assert (
        binding.provider_execution_enabled
        is True
    )
    rendered = repr(binding)
    assert ACCESS_VALUE not in rendered
    assert REFRESH_VALUE not in rendered


@pytest.mark.asyncio
async def test_trusted_enablement_blocks_before_factory_when_context_is_incomplete(
) -> None:
    accounts = FakeConnectedAccounts()
    gateway_calls: list[object] = []
    context = ready_context().model_copy(
        update={
            "artifact_path": None,
        }
    )

    def gateway_factory(
        **kwargs,
    ) -> object:
        gateway_calls.append(kwargs)
        return object()

    with pytest.raises(
        WorkerCloudflareCredentialAcquisitionBlockedError
    ) as raised:
        await build_provider_pipeline_binding(
            FakeDB(),
            context,
            provider_execution_enabled=True,
            connected_accounts=accounts,
            gateway_factory=gateway_factory,
        )

    assert raised.value.metadata[
        "blockers"
    ] == [
        "artifact_context_missing"
    ]
    assert accounts.calls == []
    assert gateway_calls == []


@pytest.mark.asyncio
async def test_untrusted_payload_cannot_enable_provider_binding(
) -> None:
    payload = {
        "project_id": "project-1",
        "user_id": "user-1",
        "branch": "main",
        "cloudflare_project_name": (
            "portfolio-site"
        ),
        "execution_mode": "provider_enabled",
        "cloudflare_token_ref": {
            "provider": "cloudflare",
            "token_secret_ref": (
                REFERENCE_VALUE
            ),
            "account_id": "account-1",
        },
    }
    context = deployment_pipeline_context(
        "deployment-1",
        payload,
    )
    accounts = FakeConnectedAccounts()

    binding = (
        await build_provider_pipeline_binding(
            FakeDB(),
            context,
            connected_accounts=accounts,
        )
    )

    assert (
        context.execution_mode
        == "contract_skeleton"
    )
    assert (
        binding.provider_execution_enabled
        is False
    )
    assert accounts.calls == []


@pytest.mark.asyncio
async def test_invalid_pipeline_factory_result_is_rejected_without_secret_leak(
) -> None:
    accounts = FakeConnectedAccounts()

    def pipeline_factory(
        **kwargs,
    ):
        return object()

    with pytest.raises(
        TypeError,
        match=(
            "Provider pipeline factory returned "
            "an invalid pipeline"
        ),
    ) as raised:
        await build_provider_pipeline_binding(
            FakeDB(),
            ready_context(),
            provider_execution_enabled=True,
            connected_accounts=accounts,
            gateway_factory=lambda **kwargs: object(),
            pipeline_factory=pipeline_factory,
        )

    rendered = str(raised.value)
    assert ACCESS_VALUE not in rendered
    assert REFRESH_VALUE not in rendered


def test_job_handlers_use_neutral_binding_without_enabling_provider(
) -> None:
    from pathlib import Path

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
            "build_provider_pipeline_binding"
            in source
        )
        assert (
            "provider_execution_enabled=True"
            not in source
        )
        assert (
            '"provider_enabled"'
            not in source
        )
        assert "backend.providers" not in source
        assert "cloudflare_provider" not in source
