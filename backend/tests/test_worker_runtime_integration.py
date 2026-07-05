from __future__ import annotations

from datetime import datetime, timezone

import pytest

from backend.workers.queue.client import QueueClient
from backend.workers.queue.schemas import JobPayload
from backend.workers.runner.retry import RetryPolicy
from backend.workers.schemas import JobRecord
from backend.workers.worker import WorkerRuntime

NOW = datetime.now(timezone.utc)


def job_record(**overrides) -> JobRecord:
    data = {
        "id": "job_1",
        "job_type": "webhook_event",
        "status": "running",
        "queue_name": "default",
        "payload": {},
        "result": None,
        "error_code": None,
        "error_summary": None,
        "attempts": 1,
        "max_attempts": 3,
        "locked_by": "worker_1",
        "locked_at": NOW,
        "available_at": NOW,
        "started_at": NOW,
        "completed_at": None,
        "failed_at": None,
        "created_at": NOW,
        "updated_at": NOW,
    }
    data.update(overrides)
    return JobRecord(**data)


class FakeRepository:
    def __init__(self, leased: JobRecord | None = None) -> None:
        self.leased = leased
        self.completed: str | None = None
        self.failed: str | None = None
        self.retried: str | None = None

    async def lease_next_job(self, db, *, worker_id: str, queue_name: str):
        return self.leased

    async def mark_completed(self, db, *, job_id: str, result: dict | None = None):
        self.completed = job_id
        return job_record(id=job_id, status="completed", result=result, completed_at=NOW)

    async def mark_failed(self, db, *, job_id: str, error_code: str, error_summary: str):
        self.failed = job_id
        return job_record(id=job_id, status="failed", error_code=error_code, error_summary=error_summary, failed_at=NOW)

    async def schedule_retry(self, db, *, job_id: str, error_code: str, error_summary: str, delay_seconds: int):
        self.retried = job_id
        return job_record(id=job_id, status="retry_waiting", error_code=error_code, error_summary=error_summary)


class FakeDispatcher:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.dispatched: tuple[str, dict] | None = None

    async def dispatch(self, job_type: str, payload: dict[str, object]) -> None:
        self.dispatched = (job_type, payload)
        if self.fail:
            raise RuntimeError("boom")


class FakeDB:
    def __init__(self) -> None:
        self.commits = 0

    async def commit(self) -> None:
        self.commits += 1


@pytest.mark.asyncio
async def test_queue_client_without_db_returns_contract_job_ref() -> None:
    client = QueueClient()
    ref = await client.enqueue(
        JobPayload(job_type="deploy_project", payload={"deployment_id": "dep_1"}, trace_id="trace_1")
    )
    assert ref.id.startswith("job_")
    assert ref.status == "queued"
    assert ref.type == "deploy_project"


@pytest.mark.asyncio
async def test_worker_runtime_processes_leased_job() -> None:
    repository = FakeRepository(leased=job_record(job_type="webhook_event", payload={"event": "ping"}))
    dispatcher = FakeDispatcher()
    worker = WorkerRuntime(
        worker_id="worker_1",
        queue_name="default",
        repository=repository,
        dispatcher=dispatcher,
    )
    db = FakeDB()
    result = await worker.run_once(db)
    assert result.processed is True
    assert result.status == "completed"
    assert result.job_id == "job_1"
    assert repository.completed == "job_1"
    assert dispatcher.dispatched == ("webhook_event", {"event": "ping"})
    assert db.commits == 1


@pytest.mark.asyncio
async def test_worker_runtime_retries_failed_job_before_max_attempts() -> None:
    repository = FakeRepository(leased=job_record(attempts=1, max_attempts=3))
    worker = WorkerRuntime(
        worker_id="worker_1",
        queue_name="default",
        repository=repository,
        dispatcher=FakeDispatcher(fail=True),
        retry_policy=RetryPolicy(max_attempts=3, base_delay_seconds=1),
    )
    result = await worker.run_once(FakeDB())
    assert result.status == "retry_waiting"
    assert result.error_code == "JOB_EXECUTION_FAILED"
    assert repository.retried == "job_1"


@pytest.mark.asyncio
async def test_worker_runtime_without_db_is_non_mutating_ready_check() -> None:
    worker = WorkerRuntime(worker_id="worker_1", queue_name="default")
    result = await worker.run_once()
    assert result.processed is False
    assert result.status == "idle"
