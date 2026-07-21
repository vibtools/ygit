from __future__ import annotations

from dataclasses import dataclass

from backend.pipelines.deploy_pipeline.internal.provider_gateway import (
    build_cloudflare_provider_execution_plan,
)
from backend.workers.jobs.deployment_runtime import (
    deployment_pipeline_context,
)

REFERENCE_VALUE = "cloudflare_oauth_account:account-1"


@dataclass(frozen=True)
class BuildResult:
    artifact_ready: bool
    output_directory: str


def runtime_payload() -> dict[str, object]:
    return {
        "project_id": "project-1",
        "user_id": "user-1",
        "repository_id": "repository-1",
        "analysis_id": "analysis-1",
        "git_ref": "main",
        "cloudflare_project_name": "portfolio-site",
        "cloudflare_token_ref": {
            "provider": "cloudflare",
            "token_secret_ref": REFERENCE_VALUE,
            "account_id": "cf-account-1",
            "account_name": "Primary Account",
        },
    }


def build_result(deployment_id: str) -> BuildResult:
    return BuildResult(
        artifact_ready=True,
        output_directory=f"D:/workspace/{deployment_id}/dist",
    )


def test_worker_context_carries_cloudflare_runtime_identifiers() -> None:
    context = deployment_pipeline_context(
        "deployment-1",
        runtime_payload(),
        build_result=build_result("deployment-1"),
    )
    assert context.cloudflare_project_name == "portfolio-site"
    assert context.cloudflare_token_ref is not None
    assert context.cloudflare_token_ref.account_id == "cf-account-1"
    assert context.cloudflare_token_ref.token_secret_ref == REFERENCE_VALUE
    assert context.execution_mode == "contract_skeleton"


def test_worker_payload_cannot_enable_provider_execution() -> None:
    payload = runtime_payload()
    payload["execution_mode"] = "provider_enabled"
    context = deployment_pipeline_context(
        "deployment-2",
        payload,
        build_result=build_result("deployment-2"),
    )
    assert context.execution_mode == "contract_skeleton"


def test_worker_context_becomes_ready_only_after_trusted_enable() -> None:
    context = deployment_pipeline_context(
        "deployment-3",
        runtime_payload(),
        build_result=build_result("deployment-3"),
    )
    disabled = build_cloudflare_provider_execution_plan(context)
    enabled = build_cloudflare_provider_execution_plan(
        context.model_copy(update={"execution_mode": "provider_enabled"})
    )
    assert disabled.ready_to_execute is False
    assert disabled.blockers == ["provider_execution_disabled"]
    assert enabled.ready_to_execute is True
    assert enabled.blockers == []


def test_missing_worker_project_name_blocks_trusted_plan() -> None:
    payload = runtime_payload()
    payload.pop("cloudflare_project_name")
    context = deployment_pipeline_context(
        "deployment-4",
        payload,
        build_result=build_result("deployment-4"),
    ).model_copy(update={"execution_mode": "provider_enabled"})
    plan = build_cloudflare_provider_execution_plan(context)
    assert plan.ready_to_execute is False
    assert plan.blockers == ["cloudflare_project_name_missing"]


def test_context_serialization_contains_no_resolved_credential() -> None:
    context = deployment_pipeline_context(
        "deployment-5",
        runtime_payload(),
        build_result=build_result("deployment-5"),
    )
    serialized = context.model_dump_json()
    assert "access_token" not in serialized
    assert "refresh_token" not in serialized
    assert "Bearer " not in serialized
