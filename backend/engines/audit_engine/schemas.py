from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field

AuditActorType = Literal["user", "admin", "system", "worker"]


class AuditLogCreate(BaseModel):
    event_name: str
    event_version: str = "1.0"
    actor_user_id: str | None = None
    actor_type: AuditActorType = "system"
    target_type: str | None = None
    target_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    trace_id: str
    metadata: dict[str, Any] | None = Field(default_factory=dict)


class AuditLogRecord(BaseModel):
    id: str
    event_name: str
    event_version: str
    actor_user_id: str | None
    actor_type: AuditActorType
    target_type: str | None
    target_id: str | None
    ip_address: str | None
    user_agent: str | None
    trace_id: str
    metadata: dict[str, Any] | None = Field(default_factory=dict)
    created_at: datetime
    immutable: bool = True


class AuditLogFilters(BaseModel):
    event_name: str | None = None
    actor_user_id: str | None = None
    actor_type: AuditActorType | None = None
    target_type: str | None = None
    target_id: str | None = None
    trace_id: str | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class AuditLogPage(BaseModel):
    items: list[AuditLogRecord]
    page: int
    page_size: int
    total_items: int
    total_pages: int


class AuditWriteResult(BaseModel):
    accepted: bool = True
    audit_log: AuditLogRecord


class AuditDeleteResult(BaseModel):
    deleted: bool = False
    reason: str = "Audit logs are immutable and cannot be deleted."


class AuditEventEnvelopeInput(BaseModel):
    event_id: str
    event_name: str
    event_version: str = "1.0"
    actor_user_id: str | None = None
    target_type: str | None = None
    target_id: str | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    trace_id: str
    metadata: dict[str, Any] | None = Field(default_factory=dict)
