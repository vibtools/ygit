from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.exceptions import YGITError
from backend.workers.repository import JobRepository
from backend.workers.runner.dispatcher import JobDispatcher
from backend.workers.runner.retry import RetryPolicy
from backend.workers.schemas import JobRecord, JobRunResult, WorkerHeartbeat

logger = logging.getLogger(__name__)


class WorkerRuntime:
    """Single shared worker runtime.

    The runtime leases jobs, dispatches them to approved handlers, and updates
    the Worker / Job System state. It does not contain engine business logic,
    does not import API routes, and does not call providers directly.
    """

    def __init__(
        self,
        *,
        worker_id: str,
        queue_name: str,
        repository: JobRepository | None = None,
        dispatcher: JobDispatcher | None = None,
        retry_policy: RetryPolicy | None = None,
    ) -> None:
        self.worker_id = worker_id
        self.queue_name = queue_name
        self.repository = repository or JobRepository()
        self.dispatcher = dispatcher or JobDispatcher()
        self.retry_policy = retry_policy or RetryPolicy(max_attempts=3)

    def heartbeat(self) -> WorkerHeartbeat:
        return WorkerHeartbeat(
            worker_id=self.worker_id,
            queue_name=self.queue_name,
            status="ready",
            checked_at=datetime.now(timezone.utc),
        )

    async def run_once(self, db: AsyncSession | None = None) -> JobRunResult:
        if db is None:
            logger.info(
                "worker.ready",
                extra={"worker_id": self.worker_id, "queue_name": self.queue_name, "mode": "no-db"},
            )
            return JobRunResult(worker_id=self.worker_id, queue_name=self.queue_name, processed=False)

        job = await self.repository.lease_next_job(db, worker_id=self.worker_id, queue_name=self.queue_name)
        if job is None:
            await db.commit()
            return JobRunResult(worker_id=self.worker_id, queue_name=self.queue_name, processed=False)
        return await self.run_job_record(db, job)

    async def run_job_record(self, db: AsyncSession, job: JobRecord) -> JobRunResult:
        try:
            await self.dispatcher.dispatch(job.job_type, job.payload)
        except YGITError as exc:
            return await self._record_failure(
                db,
                job=job,
                error_code=exc.code,
                error_summary=exc.message,
            )
        except Exception as exc:  # pragma: no cover - defensive runtime boundary
            return await self._record_failure(
                db,
                job=job,
                error_code="JOB_EXECUTION_FAILED",
                error_summary=str(exc),
            )

        completed = await self.repository.mark_completed(
            db,
            job_id=job.id,
            result={"processed_by": self.worker_id},
        )
        await db.commit()
        return JobRunResult(
            worker_id=self.worker_id,
            queue_name=self.queue_name,
            processed=True,
            job_id=completed.id,
            status="completed",
        )

    async def _record_failure(
        self,
        db: AsyncSession,
        *,
        job: JobRecord,
        error_code: str,
        error_summary: str,
    ) -> JobRunResult:
        if job.attempts < job.max_attempts:
            updated = await self.repository.schedule_retry(
                db,
                job_id=job.id,
                error_code=error_code,
                error_summary=error_summary,
                delay_seconds=self.retry_policy.next_delay_seconds(job.attempts),
            )
            await db.commit()
            return JobRunResult(
                worker_id=self.worker_id,
                queue_name=self.queue_name,
                processed=True,
                job_id=updated.id,
                status=updated.status,
                error_code=error_code,
                error_summary=error_summary,
            )

        failed = await self.repository.mark_failed(
            db,
            job_id=job.id,
            error_code=error_code,
            error_summary=error_summary,
        )
        await db.commit()
        return JobRunResult(
            worker_id=self.worker_id,
            queue_name=self.queue_name,
            processed=True,
            job_id=failed.id,
            status="failed",
            error_code=error_code,
            error_summary=error_summary,
        )
