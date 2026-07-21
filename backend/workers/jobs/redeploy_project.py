from __future__ import annotations

from backend.pipelines.deploy_pipeline.public import deploy_pipeline
from backend.workers.jobs.deployment_outcome import require_completed_pipeline_result

JOB_TYPE = "redeploy_project"


async def run(payload: dict[str, object]) -> None:
    """Run redeployment through Deploy Pipeline.

    Worker job owns runtime dispatch only. It must not contain Cloudflare/GitHub
    provider logic and must not write deployment logs directly.
    """
    deployment_id = str(payload["deployment_id"])
    source_deployment_id = payload.get("source_deployment_id")
    deployment_result = await deploy_pipeline.execute_redeployment(
        deployment_id,
        source_deployment_id=(
            str(source_deployment_id)
            if source_deployment_id
            else None
        ),
    )

    require_completed_pipeline_result(
        deployment_id=deployment_id,
        result=deployment_result,
    )
