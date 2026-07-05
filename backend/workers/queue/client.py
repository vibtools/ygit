from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from backend.workers.queue.schemas import JobPayload, JobRef
from backend.workers.repository import JobRepository
from backend.workers.schemas import JobCreateInput


class QueueClient:
    """Queue/job creation boundary.

    In tests and contract-only contexts this can return an in-memory JobRef.
    When a database session is supplied, it creates a durable row in the `jobs`
    table owned by Worker / Job System.
    """

    def __init__(self, repository: JobRepository | None = None, *, queue_name: str = "default") -> None:
        self.repository = repository or JobRepository()
        self.queue_name = queue_name

    async def enqueue(self, payload: JobPayload, db: AsyncSession | None = None) -> JobRef:
        if db is None:
            return JobRef(type=payload.job_type, status="queued")
        record = await self.repository.create_job(
            db,
            JobCreateInput(
                job_type=payload.job_type,
                queue_name=self.queue_name,
                payload=payload.payload,
                trace_id=payload.trace_id,
            ),
        )
        return JobRef(id=record.id, type=record.job_type, status=record.status)  # type: ignore[arg-type]
