from __future__ import annotations

from math import ceil

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.ids import new_id
from backend.engines.notification_engine.errors import NotificationChannelUnsupportedError, NotificationNotFoundError
from backend.engines.notification_engine.repository import NotificationRepository
from backend.engines.notification_engine.schemas import (
    Notification,
    NotificationCreateInput,
    NotificationEventInput,
    NotificationFilters,
    NotificationPage,
    UnreadCount,
)


class NotificationInternalService:
    """Internal implementation for Notification Engine.

    MVP supports in-app notifications only. This service must not call providers,
    mutate project/deployment state, or write another engine's tables directly.
    """

    def __init__(self, repository: NotificationRepository | None = None) -> None:
        self.repository = repository or NotificationRepository()

    async def create_notification(
        self,
        db: AsyncSession | None,
        *,
        user_id: str,
        input_data: NotificationCreateInput,
    ) -> Notification:
        if input_data.channel != "in_app":
            raise NotificationChannelUnsupportedError()
        if db is None:
            return Notification(
                id=new_id("notif"),
                user_id=user_id,
                type=input_data.type,
                title=input_data.title,
                message=input_data.message,
                severity=input_data.severity,
                status="unread",
                related_resource_type=input_data.related_resource_type,
                related_resource_id=input_data.related_resource_id,
                metadata=input_data.metadata,
            )
        model = await self.repository.create(db, user_id=user_id, input_data=input_data)
        return self.repository.to_schema(model)

    async def create_from_event(
        self,
        db: AsyncSession | None,
        *,
        event: NotificationEventInput,
    ) -> Notification:
        input_data = NotificationCreateInput(
            type=event.type,
            title=event.title,
            message=event.message,
            severity=event.severity,
            related_resource_type=event.related_resource_type,
            related_resource_id=event.related_resource_id,
            metadata={"source_event": event.event_name, **event.metadata},
        )
        return await self.create_notification(db, user_id=event.recipient_user_id, input_data=input_data)

    async def list_notifications(
        self,
        db: AsyncSession | None,
        *,
        user_id: str,
        filters: NotificationFilters,
    ) -> NotificationPage:
        if db is None:
            return NotificationPage(items=[], page=filters.page, page_size=filters.page_size, total_items=0, total_pages=0)
        rows, total = await self.repository.list_for_user(db, user_id=user_id, filters=filters)
        total_pages = ceil(total / filters.page_size) if total else 0
        return NotificationPage(
            items=[self.repository.to_schema(row) for row in rows],
            page=filters.page,
            page_size=filters.page_size,
            total_items=total,
            total_pages=total_pages,
        )

    async def mark_notification_read(
        self,
        db: AsyncSession | None,
        *,
        user_id: str,
        notification_id: str,
    ) -> Notification:
        if db is None:
            return Notification(
                id=notification_id,
                user_id=user_id,
                type="system_notice",
                title="Notification read",
                message="Notification marked read in contract-only mode.",
                severity="info",
                status="read",
            )
        model = await self.repository.get_for_user(db, user_id=user_id, notification_id=notification_id)
        if model is None:
            raise NotificationNotFoundError()
        updated = await self.repository.mark_read(db, model=model)
        return self.repository.to_schema(updated)

    async def get_unread_count(self, db: AsyncSession | None, *, user_id: str) -> UnreadCount:
        if db is None:
            return UnreadCount(unread_count=0)
        return UnreadCount(unread_count=await self.repository.unread_count(db, user_id=user_id))
