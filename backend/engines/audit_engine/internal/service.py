from __future__ import annotations

import re
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.engines.audit_engine.errors import AuditDeleteForbiddenError, AuditEventInvalidError, AuditLogWriteFailedError
from backend.engines.audit_engine.repository import AuditLogRepository
from backend.engines.audit_engine.schemas import (
    AuditEventEnvelopeInput,
    AuditLogCreate,
    AuditLogFilters,
    AuditLogPage,
    AuditLogRecord,
)
from backend.shared.events.envelope import EventEnvelope

EVENT_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$")
SECRET_KEYWORDS = {
    "authorization",
    "cookie",
    "password",
    "secret",
    "session",
    "token",
    "token_ciphertext",
    "token_secret_ref",
    "refresh_token",
    "access_token",
    "client_secret",
    "database_password",
}


class AuditInternalService:
    """Internal Audit Engine service. External consumers must use public.py."""

    def __init__(self, repository: AuditLogRepository | None = None) -> None:
        self._repository = repository or AuditLogRepository()

    async def record_event(self, db: AsyncSession, *, input_data: AuditLogCreate) -> AuditLogRecord:
        self._validate_event_name(input_data.event_name)
        safe_input = input_data.model_copy(update={"metadata": self._sanitize_metadata(input_data.metadata or {})})
        try:
            record = await self._repository.create(db, input_data=safe_input)
            await db.commit()
            return record
        except AuditEventInvalidError:
            raise
        except Exception as exc:  # pragma: no cover - defensive runtime mapping
            raise AuditLogWriteFailedError() from exc

    async def record_envelope(
        self,
        db: AsyncSession,
        *,
        event: EventEnvelope | AuditEventEnvelopeInput,
        actor_type: str = "system",
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLogRecord:
        input_data = AuditLogCreate(
            event_name=event.event_name,
            event_version=getattr(event, "event_version", "1.0"),
            actor_user_id=event.actor_user_id,
            actor_type=actor_type,  # type: ignore[arg-type]
            target_type=event.target_type,
            target_id=event.target_id,
            ip_address=ip_address,
            user_agent=user_agent,
            trace_id=event.trace_id,
            metadata=getattr(event, "metadata", {}) or {},
        )
        return await self.record_event(db, input_data=input_data)

    async def get_audit_log(self, db: AsyncSession, *, audit_id: str) -> AuditLogRecord:
        return await self._repository.get_by_id(db, audit_id)

    async def list_audit_logs(self, db: AsyncSession, *, filters: AuditLogFilters) -> AuditLogPage:
        return await self._repository.list(db, filters=filters)

    async def delete_audit_log_forbidden(self, db: AsyncSession, *, audit_id: str) -> None:
        _ = db
        _ = audit_id
        raise AuditDeleteForbiddenError()

    def _validate_event_name(self, event_name: str) -> None:
        if not EVENT_NAME_PATTERN.match(event_name):
            raise AuditEventInvalidError()
        if len(event_name) > 160:
            raise AuditEventInvalidError()

    def _sanitize_metadata(self, value: Any) -> Any:
        if isinstance(value, dict):
            result: dict[str, Any] = {}
            for key, item in value.items():
                normalized = str(key).lower()
                if any(secret in normalized for secret in SECRET_KEYWORDS):
                    result[str(key)] = "[REDACTED]"
                else:
                    result[str(key)] = self._sanitize_metadata(item)
            return result
        if isinstance(value, list):
            return [self._sanitize_metadata(item) for item in value]
        return value
