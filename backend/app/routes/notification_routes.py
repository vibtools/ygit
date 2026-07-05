from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.dependencies.auth import require_user
from backend.core.database import get_db_session
from backend.core.responses import success_response
from backend.engines.auth_engine.schemas import CurrentUser
from backend.engines.notification_engine.public import notification_service
from backend.engines.notification_engine.schemas import NotificationFilters, NotificationStatus, NotificationType

router = APIRouter(prefix="/notifications", tags=["Notifications"])


def _meta(request: Request) -> dict[str, str | None]:
    return {"trace_id": getattr(request.state, "trace_id", None)}


@router.get("")
async def list_notifications(
    request: Request,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: NotificationStatus | None = None,
    type: NotificationType | None = None,
    user: CurrentUser = Depends(require_user),
    db: AsyncSession = Depends(get_db_session),
):
    filters = NotificationFilters(page=page, page_size=page_size, status=status, type=type)
    result = await notification_service.list_notifications(db, user_id=user.id, filters=filters)
    return success_response(
        {
            "items": [item.model_dump(mode="json") for item in result.items],
            "pagination": {
                "page": result.page,
                "page_size": result.page_size,
                "total_items": result.total_items,
                "total_pages": result.total_pages,
            },
        },
        meta=_meta(request),
    )


@router.get("/unread-count")
async def unread_count(
    request: Request,
    user: CurrentUser = Depends(require_user),
    db: AsyncSession = Depends(get_db_session),
):
    result = await notification_service.get_unread_count(db, user_id=user.id)
    return success_response(result.model_dump(mode="json"), meta=_meta(request))


@router.patch("/{notification_id}/read")
async def mark_read(
    notification_id: str,
    request: Request,
    user: CurrentUser = Depends(require_user),
    db: AsyncSession = Depends(get_db_session),
):
    result = await notification_service.mark_notification_read(db, user_id=user.id, notification_id=notification_id)
    return success_response({"notification": result.model_dump(mode="json")}, meta=_meta(request))
