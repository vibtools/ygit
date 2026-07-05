from __future__ import annotations

from backend.pipelines.deploy_pipeline.internal.service import DeployPipelineService
from backend.pipelines.deploy_pipeline.schemas import DeploymentPipelineResult


class DeployPipeline:
    """Public Deploy Pipeline API.

    Consumers: Deploy Engine and Worker Job Runner only.
    Forbidden consumers: API routes, Dashboard, Admin routes.
    """

    def __init__(self, service: DeployPipelineService | None = None) -> None:
        self.service = service or DeployPipelineService()

    async def execute_deployment(self, deployment_id: str) -> DeploymentPipelineResult:
        return await self.service.execute_deployment(deployment_id)

    async def execute_redeployment(
        self,
        deployment_id: str,
        source_deployment_id: str | None = None,
    ) -> DeploymentPipelineResult:
        return await self.service.execute_redeployment(
            deployment_id,
            source_deployment_id=source_deployment_id,
        )


deploy_pipeline = DeployPipeline()
