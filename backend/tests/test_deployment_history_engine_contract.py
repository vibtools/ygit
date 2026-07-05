from __future__ import annotations

import pytest

from backend.engines.deployment_history_engine.schemas import DeploymentLogInput
from backend.pipelines.deploy_pipeline.contract import DeployPipelineStage
from backend.pipelines.deploy_pipeline.internal.events import build_stage_event
from backend.pipelines.deploy_pipeline.internal.history_contract import build_history_write
from backend.pipelines.deploy_pipeline.schemas import PipelineLogEntry, PipelineProviderSummary


def test_deployment_log_metadata_rejects_secret_keys() -> None:
    with pytest.raises(ValueError):
        DeploymentLogInput(message="unsafe", metadata={"access_token": "nope"})


def test_history_write_intent_from_pipeline_shape_is_consumable() -> None:
    event = build_stage_event(
        deployment_id="dep_123",
        stage=DeployPipelineStage.PROVIDER_DEPLOYING,
        trace_id="trace_123",
        metadata={"execution_mode": "contract_skeleton"},
    )
    log = PipelineLogEntry(message="Provider handoff reached.", metadata={"stage": "provider_deploying"})
    provider_summary = PipelineProviderSummary(
        provider="cloudflare",
        action="deploy_pages",
        status="skipped",
        metadata={"reason": "provider_execution_disabled"},
    )
    intent = build_history_write(event=event, logs=[log], provider_summary=provider_summary)
    assert intent.deployment_id == "dep_123"
    assert intent.history_status == "running"
    assert intent.event_name == "deployment.provider_deploying"
    assert intent.provider_summary is not None
    assert intent.log_entries[0].message == "Provider handoff reached."
