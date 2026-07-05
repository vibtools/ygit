from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.ids import new_id
from backend.engines.repository_analysis_engine.schemas import AnalysisJobRef
from backend.workers.queue.client import QueueClient
from backend.workers.queue.schemas import JobPayload


class DeepAnalysisQueue:
    """Queues deep analysis through Worker / Job System.

    If a DB session is supplied, a durable job row is created. Without a DB
    session, this remains a contract-safe job reference for unit tests.
    """

    def __init__(self, queue_client: QueueClient | None = None) -> None:
        self.queue_client = queue_client or QueueClient(queue_name="analysis")

    async def queue(
        self,
        *,
        repository_id: str,
        user_id: str,
        db: AsyncSession | None = None,
        trace_id: str = "trace_repository_analysis_deep",
    ) -> AnalysisJobRef:
        if db is None:
            return AnalysisJobRef(id=new_id("job"), status="queued")
        job = await self.queue_client.enqueue(
            JobPayload(
                job_type="repository_analysis_deep",
                payload={"repository_id": repository_id, "user_id": user_id},
                trace_id=trace_id,
            ),
            db=db,
        )
        return AnalysisJobRef(id=job.id, status="queued")
