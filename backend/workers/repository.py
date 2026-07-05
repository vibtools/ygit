from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.ids import new_id
from backend.workers.errors import JobTransitionInvalidError
from backend.workers.models import JobModel
from backend.workers.schemas import JobCreateInput, JobRecord


TERMINAL_STATUSES = {"completed", "failed", "cancelled"}


class JobRepository:
    """Repository owned by Worker / Job System for durable job state."""

    async def create_job(self, db: AsyncSession, input_data: JobCreateInput) -> JobRecord:
        now = datetime.now(timezone.utc)
        job = JobModel(
            id=new_id("job"),
            job_type=input_data.job_type,
            status="queued",
            queue_name=input_data.queue_name,
            payload=input_data.payload,
            result=None,
            attempts=0,
            max_attempts=input_data.max_attempts,
            available_at=input_data.available_at or now,
        )
        db.add(job)
        await db.flush()
        return self.to_record(job)

    async def get_by_id(self, db: AsyncSession, job_id: str) -> JobModel | None:
        result = await db.execute(select(JobModel).where(JobModel.id == job_id))
        return result.scalar_one_or_none()

    async def lease_next_job(
        self,
        db: AsyncSession,
        *,
        worker_id: str,
        queue_name: str,
    ) -> JobRecord | None:
        now = datetime.now(timezone.utc)
        stmt = (
            select(JobModel)
            .where(JobModel.queue_name == queue_name)
            .where(JobModel.status.in_(["queued", "retry_waiting"]))
            .where(JobModel.available_at <= now)
            .order_by(JobModel.available_at.asc(), JobModel.created_at.asc())
            .limit(1)
        )
        result = await db.execute(stmt)
        job = result.scalar_one_or_none()
        if job is None:
            return None
        job.status = "running"
        job.locked_by = worker_id
        job.locked_at = now
        job.started_at = job.started_at or now
        job.attempts += 1
        await db.flush()
        return self.to_record(job)

    async def mark_completed(
        self,
        db: AsyncSession,
        *,
        job_id: str,
        result: dict[str, Any] | None = None,
    ) -> JobRecord:
        job = await self._require_mutable(db, job_id)
        job.status = "completed"
        job.result = result or {}
        job.error_code = None
        job.error_summary = None
        job.completed_at = datetime.now(timezone.utc)
        job.locked_by = None
        job.locked_at = None
        await db.flush()
        return self.to_record(job)

    async def mark_failed(
        self,
        db: AsyncSession,
        *,
        job_id: str,
        error_code: str,
        error_summary: str,
    ) -> JobRecord:
        job = await self._require_mutable(db, job_id)
        job.status = "failed"
        job.error_code = error_code
        job.error_summary = error_summary[:2000]
        job.failed_at = datetime.now(timezone.utc)
        job.locked_by = None
        job.locked_at = None
        await db.flush()
        return self.to_record(job)

    async def schedule_retry(
        self,
        db: AsyncSession,
        *,
        job_id: str,
        error_code: str,
        error_summary: str,
        delay_seconds: int,
    ) -> JobRecord:
        job = await self._require_mutable(db, job_id)
        if job.attempts >= job.max_attempts:
            return await self.mark_failed(
                db,
                job_id=job_id,
                error_code=error_code,
                error_summary=error_summary,
            )
        job.status = "retry_waiting"
        job.error_code = error_code
        job.error_summary = error_summary[:2000]
        job.available_at = datetime.now(timezone.utc) + timedelta(seconds=delay_seconds)
        job.locked_by = None
        job.locked_at = None
        await db.flush()
        return self.to_record(job)

    async def cancel_job(self, db: AsyncSession, *, job_id: str) -> JobRecord:
        job = await self._require_mutable(db, job_id)
        job.status = "cancelled"
        job.locked_by = None
        job.locked_at = None
        await db.flush()
        return self.to_record(job)

    async def _require_mutable(self, db: AsyncSession, job_id: str) -> JobModel:
        job = await self.get_by_id(db, job_id)
        if job is None:
            raise ValueError("Job not found.")
        if job.status in TERMINAL_STATUSES:
            raise JobTransitionInvalidError("Terminal jobs cannot be modified.")
        return job

    def to_record(self, job: JobModel) -> JobRecord:
        return JobRecord(
            id=job.id,
            job_type=job.job_type,  # type: ignore[arg-type]
            status=job.status,  # type: ignore[arg-type]
            queue_name=job.queue_name,
            payload=dict(job.payload or {}),
            result=dict(job.result) if job.result is not None else None,
            error_code=job.error_code,
            error_summary=job.error_summary,
            attempts=job.attempts,
            max_attempts=job.max_attempts,
            locked_by=job.locked_by,
            locked_at=job.locked_at,
            available_at=job.available_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
            failed_at=job.failed_at,
            created_at=job.created_at,
            updated_at=job.updated_at,
        )
