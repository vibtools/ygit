from __future__ import annotations

from backend.pipelines.deploy_pipeline.public import deploy_pipeline

JOB_TYPE = "deploy_project"


async def run(payload: dict[str, object]) -> None:
    """Run deployment through Deploy Pipeline.

    Worker job owns runtime dispatch only. It must not contain Cloudflare/GitHub
    provider logic and must not write deployment logs directly.
    """
    deployment_id = str(payload["deployment_id"])
    await deploy_pipeline.execute_deployment(deployment_id)
