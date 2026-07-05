from __future__ import annotations

import pytest

from backend.pipelines.deploy_pipeline.contract import DeployPipelineStage
from backend.pipelines.deploy_pipeline.public import DeployPipeline


@pytest.mark.asyncio
async def test_deploy_pipeline_skeleton_returns_history_write_intents() -> None:
    result = await DeployPipeline().execute_deployment("dep_test")

    assert result.deployment_id == "dep_test"
    assert result.status == "prepared"
    assert result.stage == DeployPipelineStage.PROVIDER_DEPLOYING
    assert result.metadata["provider_calls_executed"] is False
    assert result.metadata["history_contract_ready"] is True
    assert [event.stage for event in result.events] == [
        DeployPipelineStage.PENDING,
        DeployPipelineStage.PREPARING,
        DeployPipelineStage.PROVIDER_DEPLOYING,
    ]
    assert len(result.history_writes) == 3
    assert result.history_writes[-1].provider_summary is not None
    assert result.history_writes[-1].provider_summary.provider == "cloudflare"
    assert result.history_writes[-1].provider_summary.status == "pending"


@pytest.mark.asyncio
async def test_redeployment_pipeline_accepts_source_deployment() -> None:
    result = await DeployPipeline().execute_redeployment("dep_new", source_deployment_id="dep_old")
    assert result.deployment_id == "dep_new"
    assert result.status == "prepared"
