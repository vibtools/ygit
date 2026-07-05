from __future__ import annotations

from typing import Literal

from backend.pipelines.deploy_pipeline.contract import DeployPipelineStage
from backend.pipelines.deploy_pipeline.schemas import (
    HistoryWriteIntent,
    PipelineEvent,
    PipelineLogEntry,
    PipelineProviderSummary,
)


def history_status_for_stage(
    stage: DeployPipelineStage,
) -> Literal["created", "running", "completed", "failed", "cancelled"]:
    if stage == DeployPipelineStage.PENDING:
        return "created"
    if stage in {
        DeployPipelineStage.PREPARING,
        DeployPipelineStage.PROVIDER_DEPLOYING,
        DeployPipelineStage.VERIFYING,
    }:
        return "running"
    if stage == DeployPipelineStage.COMPLETED:
        return "completed"
    return "failed"


def build_history_write(
    *,
    event: PipelineEvent,
    logs: list[PipelineLogEntry] | None = None,
    provider_summary: PipelineProviderSummary | None = None,
    metadata: dict[str, object] | None = None,
) -> HistoryWriteIntent:
    return HistoryWriteIntent(
        deployment_id=event.deployment_id,
        stage=event.stage,
        history_status=history_status_for_stage(event.stage),
        event_name=event.event_name,
        log_entries=list(logs or []),
        provider_summary=provider_summary,
        metadata=dict(metadata or {}),
    )
