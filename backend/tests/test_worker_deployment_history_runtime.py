from __future__ import annotations

from types import SimpleNamespace

import pytest

from backend.core.exceptions import YGITError
from backend.workers.jobs import (
    deploy_project,
    redeploy_project,
)
from backend.workers.jobs.deployment_history_runtime import (
    deployment_history_completed,
    persist_deployment_failure_safely,
    persist_pipeline_result_history,
    safe_failure_details,
)


class FakeDB:
    def __init__(self) -> None:
        self.rollback_calls = 0

    async def rollback(self) -> None:
        self.rollback_calls += 1


class FakeHistoryService:
    def __init__(
        self,
        *,
        runtime_record=None,
    ) -> None:
        self.runtime_record = runtime_record
        self.intents: list[object] = []
        self.failures: list[
            tuple[str, str, str | None]
        ] = []

    async def get_runtime_record(
        self,
        db,
        *,
        deployment_id: str,
    ):
        _ = db
        _ = deployment_id
        return self.runtime_record

    async def consume_history_write_intent(
        self,
        db,
        intent,
    ):
        _ = db
        self.intents.append(intent)

    async def mark_failed(
        self,
        db,
        *,
        deployment_id: str,
        error_summary: str,
        failure_code: str | None = None,
    ):
        _ = db
        self.failures.append(
            (
                deployment_id,
                error_summary,
                failure_code,
            )
        )


@pytest.mark.asyncio
async def test_pipeline_history_intents_persist_in_order(
) -> None:
    service = FakeHistoryService()
    db = FakeDB()
    intents = [
        object(),
        object(),
        object(),
    ]

    count = await persist_pipeline_result_history(
        db,
        SimpleNamespace(
            history_writes=intents
        ),
        service=service,
    )

    assert count == 3
    assert service.intents == intents


@pytest.mark.asyncio
async def test_completed_history_blocks_duplicate_execution(
) -> None:
    service = FakeHistoryService(
        runtime_record=SimpleNamespace(
            status="completed"
        )
    )

    assert (
        await deployment_history_completed(
            FakeDB(),
            "deployment-completed",
            service=service,
        )
        is True
    )


@pytest.mark.asyncio
async def test_noncompleted_history_allows_execution(
) -> None:
    service = FakeHistoryService(
        runtime_record=SimpleNamespace(
            status="running"
        )
    )

    assert (
        await deployment_history_completed(
            FakeDB(),
            "deployment-running",
            service=service,
        )
        is False
    )


def test_ygit_failure_details_remain_safe(
) -> None:
    error = YGITError(
        code="PROVIDER_TIMEOUT",
        message="Provider request timed out.",
    )

    assert safe_failure_details(error) == (
        "PROVIDER_TIMEOUT",
        "Provider request timed out.",
    )


def test_unknown_failure_details_are_sanitized(
) -> None:
    error = RuntimeError(
        "internal-token-value"
    )

    assert safe_failure_details(error) == (
        "JOB_EXECUTION_FAILED",
        "Deployment execution failed.",
    )


@pytest.mark.asyncio
async def test_safe_failure_persistence_rolls_back_and_records(
) -> None:
    db = FakeDB()
    service = FakeHistoryService()

    persisted = (
        await persist_deployment_failure_safely(
            db,
            "deployment-failed",
            RuntimeError(
                "private-runtime-detail"
            ),
            service=service,
        )
    )

    assert persisted is True
    assert db.rollback_calls == 1
    assert service.failures == [
        (
            "deployment-failed",
            "Deployment execution failed.",
            "JOB_EXECUTION_FAILED",
        )
    ]


@pytest.mark.asyncio
async def test_deploy_handler_skips_completed_history(
    monkeypatch,
) -> None:
    calls: list[str] = []

    async def completed(db, deployment_id):
        _ = db
        calls.append(deployment_id)
        return True

    async def forbidden(*args, **kwargs):
        _ = args
        _ = kwargs
        raise AssertionError(
            "provider binding must not run"
        )

    monkeypatch.setattr(
        deploy_project,
        "deployment_history_completed",
        completed,
    )
    monkeypatch.setattr(
        deploy_project,
        "build_provider_pipeline_binding",
        forbidden,
    )

    await deploy_project.run(
        {
            "deployment_id": (
                "deployment-already-complete"
            ),
        },
        db=FakeDB(),
    )

    assert calls == [
        "deployment-already-complete"
    ]


@pytest.mark.asyncio
async def test_redeploy_handler_skips_completed_history(
    monkeypatch,
) -> None:
    calls: list[str] = []

    async def completed(db, deployment_id):
        _ = db
        calls.append(deployment_id)
        return True

    async def forbidden(*args, **kwargs):
        _ = args
        _ = kwargs
        raise AssertionError(
            "provider binding must not run"
        )

    monkeypatch.setattr(
        redeploy_project,
        "deployment_history_completed",
        completed,
    )
    monkeypatch.setattr(
        redeploy_project,
        "build_provider_pipeline_binding",
        forbidden,
    )

    await redeploy_project.run(
        {
            "deployment_id": (
                "redeployment-already-complete"
            ),
        },
        db=FakeDB(),
    )

    assert calls == [
        "redeployment-already-complete"
    ]
