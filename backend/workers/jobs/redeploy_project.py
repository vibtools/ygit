from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from backend.pipelines.deploy_pipeline.public import deploy_pipeline
from backend.workers.errors import WorkerBuildStageFailedError
from backend.workers.git_checkout import run_git_checkout
from backend.workers.jobs.deployment_outcome import require_completed_pipeline_result
from backend.workers.jobs.deployment_runtime import (
    build_provider_pipeline_binding,
    build_stage_input,
    deployment_pipeline_context,
    execute_redeployment_with_context,
    optional_str,
    payload_with_workspace_if_checkout_ready,
)
from backend.workers.workspace import prepare_repository_workspace

JOB_TYPE = "redeploy_project"


async def run(
    payload: dict[str, object],
    *,
    db: AsyncSession | None = None,
) -> None:
    """Run redeployment through shared worker checkout/build preparation."""

    deployment_id = str(
        payload["deployment_id"]
    )

    source_deployment_id = payload.get(
        "source_deployment_id"
    )

    runtime_payload = (
        payload_with_workspace_if_checkout_ready(
            deployment_id,
            payload,
            checkout_runner=run_git_checkout,
            workspace_preparer=(
                prepare_repository_workspace
            ),
        )
    )

    build_input = build_stage_input(
        deployment_id,
        runtime_payload,
    )
    build_result = None

    if build_input is not None:
        build_result = (
            deploy_pipeline.execute_build_stage(
                build_input
            )
        )

        build_status = optional_str(
            getattr(
                build_result,
                "status",
                None,
            )
        ) or "missing"

        if build_status != "succeeded":
            raise WorkerBuildStageFailedError(
                deployment_id=deployment_id,
                build_status=build_status,
            )

    normalized_source_deployment_id = (
        optional_str(source_deployment_id)
    )

    pipeline_context = deployment_pipeline_context(
        deployment_id,
        runtime_payload,
        build_result=build_result,
        source_deployment_id=(
            normalized_source_deployment_id
        ),
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
        await execute_redeployment_with_context(
            active_pipeline,
            deployment_id,
            source_deployment_id=(
                normalized_source_deployment_id
            ),
            context=active_context,
        )
    )

    require_completed_pipeline_result(
        deployment_id=deployment_id,
        result=deployment_result,
    )
