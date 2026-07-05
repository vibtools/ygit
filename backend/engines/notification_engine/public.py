from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from backend.engines.notification_engine.internal.service import NotificationInternalService
from backend.engines.notification_engine.schemas import (
    Notification,
    NotificationCreateInput,
    NotificationEventInput,
    NotificationFilters,
    NotificationPage,
    UnreadCount,
)


class NotificationPublicService:
    """Public Notification Engine API.

    Approved consumers: API routes, Deploy Engine, Deploy Pipeline, Deployment History
    Engine, Worker/Job Runner, Platform Engine, and Audit Engine through public service
    contracts. Consumers must not import Notification Engine internals, repository, or
    models directly.
    """

    def __init__(self, internal: NotificationInternalService | None = None) -> None:
        self.internal = internal or NotificationInternalService()

    async def create_notification(
        self,
        db: AsyncSession | None,
        *,
        user_id: str,
        input_data: NotificationCreateInput,
    ) -> Notification:
        return await self.internal.create_notification(db, user_id=user_id, input_data=input_data)

    async def create_from_event(
        self,
        db: AsyncSession | None,
        *,
        event: NotificationEventInput,
    ) -> Notification:
        return await self.internal.create_from_event(db, event=event)

    async def list_notifications(
        self,
        db: AsyncSession | None,
        *,
        user_id: str,
        filters: NotificationFilters,
    ) -> NotificationPage:
        return await self.internal.list_notifications(db, user_id=user_id, filters=filters)

    async def mark_notification_read(
        self,
        db: AsyncSession | None,
        *,
        user_id: str,
        notification_id: str,
    ) -> Notification:
        return await self.internal.mark_notification_read(db, user_id=user_id, notification_id=notification_id)

    async def get_unread_count(self, db: AsyncSession | None, *, user_id: str) -> UnreadCount:
        return await self.internal.get_unread_count(db, user_id=user_id)


notification_service = NotificationPublicService()
