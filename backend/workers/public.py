from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from backend.workers.errors import JobAccessDeniedError, JobNotFoundError
from backend.workers.queue.schemas import JobPayload, JobRef
from backend.workers.repository import JobRepository
from backend.workers.schemas import JobCreateInput, JobRecord


class JobSystemPublicService:
    """Public Job System API.

    Approved consumers: engine public APIs, worker runtime, API job status routes.
    This service owns durable job records; worker jobs must not write engine-owned tables directly.
    """

    def __init__(self, repository: JobRepository | None = None) -> None:
        self.repository = repository or JobRepository()

    async def enqueue_job(
        self,
        db: AsyncSession,
        *,
        payload: JobPayload,
        queue_name: str = "default",
        max_attempts: int = 3,
    ) -> JobRef:
        record = await self.repository.create_job(
            db,
            JobCreateInput(
                job_type=payload.job_type,  # type: ignore[arg-type]
                queue_name=queue_name,
                payload=payload.payload,
                trace_id=payload.trace_id,
                max_attempts=max_attempts,
            ),
        )
        return JobRef(id=record.id, type=record.job_type, status=record.status)  # type: ignore[arg-type]

    async def get_job(self, db: AsyncSession, *, job_id: str) -> JobRecord:
        model = await self.repository.get_by_id(db, job_id)
        if model is None:
            raise JobNotFoundError()
        return self.repository.to_record(model)

    async def get_job_for_user(self, db: AsyncSession, *, user_id: str, job_id: str) -> JobRecord:
        record = await self.get_job(db, job_id=job_id)
        payload_user_id = record.payload.get("user_id")
        if payload_user_id is not None and payload_user_id != user_id:
            raise JobAccessDeniedError()
        return record


job_system = JobSystemPublicService()
