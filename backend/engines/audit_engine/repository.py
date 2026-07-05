from __future__ import annotations

from datetime import datetime, timezone
from math import ceil

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.ids import new_id
from backend.engines.audit_engine.errors import AuditDeleteForbiddenError, AuditLogNotFoundError
from backend.engines.audit_engine.models import AuditLogModel
from backend.engines.audit_engine.schemas import AuditLogCreate, AuditLogFilters, AuditLogPage, AuditLogRecord


class AuditLogRepository:
    """Append-only repository owned by Audit Engine only."""

    async def create(self, db: AsyncSession, *, input_data: AuditLogCreate) -> AuditLogRecord:
        model = AuditLogModel(
            id=new_id("audit"),
            event_name=input_data.event_name,
            event_version=input_data.event_version,
            actor_user_id=input_data.actor_user_id,
            actor_type=input_data.actor_type,
            target_type=input_data.target_type,
            target_id=input_data.target_id,
            ip_address=input_data.ip_address,
            user_agent=input_data.user_agent,
            trace_id=input_data.trace_id,
            metadata_=input_data.metadata or {},
            created_at=datetime.now(timezone.utc),
        )
        db.add(model)
        await db.flush()
        return self.to_record(model)

    async def get_by_id(self, db: AsyncSession, audit_id: str) -> AuditLogRecord:
        result = await db.execute(select(AuditLogModel).where(AuditLogModel.id == audit_id))
        model = result.scalar_one_or_none()
        if model is None:
            raise AuditLogNotFoundError()
        return self.to_record(model)

    async def list(self, db: AsyncSession, *, filters: AuditLogFilters) -> AuditLogPage:
        conditions = []
        if filters.event_name:
            conditions.append(AuditLogModel.event_name == filters.event_name)
        if filters.actor_user_id:
            conditions.append(AuditLogModel.actor_user_id == filters.actor_user_id)
        if filters.actor_type:
            conditions.append(AuditLogModel.actor_type == filters.actor_type)
        if filters.target_type:
            conditions.append(AuditLogModel.target_type == filters.target_type)
        if filters.target_id:
            conditions.append(AuditLogModel.target_id == filters.target_id)
        if filters.trace_id:
            conditions.append(AuditLogModel.trace_id == filters.trace_id)

        where_clause = and_(*conditions) if conditions else True
        total_result = await db.execute(select(func.count()).select_from(AuditLogModel).where(where_clause))
        total_items = int(total_result.scalar_one() or 0)
        offset = (filters.page - 1) * filters.page_size
        result = await db.execute(
            select(AuditLogModel)
            .where(where_clause)
            .order_by(AuditLogModel.created_at.desc())
            .offset(offset)
            .limit(filters.page_size)
        )
        items = [self.to_record(model) for model in result.scalars().all()]
        total_pages = ceil(total_items / filters.page_size) if total_items else 0
        return AuditLogPage(
            items=items,
            page=filters.page,
            page_size=filters.page_size,
            total_items=total_items,
            total_pages=total_pages,
        )

    async def delete_forbidden(self, db: AsyncSession, audit_id: str) -> None:
        _ = db
        _ = audit_id
        raise AuditDeleteForbiddenError()

    def to_record(self, model: AuditLogModel) -> AuditLogRecord:
        return AuditLogRecord(
            id=model.id,
            event_name=model.event_name,
            event_version=model.event_version,
            actor_user_id=model.actor_user_id,
            actor_type=model.actor_type,  # type: ignore[arg-type]
            target_type=model.target_type,
            target_id=model.target_id,
            ip_address=model.ip_address,
            user_agent=model.user_agent,
            trace_id=model.trace_id,
            metadata=model.metadata_ or {},
            created_at=model.created_at,
            immutable=True,
        )
