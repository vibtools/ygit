from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.ids import new_id
from backend.engines.notification_engine.models import NotificationModel
from backend.engines.notification_engine.schemas import Notification, NotificationCreateInput, NotificationFilters


class NotificationRepository:
    """Database repository owned by Notification Engine.

    External consumers must use Notification Engine public service. Direct imports of
    this repository from API routes, worker runtime, providers, or other engines are forbidden.
    """

    async def create(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        input_data: NotificationCreateInput,
    ) -> NotificationModel:
        model = NotificationModel(
            id=new_id("notif"),
            user_id=user_id,
            type=input_data.type,
            title=input_data.title,
            message=input_data.message,
            severity=input_data.severity,
            status="unread",
            channel=input_data.channel,
            delivery_status="delivered",
            related_resource_type=input_data.related_resource_type,
            related_resource_id=input_data.related_resource_id,
            metadata_json=input_data.metadata,
        )
        db.add(model)
        await db.flush()
        return model

    async def list_for_user(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        filters: NotificationFilters,
    ) -> tuple[list[NotificationModel], int]:
        stmt = select(NotificationModel).where(NotificationModel.user_id == user_id)
        count_stmt = select(func.count(NotificationModel.id)).where(NotificationModel.user_id == user_id)
        if filters.status:
            stmt = stmt.where(NotificationModel.status == filters.status)
            count_stmt = count_stmt.where(NotificationModel.status == filters.status)
        if filters.type:
            stmt = stmt.where(NotificationModel.type == filters.type)
            count_stmt = count_stmt.where(NotificationModel.type == filters.type)
        stmt = stmt.order_by(NotificationModel.created_at.desc()).offset((filters.page - 1) * filters.page_size).limit(filters.page_size)
        items_result = await db.execute(stmt)
        count_result = await db.execute(count_stmt)
        return list(items_result.scalars().all()), int(count_result.scalar_one() or 0)

    async def get_for_user(self, db: AsyncSession, *, user_id: str, notification_id: str) -> NotificationModel | None:
        result = await db.execute(
            select(NotificationModel).where(NotificationModel.id == notification_id, NotificationModel.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def mark_read(self, db: AsyncSession, *, model: NotificationModel) -> NotificationModel:
        model.status = "read"
        model.read_at = datetime.now(timezone.utc)
        await db.flush()
        return model

    async def unread_count(self, db: AsyncSession, *, user_id: str) -> int:
        result = await db.execute(
            select(func.count(NotificationModel.id)).where(
                NotificationModel.user_id == user_id,
                NotificationModel.status == "unread",
            )
        )
        return int(result.scalar_one() or 0)

    def to_schema(self, model: NotificationModel) -> Notification:
        return Notification(
            id=model.id,
            user_id=model.user_id,
            type=model.type,  # type: ignore[arg-type]
            title=model.title,
            message=model.message,
            severity=model.severity,  # type: ignore[arg-type]
            status=model.status,  # type: ignore[arg-type]
            channel="in_app",
            delivery_status=model.delivery_status,
            related_resource_type=model.related_resource_type,
            related_resource_id=model.related_resource_id,
            metadata=dict(model.metadata_json or {}),
            created_at=model.created_at,
            updated_at=model.updated_at,
            read_at=model.read_at,
        )
