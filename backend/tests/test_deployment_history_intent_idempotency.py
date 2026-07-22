from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from backend.engines.deployment_history_engine.internal.service import (
    DeploymentHistoryInternalService,
)
from backend.pipelines.deploy_pipeline.contract import (
    DeployPipelineEventName,
    DeployPipelineStage,
)
from backend.pipelines.deploy_pipeline.schemas import (
    HistoryWriteIntent,
    PipelineLogEntry,
)


class FakeDB:
    def __init__(self) -> None:
        self.commit_calls = 0

    async def commit(self) -> None:
        self.commit_calls += 1


class FakeRepository:
    def __init__(self) -> None:
        self.record = None
        self.logs: list[object] = []
        self.update_calls = 0

    async def get_deployment_context(
        self,
        db,
        deployment_id: str,
    ):
        _ = db
        _ = deployment_id
        return SimpleNamespace(
            project_id="project-1",
            user_id="user-1",
        )

    async def get_history_record(
        self,
        db,
        deployment_id: str,
    ):
        _ = db
        _ = deployment_id
        return self.record

    async def create_history_record(
        self,
        db,
        *,
        deployment_id: str,
        project_id: str,
        status: str,
        provider=None,
        metadata=None,
    ):
        _ = db
        _ = provider
        self.record = SimpleNamespace(
            deployment_id=deployment_id,
            project_id=project_id,
            status=status,
            metadata=dict(metadata or {}),
        )
        return self.record

    async def update_history_status(
        self,
        db,
        *,
        deployment_id: str,
        status: str,
        metadata=None,
        **kwargs,
    ):
        _ = db
        _ = deployment_id
        _ = kwargs
        self.update_calls += 1

        if self.record is None:
            raise AssertionError(
                "history record must exist"
            )

        merged = dict(
            self.record.metadata or {}
        )
        merged.update(metadata or {})
        self.record.status = status
        self.record.metadata = merged
        return self.record

    async def append_log(
        self,
        db,
        *,
        deployment_id: str,
        project_id: str,
        level: str,
        message: str,
        metadata=None,
    ):
        _ = db
        log = SimpleNamespace(
            deployment_id=deployment_id,
            project_id=project_id,
            level=level,
            message=message,
            metadata=dict(metadata or {}),
        )
        self.logs.append(log)
        return log


def build_intent(
    *,
    stage: DeployPipelineStage = (
        DeployPipelineStage.PREPARING
    ),
    message: str = "Preparing deployment.",
) -> HistoryWriteIntent:
    return HistoryWriteIntent(
        deployment_id="deployment-1",
        stage=stage,
        history_status="running",
        event_name=(
            DeployPipelineEventName
            .DEPLOYMENT_PREPARING
        ),
        log_entries=[
            PipelineLogEntry(
                timestamp=datetime.now(
                    timezone.utc
                ),
                level="info",
                message=message,
                metadata={
                    "stage": stage.value,
                },
            )
        ],
        metadata={
            "source": "test",
        },
    )


@pytest.mark.asyncio
async def test_replayed_intent_does_not_duplicate_logs(
) -> None:
    repository = FakeRepository()
    service = DeploymentHistoryInternalService(
        repository=repository
    )
    db = FakeDB()
    intent = build_intent()

    first = (
        await service
        .consume_history_write_intent(
            db,
            intent,
        )
    )
    second = (
        await service
        .consume_history_write_intent(
            db,
            intent,
        )
    )

    assert first.logs_written == 1
    assert second.logs_written == 0
    assert len(repository.logs) == 1
    assert repository.update_calls == 1
    assert db.commit_calls == 1


@pytest.mark.asyncio
async def test_distinct_intents_are_persisted(
) -> None:
    repository = FakeRepository()
    service = DeploymentHistoryInternalService(
        repository=repository
    )
    db = FakeDB()

    await service.consume_history_write_intent(
        db,
        build_intent(
            message="First event."
        ),
    )
    await service.consume_history_write_intent(
        db,
        build_intent(
            message="Second event."
        ),
    )

    assert len(repository.logs) == 2
    assert repository.update_calls == 2
    assert db.commit_calls == 2


def test_history_write_key_is_deterministic(
) -> None:
    service = DeploymentHistoryInternalService(
        repository=FakeRepository()
    )
    intent = build_intent()

    assert (
        service._history_write_key(intent)
        == service._history_write_key(intent)
    )


def test_history_write_key_changes_with_content(
) -> None:
    service = DeploymentHistoryInternalService(
        repository=FakeRepository()
    )

    assert (
        service._history_write_key(
            build_intent(
                message="First event."
            )
        )
        != service._history_write_key(
            build_intent(
                message="Second event."
            )
        )
    )
