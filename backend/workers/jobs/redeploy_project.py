from __future__ import annotations

from backend.pipelines.deploy_pipeline.public import deploy_pipeline
from backend.workers.errors import WorkerBuildStageFailedError
from backend.workers.git_checkout import run_git_checkout
from backend.workers.jobs.deployment_outcome import require_completed_pipeline_result
from backend.workers.jobs.deployment_runtime import (
    build_stage_input,
    optional_str,
    payload_with_workspace_if_checkout_ready,
)
from backend.workers.workspace import prepare_repository_workspace

JOB_TYPE = "redeploy_project"


async def run(
    payload: dict[str, object],
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

    deployment_result = (
        await deploy_pipeline.execute_redeployment(
            deployment_id,
            source_deployment_id=(
                str(source_deployment_id)
                if source_deployment_id
                else None
            ),
        )
    )

    require_completed_pipeline_result(
        deployment_id=deployment_id,
        result=deployment_result,
    )
