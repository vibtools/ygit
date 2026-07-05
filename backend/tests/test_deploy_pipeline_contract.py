from __future__ import annotations

import pytest
from pydantic import ValidationError

from backend.pipelines.deploy_pipeline.contract import (
    STAGE_EVENT_MAP,
    DeployPipelineEventName,
    DeployPipelineStage,
)
from backend.pipelines.deploy_pipeline.schemas import PipelineLogEntry, PipelineProviderSummary


def test_deploy_pipeline_stages_are_frozen() -> None:
    assert [stage.value for stage in DeployPipelineStage] == [
        "pending",
        "preparing",
        "provider_deploying",
        "verifying",
        "completed",
        "failed",
    ]


def test_deploy_pipeline_stage_event_map_is_complete() -> None:
    assert set(STAGE_EVENT_MAP) == set(DeployPipelineStage)
    assert STAGE_EVENT_MAP[DeployPipelineStage.PENDING] == DeployPipelineEventName.DEPLOYMENT_STARTED
    assert STAGE_EVENT_MAP[DeployPipelineStage.COMPLETED] == DeployPipelineEventName.DEPLOYMENT_COMPLETED
    assert STAGE_EVENT_MAP[DeployPipelineStage.FAILED] == DeployPipelineEventName.DEPLOYMENT_FAILED


def test_deploy_pipeline_metadata_rejects_secret_like_keys() -> None:
    with pytest.raises(ValidationError):
        PipelineLogEntry(message="unsafe", metadata={"github_token": "not-allowed"})
    with pytest.raises(ValidationError):
        PipelineProviderSummary(
            provider="cloudflare",
            action="deploy_pages",
            status="pending",
            metadata={"authorization": "not-allowed"},
        )
