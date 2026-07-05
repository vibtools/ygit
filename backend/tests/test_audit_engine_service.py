from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from backend.engines.audit_engine.errors import AuditDeleteForbiddenError, AuditEventInvalidError
from backend.engines.audit_engine.internal.service import AuditInternalService
from backend.engines.audit_engine.schemas import AuditLogCreate, AuditLogFilters, AuditLogPage, AuditLogRecord
from backend.shared.events.envelope import EventEnvelope


class FakeDB:
    def __init__(self) -> None:
        self.committed = False

    async def commit(self) -> None:
        self.committed = True


class FakeAuditRepository:
    def __init__(self) -> None:
        self.created: list[AuditLogCreate] = []
        self.records: dict[str, AuditLogRecord] = {}

    async def create(self, db, *, input_data: AuditLogCreate) -> AuditLogRecord:
        self.created.append(input_data)
        record = AuditLogRecord(
            id="audit_1",
            event_name=input_data.event_name,
            event_version=input_data.event_version,
            actor_user_id=input_data.actor_user_id,
            actor_type=input_data.actor_type,
            target_type=input_data.target_type,
            target_id=input_data.target_id,
            ip_address=input_data.ip_address,
            user_agent=input_data.user_agent,
            trace_id=input_data.trace_id,
            metadata=input_data.metadata,
            created_at=datetime.now(timezone.utc),
            immutable=True,
        )
        self.records[record.id] = record
        return record

    async def get_by_id(self, db, audit_id: str) -> AuditLogRecord:
        return self.records[audit_id]

    async def list(self, db, *, filters: AuditLogFilters) -> AuditLogPage:
        return AuditLogPage(items=list(self.records.values()), page=filters.page, page_size=filters.page_size, total_items=len(self.records), total_pages=1 if self.records else 0)


@pytest.mark.asyncio
async def test_record_event_sanitizes_secret_metadata_and_commits() -> None:
    db = FakeDB()
    repository = FakeAuditRepository()
    service = AuditInternalService(repository=repository)  # type: ignore[arg-type]
    result = await service.record_event(
        db,
        input_data=AuditLogCreate(
            event_name="project.created",
            actor_user_id="user_1",
            actor_type="user",
            target_type="project",
            target_id="proj_1",
            trace_id="trace_1",
            metadata={"token": "redacted_value", "nested": {"client_secret": "hidden", "safe": "ok"}},
        ),
    )
    assert result.id == "audit_1"
    assert result.metadata == {"token": "[REDACTED]", "nested": {"client_secret": "[REDACTED]", "safe": "ok"}}
    assert db.committed is True


@pytest.mark.asyncio
async def test_invalid_event_name_is_rejected() -> None:
    service = AuditInternalService(repository=FakeAuditRepository())  # type: ignore[arg-type]
    with pytest.raises(AuditEventInvalidError):
        await service.record_event(
            FakeDB(),
            input_data=AuditLogCreate(event_name="PROJECT_CREATED", actor_type="system", trace_id="trace_1"),
        )


@pytest.mark.asyncio
async def test_record_envelope_maps_event_to_audit_log() -> None:
    repository = FakeAuditRepository()
    service = AuditInternalService(repository=repository)  # type: ignore[arg-type]
    envelope = EventEnvelope(
        event_name="deployment.failed",
        actor_user_id="user_1",
        target_type="deployment",
        target_id="dep_1",
        trace_id="trace_1",
        metadata={"failure_code": "DEPLOY_PIPELINE_CLOUDFLARE_FAILED"},
    )
    result = await service.record_envelope(FakeDB(), event=envelope, actor_type="worker")
    assert result.event_name == "deployment.failed"
    assert result.actor_type == "worker"
    assert result.target_id == "dep_1"


@pytest.mark.asyncio
async def test_delete_audit_log_is_forbidden() -> None:
    service = AuditInternalService(repository=FakeAuditRepository())  # type: ignore[arg-type]
    with pytest.raises(AuditDeleteForbiddenError):
        await service.delete_audit_log_forbidden(FakeDB(), audit_id="audit_1")
