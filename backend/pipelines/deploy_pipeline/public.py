from __future__ import annotations

from backend.pipelines.deploy_pipeline.internal.service import DeployPipelineService
from backend.pipelines.deploy_pipeline.schemas import (
    DeploymentPipelineContext,
    DeploymentPipelineResult,
    ProviderTokenReference,
)
from backend.pipelines.deploy_pipeline.internal.build_stage import DeployBuildStageInput, DeployBuildStageResult, DeployPipelineBuildStage


class DeployPipeline:
    """Public Deploy Pipeline API.

    Consumers: Deploy Engine and Worker Job Runner only.
    Forbidden consumers: API routes, Dashboard, Admin routes.
    """

    def __init__(self, service: DeployPipelineService | None = None) -> None:
        self.service = service or DeployPipelineService()

    async def execute_deployment(
        self,
        deployment_id: str,
        *,
        context: DeploymentPipelineContext | None = None,
    ) -> DeploymentPipelineResult:
        return await self.service.execute_deployment(
            deployment_id,
            context=context,
        )

    async def execute_redeployment(
        self,
        deployment_id: str,
        source_deployment_id: str | None = None,
        *,
        context: DeploymentPipelineContext | None = None,
    ) -> DeploymentPipelineResult:
        return await self.service.execute_redeployment(
            deployment_id,
            source_deployment_id=source_deployment_id,
            context=context,
        )


    def execute_build_stage(self, input_data: DeployBuildStageInput) -> DeployBuildStageResult:
        """Run the worker-owned build stage through the Deploy Pipeline public boundary.

        This method intentionally delegates to the isolated build-stage module and
        does not modify deployment history, call providers, or require API routes.
        Worker integration can call this after repository checkout is available.
        """

        return DeployPipelineBuildStage().run(input_data)

deploy_pipeline = DeployPipeline()
