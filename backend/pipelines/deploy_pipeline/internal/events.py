from __future__ import annotations

from backend.pipelines.deploy_pipeline.contract import STAGE_EVENT_MAP, DeployPipelineStage
from backend.pipelines.deploy_pipeline.schemas import PipelineEvent


def build_stage_event(
    *,
    deployment_id: str,
    stage: DeployPipelineStage,
    trace_id: str | None = None,
    metadata: dict[str, object] | None = None,
) -> PipelineEvent:
    return PipelineEvent(
        event_name=STAGE_EVENT_MAP[stage],
        stage=stage,
        deployment_id=deployment_id,
        trace_id=trace_id,
        metadata=dict(metadata or {}),
    )
