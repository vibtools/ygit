from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from backend.engines.audit_engine.internal.service import AuditInternalService
from backend.engines.audit_engine.schemas import AuditEventEnvelopeInput, AuditLogCreate, AuditLogFilters, AuditLogPage, AuditLogRecord
from backend.shared.events.envelope import EventEnvelope


class AuditPublicService:
    """Public Audit Engine API. External consumers must not import internals."""

    def __init__(self, internal: AuditInternalService | None = None) -> None:
        self._internal = internal or AuditInternalService()

    async def record_event(self, db: AsyncSession, *, input_data: AuditLogCreate) -> AuditLogRecord:
        return await self._internal.record_event(db, input_data=input_data)

    async def record_envelope(
        self,
        db: AsyncSession,
        *,
        event: EventEnvelope | AuditEventEnvelopeInput,
        actor_type: str = "system",
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLogRecord:
        return await self._internal.record_envelope(
            db,
            event=event,
            actor_type=actor_type,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def get_audit_log(self, db: AsyncSession, *, audit_id: str) -> AuditLogRecord:
        return await self._internal.get_audit_log(db, audit_id=audit_id)

    async def list_audit_logs(self, db: AsyncSession, *, filters: AuditLogFilters) -> AuditLogPage:
        return await self._internal.list_audit_logs(db, filters=filters)

    async def delete_audit_log_forbidden(self, db: AsyncSession, *, audit_id: str) -> None:
        await self._internal.delete_audit_log_forbidden(db, audit_id=audit_id)


audit_service = AuditPublicService()
