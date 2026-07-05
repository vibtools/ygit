from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from backend.core.ids import new_id


QueueJobType = Literal[
    "deploy_project",
    "redeploy_project",
    "repository_analysis_deep",
    "webhook_event",
]


class JobRef(BaseModel):
    id: str = Field(default_factory=lambda: new_id("job"))
    type: QueueJobType
    status: Literal["queued", "running", "completed", "failed", "retry_waiting", "cancelled"] = "queued"


class JobPayload(BaseModel):
    job_type: QueueJobType
    payload: dict[str, Any]
    trace_id: str
