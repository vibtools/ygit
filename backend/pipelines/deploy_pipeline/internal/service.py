from __future__ import annotations

from backend.pipelines.deploy_pipeline.contract import DeployPipelineStage
from backend.pipelines.deploy_pipeline.errors import (
    DeployPipelineContextInvalidError,
)
from backend.pipelines.deploy_pipeline.internal.events import build_stage_event
from backend.pipelines.deploy_pipeline.internal.history_contract import build_history_write
from backend.pipelines.deploy_pipeline.internal.provider_gateway import (
    ContractSkeletonProviderGateway,
    DeployProviderGateway,
)
from backend.pipelines.deploy_pipeline.schemas import (
    DeploymentPipelineContext,
    DeploymentPipelineResult,
    PipelineLogEntry,
    PipelineProviderSummary,
)


class DeployPipelineService:
    """Deploy Pipeline orchestration skeleton.

    The service freezes stage/event/metadata contracts without performing live
    GitHub or Cloudflare deployment. This lets Deployment History Engine be
    implemented against real pipeline event shapes instead of placeholders.
    """

    def __init__(
        self,
        provider_gateway: DeployProviderGateway | None = None,
    ) -> None:
        self.provider_gateway = (
            provider_gateway
            or ContractSkeletonProviderGateway()
        )

    async def execute_deployment(
        self,
        deployment_id: str,
        *,
        context: DeploymentPipelineContext | None = None,
    ) -> DeploymentPipelineResult:
        runtime_context = self._resolve_context(
            deployment_id=deployment_id,
            context=context,
        )

        return await self.prepare_provider_handoff(
            runtime_context
        )

    async def execute_redeployment(
        self,
        deployment_id: str,
        source_deployment_id: str | None = None,
        *,
        context: DeploymentPipelineContext | None = None,
    ) -> DeploymentPipelineResult:
        runtime_context = self._resolve_context(
            deployment_id=deployment_id,
            context=context,
            source_deployment_id=(
                source_deployment_id
            ),
        )

        return await self.prepare_provider_handoff(
            runtime_context
        )

    def _resolve_context(
        self,
        *,
        deployment_id: str,
        context: DeploymentPipelineContext | None,
        source_deployment_id: str | None = None,
    ) -> DeploymentPipelineContext:
        if context is None:
            return DeploymentPipelineContext(
                deployment_id=deployment_id,
                source_deployment_id=(
                    source_deployment_id
                ),
            )

        if context.deployment_id != deployment_id:
            raise DeployPipelineContextInvalidError(
                "Deploy Pipeline context deployment ID "
                "does not match the requested deployment."
            )

        if (
            source_deployment_id is not None
            and context.source_deployment_id
            not in {
                None,
                source_deployment_id,
            }
        ):
            raise DeployPipelineContextInvalidError(
                "Deploy Pipeline source deployment ID "
                "does not match the redeploy request."
            )

        if (
            source_deployment_id is not None
            and context.source_deployment_id is None
        ):
            return context.model_copy(
                update={
                    "source_deployment_id": (
                        source_deployment_id
                    )
                }
            )

        return context

    async def prepare_provider_handoff(
        self,
        context: DeploymentPipelineContext,
    ) -> DeploymentPipelineResult:
        events = []
        logs: list[PipelineLogEntry] = []
        provider_summaries: list[PipelineProviderSummary] = []
        history_writes = []

        for stage, message in (
            (DeployPipelineStage.PENDING, "Deployment pipeline started."),
            (DeployPipelineStage.PREPARING, "Deployment context prepared for provider handoff."),
            (
                DeployPipelineStage.PROVIDER_DEPLOYING,
                "Provider deployment handoff reached. Live provider execution is not enabled in skeleton.",
            ),
        ):
            event = build_stage_event(
                deployment_id=context.deployment_id,
                stage=stage,
                trace_id=context.trace_id,
                metadata={"execution_mode": context.execution_mode},
            )
            log = PipelineLogEntry(
                level="info",
                message=message,
                metadata={"stage": stage.value, "execution_mode": context.execution_mode},
            )
            events.append(event)
            logs.append(log)
            history_writes.append(
                build_history_write(
                    event=event,
                    logs=[log],
                    metadata={"source": "deploy_pipeline_contract_skeleton"},
                )
            )

        provider_summary = await self.provider_gateway.deploy_to_cloudflare(context)
        provider_summaries.append(provider_summary)
        history_writes[-1] = build_history_write(
            event=events[-1],
            logs=[logs[-1]],
            provider_summary=provider_summary,
            metadata={"source": "deploy_pipeline_contract_skeleton"},
        )

        return DeploymentPipelineResult(
            deployment_id=context.deployment_id,
            status="prepared",
            stage=DeployPipelineStage.PROVIDER_DEPLOYING,
            deployment_url=None,
            events=events,
            logs=logs,
            provider_summaries=provider_summaries,
            history_writes=history_writes,
            metadata={
                "execution_mode": context.execution_mode,
                "provider_calls_executed": False,
                "history_contract_ready": True,
            },
        )
