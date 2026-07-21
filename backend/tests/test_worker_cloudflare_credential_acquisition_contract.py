from __future__ import annotations

from datetime import datetime, timezone

import pytest

from pydantic import SecretStr

from backend.engines.auth_engine.connected_accounts_module.schemas import (
    ResolvedProviderCredential,
)
from backend.pipelines.deploy_pipeline.public import (
    DeploymentPipelineContext,
    ProviderTokenReference,
)
from backend.workers.errors import (
    WorkerCloudflareCredentialAcquisitionBlockedError,
)
from backend.workers.jobs.deployment_runtime import (
    acquire_cloudflare_deployment_credential,
)


REFERENCE_VALUE = (
    "cloudflare_oauth_account:account-1"
)
ACCESS_VALUE = "resolved-" + "access-value"
REFRESH_VALUE = "resolved-" + "refresh-value"


class FakeDB:
    pass


class FakeConnectedAccounts:
    def __init__(
        self,
        *,
        credential_reference: str = (
            REFERENCE_VALUE
        ),
    ) -> None:
        self.credential_reference = (
            credential_reference
        )
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
            token_secret_ref=(
                self.credential_reference
            ),
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


def ready_context() -> DeploymentPipelineContext:
    return DeploymentPipelineContext(
        deployment_id="deployment-1",
        project_id="project-1",
        cloudflare_project_name=(
            "portfolio-site"
        ),
        user_id="user-1",
        repository_id="repository-1",
        branch="main",
        artifact_path=(
            "D:/workspace/deployment-1/dist"
        ),
        cloudflare_token_ref=(
            ProviderTokenReference(
                provider="cloudflare",
                token_secret_ref=(
                    REFERENCE_VALUE
                ),
                account_id="account-1",
                account_name=(
                    "Primary Account"
                ),
            )
        ),
        execution_mode="provider_enabled",
    )


@pytest.mark.asyncio
async def test_ready_plan_acquires_credential_through_public_service(
) -> None:
    db = FakeDB()
    service = FakeConnectedAccounts()
    context = ready_context()

    credential = (
        await acquire_cloudflare_deployment_credential(
            db,
            context,
            connected_accounts=service,
        )
    )

    assert service.calls == [
        (
            db,
            "user-1",
            REFERENCE_VALUE,
        )
    ]
    assert (
        credential.access_token
        .get_secret_value()
        == ACCESS_VALUE
    )


@pytest.mark.asyncio
async def test_disabled_plan_blocks_before_credential_service_call(
) -> None:
    service = FakeConnectedAccounts()
    context = ready_context().model_copy(
        update={
            "execution_mode": (
                "contract_skeleton"
            ),
        }
    )

    with pytest.raises(
        WorkerCloudflareCredentialAcquisitionBlockedError
    ) as raised:
        await acquire_cloudflare_deployment_credential(
            FakeDB(),
            context,
            connected_accounts=service,
        )

    assert service.calls == []
    assert raised.value.metadata == {
        "deployment_id": "deployment-1",
        "blockers": [
            "provider_execution_disabled"
        ],
    }
    assert REFERENCE_VALUE not in str(
        raised.value
    )


@pytest.mark.asyncio
async def test_incomplete_context_blocks_before_resolution(
) -> None:
    service = FakeConnectedAccounts()
    context = ready_context().model_copy(
        update={
            "artifact_path": None,
        }
    )

    with pytest.raises(
        WorkerCloudflareCredentialAcquisitionBlockedError
    ) as raised:
        await acquire_cloudflare_deployment_credential(
            FakeDB(),
            context,
            connected_accounts=service,
        )

    assert service.calls == []
    assert raised.value.metadata[
        "blockers"
    ] == [
        "artifact_context_missing"
    ]


@pytest.mark.asyncio
async def test_resolved_reference_mismatch_is_rejected_without_secret_leak(
) -> None:
    service = FakeConnectedAccounts(
        credential_reference=(
            "cloudflare_oauth_account:"
            "different-account"
        )
    )

    with pytest.raises(
        WorkerCloudflareCredentialAcquisitionBlockedError
    ) as raised:
        await acquire_cloudflare_deployment_credential(
            FakeDB(),
            ready_context(),
            connected_accounts=service,
        )

    assert raised.value.metadata[
        "blockers"
    ] == [
        "credential_reference_mismatch"
    ]
    rendered = str(raised.value)
    assert ACCESS_VALUE not in rendered
    assert REFRESH_VALUE not in rendered


@pytest.mark.asyncio
async def test_resolved_credential_serialization_masks_secret_values(
) -> None:
    credential = (
        await acquire_cloudflare_deployment_credential(
            FakeDB(),
            ready_context(),
            connected_accounts=(
                FakeConnectedAccounts()
            ),
        )
    )
    serialized = (
        credential.model_dump_json()
    )

    assert ACCESS_VALUE not in serialized
    assert REFRESH_VALUE not in serialized
    assert "**********" in serialized


def test_credential_acquisition_is_not_wired_into_job_handlers(
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
            "acquire_cloudflare_"
            "deployment_credential"
            not in source
        )
