from __future__ import annotations

from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from backend.pipelines.deploy_pipeline.public import DeployBuildStageInput, deploy_pipeline
from backend.workers.errors import WorkerBuildStageFailedError
from backend.workers.git_checkout import run_git_checkout
from backend.workers.jobs.deployment_outcome import require_completed_pipeline_result
from backend.workers.jobs.deployment_runtime import (
    build_provider_pipeline_binding,
    build_stage_input,
    deployment_pipeline_context,
    execute_deployment_with_context,
    optional_str,
    payload_checkout_ref,
    payload_checkout_timeout_seconds,
    payload_environment,
    payload_has_build_stage_fields,
    payload_needs_worker_workspace,
    payload_timeout_seconds,
    payload_with_workspace_if_checkout_ready,
    repository_contains_checkout,
)
from backend.workers.workspace import prepare_repository_workspace

JOB_TYPE = "deploy_project"

def _optional_str(
    value: object,
) -> str | None:
    return optional_str(value)


def _payload_has_build_stage_fields(
    payload: dict[str, object],
) -> bool:
    return payload_has_build_stage_fields(
        payload
    )


def _payload_needs_worker_workspace(
    payload: dict[str, object],
) -> bool:
    return payload_needs_worker_workspace(
        payload
    )


def _repository_contains_checkout(
    repository_path: Path,
) -> bool:
    return repository_contains_checkout(
        repository_path
    )


def _payload_timeout_seconds(
    value: object,
) -> int:
    return payload_timeout_seconds(value)


def _payload_checkout_ref(
    payload: dict[str, object],
) -> str | None:
    return payload_checkout_ref(payload)


def _payload_checkout_timeout_seconds(
    value: object,
) -> int:
    return payload_checkout_timeout_seconds(
        value
    )


def _payload_environment(
    value: object,
) -> dict[str, str]:
    return payload_environment(value)


def _payload_with_workspace_if_checkout_ready(
    deployment_id: str,
    payload: dict[str, object],
) -> dict[str, object]:
    return payload_with_workspace_if_checkout_ready(
        deployment_id,
        payload,
        checkout_runner=run_git_checkout,
        workspace_preparer=prepare_repository_workspace,
    )


def _build_stage_input(
    deployment_id: str,
    payload: dict[str, object],
) -> DeployBuildStageInput | None:
    return build_stage_input(
        deployment_id,
        payload,
    )


async def run(
    payload: dict[str, object],
    *,
    db: AsyncSession | None = None,
) -> None:
    """Run deployment through Deploy Pipeline.

    Worker job owns runtime dispatch only. It must not contain Cloudflare/GitHub
    provider logic and must not write deployment logs directly.
    """

    deployment_id = str(payload["deployment_id"])
    runtime_payload = _payload_with_workspace_if_checkout_ready(deployment_id, payload)
    build_input = _build_stage_input(deployment_id, runtime_payload)
    build_result = None

    if build_input is not None:
        build_result = deploy_pipeline.execute_build_stage(
            build_input
        )

        build_status = _optional_str(
            getattr(build_result, "status", None)
        ) or "missing"

        if build_status != "succeeded":
            raise WorkerBuildStageFailedError(
                deployment_id=deployment_id,
                build_status=build_status,
            )

    pipeline_context = deployment_pipeline_context(
        deployment_id,
        runtime_payload,
        build_result=build_result,
    )
    active_pipeline = deploy_pipeline
    active_context = pipeline_context

    if db is not None:
        binding = await build_provider_pipeline_binding(
            db,
            pipeline_context,
        )
        active_pipeline = binding.pipeline
        active_context = binding.context

    deployment_result = (
        await execute_deployment_with_context(
            active_pipeline,
            deployment_id,
            context=active_context,
        )
    )

    require_completed_pipeline_result(
        deployment_id=deployment_id,
        result=deployment_result,
    )
