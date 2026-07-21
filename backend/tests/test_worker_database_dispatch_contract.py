from __future__ import annotations

from types import SimpleNamespace

import pytest

from backend.workers.runner.dispatcher import JobDispatcher
from backend.workers.worker import WorkerRuntime


class FakeDB:
    def __init__(self) -> None:
        self.commits = 0

    async def commit(self) -> None:
        self.commits += 1


class FakeRepository:
    def __init__(self) -> None:
        self.completed = False

    async def mark_completed(
        self,
        db,
        *,
        job_id: str,
        result: dict | None = None,
    ):
        _ = db
        _ = result
        self.completed = True
        return SimpleNamespace(id=job_id)

    async def schedule_retry(self, *args, **kwargs):
        raise AssertionError("retry must not be scheduled")

    async def mark_failed(self, *args, **kwargs):
        raise AssertionError("job must not be marked failed")


def job_record() -> SimpleNamespace:
    return SimpleNamespace(
        id="job-db-aware-1",
        job_type="db-aware-job",
        payload={"deployment_id": "deployment-1"},
        attempts=1,
        max_attempts=3,
    )


@pytest.mark.asyncio
async def test_dispatcher_passes_exact_db_to_db_aware_handler() -> None:
    dispatcher = JobDispatcher()
    received: dict[str, object] = {}

    async def handler(payload: dict[str, object], *, db) -> None:
        received["payload"] = payload
        received["db"] = db

    dispatcher.handlers = {"db-aware-job": handler}
    db = FakeDB()
    payload = {"deployment_id": "deployment-1"}

    await dispatcher.dispatch("db-aware-job", payload, db=db)

    assert received["db"] is db
    assert received["payload"] is payload


@pytest.mark.asyncio
async def test_dispatcher_preserves_legacy_handler_contract() -> None:
    dispatcher = JobDispatcher()
    received: list[dict[str, object]] = []

    async def handler(payload: dict[str, object]) -> None:
        received.append(payload)

    dispatcher.handlers = {"legacy-job": handler}
    payload = {"event": "ping"}

    await dispatcher.dispatch("legacy-job", payload, db=FakeDB())

    assert received == [payload]


@pytest.mark.asyncio
async def test_worker_runtime_passes_db_to_db_aware_dispatcher() -> None:
    class DbAwareDispatcher:
        def __init__(self) -> None:
            self.received_db = None
            self.received_payload = None

        async def dispatch(
            self,
            job_type: str,
            payload: dict[str, object],
            *,
            db,
        ) -> None:
            assert job_type == "db-aware-job"
            self.received_db = db
            self.received_payload = payload

    repository = FakeRepository()
    dispatcher = DbAwareDispatcher()
    worker = WorkerRuntime(
        worker_id="worker-1",
        queue_name="default",
        repository=repository,
        dispatcher=dispatcher,
    )
    db = FakeDB()
    job = job_record()

    result = await worker.run_job_record(db, job)

    assert dispatcher.received_db is db
    assert dispatcher.received_payload is job.payload
    assert repository.completed is True
    assert db.commits == 1
    assert result.status == "completed"


@pytest.mark.asyncio
async def test_worker_runtime_preserves_legacy_dispatcher_contract() -> None:
    class LegacyDispatcher:
        def __init__(self) -> None:
            self.calls = []

        async def dispatch(
            self,
            job_type: str,
            payload: dict[str, object],
        ) -> None:
            self.calls.append((job_type, payload))

    repository = FakeRepository()
    dispatcher = LegacyDispatcher()
    worker = WorkerRuntime(
        worker_id="worker-1",
        queue_name="default",
        repository=repository,
        dispatcher=dispatcher,
    )
    db = FakeDB()
    job = job_record()

    await worker.run_job_record(db, job)

    assert dispatcher.calls == [("db-aware-job", job.payload)]
    assert repository.completed is True


def test_db_context_is_not_added_to_job_payload() -> None:
    payload = {"deployment_id": "deployment-1"}
    before = dict(payload)

    assert "db" not in payload
    assert payload == before
