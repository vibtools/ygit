from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


JobType = Literal[
    "deploy_project",
    "redeploy_project",
    "repository_analysis_deep",
    "webhook_event",
]

JobStatus = Literal[
    "queued",
    "running",
    "completed",
    "failed",
    "retry_waiting",
    "cancelled",
]

QueueName = Literal["default", "deployments", "analysis", "webhooks"]


class JobCreateInput(BaseModel):
    job_type: JobType
    queue_name: str = "default"
    payload: dict[str, Any]
    trace_id: str
    max_attempts: int = Field(default=3, ge=1, le=10)
    available_at: datetime | None = None

    @field_validator("queue_name")
    @classmethod
    def validate_queue_name(cls, value: str) -> str:
        if not value or any(ch in value for ch in " /\\\r\n\t"):
            raise ValueError("Queue name is invalid.")
        return value


class JobRecord(BaseModel):
    id: str
    job_type: JobType
    status: JobStatus
    queue_name: str
    payload: dict[str, Any]
    result: dict[str, Any] | None = None
    error_code: str | None = None
    error_summary: str | None = None
    attempts: int = 0
    max_attempts: int = 3
    locked_by: str | None = None
    locked_at: datetime | None = None
    available_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    failed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class JobRunResult(BaseModel):
    worker_id: str
    queue_name: str
    processed: bool
    job_id: str | None = None
    status: JobStatus | Literal["idle"] = "idle"
    error_code: str | None = None
    error_summary: str | None = None


class WorkerHeartbeat(BaseModel):
    worker_id: str
    queue_name: str
    status: Literal["ready", "running", "idle", "stopped"]
    checked_at: datetime
