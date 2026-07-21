from __future__ import annotations

import pytest
from pydantic import ValidationError

from backend.pipelines.deploy_pipeline.contract import (
    CLOUDFLARE_PROVIDER_OPERATION_ORDER,
    CloudflareProviderOperation,
)
from backend.pipelines.deploy_pipeline.errors import (
    DeployPipelineContextInvalidError,
)
from backend.pipelines.deploy_pipeline.internal.provider_gateway import (
    build_cloudflare_provider_execution_plan,
)
from backend.pipelines.deploy_pipeline.schemas import (
    CloudflareProviderExecutionPlan,
    DeploymentPipelineContext,
    ProviderTokenReference,
)


REFERENCE_VALUE = (
    "cloudflare_oauth_account:account-1"
)


def cloudflare_reference(
    *,
    provider: str = "cloudflare",
) -> ProviderTokenReference:
    return ProviderTokenReference.model_validate(
        {
            "provider": provider,
            "token_secret_ref": REFERENCE_VALUE,
            "account_id": "cf-account-1",
            "account_name": "Primary Account",
        }
    )


def complete_context(
    *,
    execution_mode: str = "provider_enabled",
) -> DeploymentPipelineContext:
    return DeploymentPipelineContext.model_validate(
        {
            "deployment_id": "deployment-1",
            "project_id": "project-1",
            "cloudflare_project_name": "portfolio-site",
            "user_id": "user-1",
            "artifact_path": (
                "D:/workspace/deployment-1/dist"
            ),
            "branch": "main",
            "cloudflare_token_ref": (
                cloudflare_reference()
                .model_dump()
            ),
            "execution_mode": execution_mode,
        }
    )


def test_provider_enabled_context_builds_ready_ordered_plan(
) -> None:
    plan = (
        build_cloudflare_provider_execution_plan(
            complete_context()
        )
    )

    assert plan.ready_to_execute is True
    assert plan.blockers == []
    assert plan.operations == list(
        CLOUDFLARE_PROVIDER_OPERATION_ORDER
    )
    assert plan.operations == [
        CloudflareProviderOperation.ENSURE_PROJECT,
        CloudflareProviderOperation.BUILD_ARTIFACT_MANIFEST,
        CloudflareProviderOperation.PREPARE_ASSET_UPLOAD,
        CloudflareProviderOperation.UPLOAD_MISSING_ASSETS,
        CloudflareProviderOperation.UPSERT_ASSET_HASHES,
        CloudflareProviderOperation.CREATE_DEPLOYMENT,
    ]


def test_contract_skeleton_plan_remains_disabled(
) -> None:
    plan = (
        build_cloudflare_provider_execution_plan(
            complete_context(
                execution_mode="contract_skeleton"
            )
        )
    )

    assert plan.ready_to_execute is False
    assert plan.blockers == [
        "provider_execution_disabled"
    ]


def test_missing_runtime_context_accumulates_safe_blockers(
) -> None:
    context = DeploymentPipelineContext(
        deployment_id="deployment-2",
    )

    plan = (
        build_cloudflare_provider_execution_plan(
            context
        )
    )

    assert plan.ready_to_execute is False
    assert plan.blockers == [
        "user_context_missing",
        "project_context_missing",
        "artifact_context_missing",
        "branch_context_missing",
        "cloudflare_reference_missing",
        "provider_execution_disabled",
    ]


def test_wrong_provider_reference_is_rejected(
) -> None:
    context = complete_context().model_copy(
        update={
            "cloudflare_token_ref": (
                cloudflare_reference(
                    provider="github"
                )
            )
        }
    )

    with pytest.raises(
        DeployPipelineContextInvalidError,
        match="provider is invalid",
    ):
        build_cloudflare_provider_execution_plan(
            context
        )


def test_control_character_context_is_rejected(
) -> None:
    context = complete_context().model_copy(
        update={
            "artifact_path": "dist\nunsafe",
        }
    )

    with pytest.raises(
        DeployPipelineContextInvalidError,
        match="artifact path is invalid",
    ):
        build_cloudflare_provider_execution_plan(
            context
        )


def test_plan_serialization_excludes_sensitive_reference_and_path(
) -> None:
    context = complete_context()
    plan = (
        build_cloudflare_provider_execution_plan(
            context
        )
    )
    serialized = plan.model_dump_json()

    assert REFERENCE_VALUE not in serialized
    assert context.artifact_path not in serialized
    assert "token_secret_ref" not in serialized


def test_plan_builder_does_not_mutate_context(
) -> None:
    context = complete_context()
    before = context.model_dump()

    build_cloudflare_provider_execution_plan(
        context
    )

    assert context.model_dump() == before


def test_plan_model_rejects_reordered_operations(
) -> None:
    operations = list(
        CLOUDFLARE_PROVIDER_OPERATION_ORDER
    )
    operations.reverse()

    with pytest.raises(
        ValidationError,
        match="operation order is invalid",
    ):
        CloudflareProviderExecutionPlan(
            deployment_id="deployment-3",
            execution_mode="provider_enabled",
            operations=operations,
            ready_to_execute=True,
            blockers=[],
        )


def test_plan_model_rejects_inconsistent_readiness(
) -> None:
    with pytest.raises(
        ValidationError,
        match="readiness is inconsistent",
    ):
        CloudflareProviderExecutionPlan(
            deployment_id="deployment-4",
            execution_mode="provider_enabled",
            operations=list(
                CLOUDFLARE_PROVIDER_OPERATION_ORDER
            ),
            ready_to_execute=True,
            blockers=[
                "artifact_context_missing"
            ],
        )

def test_provider_enabled_plan_requires_cloudflare_runtime_identifiers(
) -> None:
    context = complete_context().model_copy(
        update={
            "cloudflare_project_name": None,
            "cloudflare_token_ref": (
                cloudflare_reference().model_copy(
                    update={"account_id": None}
                )
            ),
        }
    )
    plan = build_cloudflare_provider_execution_plan(context)
    assert plan.ready_to_execute is False
    assert plan.blockers == [
        "cloudflare_project_name_missing",
        "cloudflare_account_context_missing",
    ]


def test_cloudflare_project_name_control_character_is_rejected(
) -> None:
    context = complete_context().model_copy(
        update={"cloudflare_project_name": "portfolio\nunsafe"}
    )
    with pytest.raises(
        DeployPipelineContextInvalidError,
        match="Cloudflare project name is invalid",
    ):
        build_cloudflare_provider_execution_plan(context)


def test_cloudflare_account_id_control_character_is_rejected(
) -> None:
    context = complete_context().model_copy(
        update={
            "cloudflare_token_ref": (
                cloudflare_reference().model_copy(
                    update={"account_id": "account\runsafe"}
                )
            )
        }
    )
    with pytest.raises(
        DeployPipelineContextInvalidError,
        match="Cloudflare account ID is invalid",
    ):
        build_cloudflare_provider_execution_plan(context)
