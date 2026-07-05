from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request

from backend.app.admin_surface.service import admin_operations_service
from backend.app.dependencies.auth import require_admin
from backend.core.database import get_db_session
from backend.core.responses import success_response
from backend.engines.auth_engine.schemas import CurrentUser
from backend.engines.audit_engine.public import audit_service
from backend.engines.audit_engine.schemas import AuditLogFilters
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/admin", tags=["Admin"])


def _meta(request: Request) -> dict[str, str | None]:
    return {"trace_id": getattr(request.state, "trace_id", None)}


@router.get("/overview")
async def overview(request: Request, user: CurrentUser = Depends(require_admin)):
    result = await admin_operations_service.get_overview()
    return success_response({"overview": result.model_dump(mode="json")}, meta=_meta(request))


@router.get("/platform/health")
async def platform_health(request: Request, user: CurrentUser = Depends(require_admin)):
    result = await admin_operations_service.get_overview()
    return success_response({"health": [item.model_dump(mode="json") for item in result.health]}, meta=_meta(request))


@router.get("/queue/status")
async def queue_status(request: Request, user: CurrentUser = Depends(require_admin)):
    result = await admin_operations_service.get_queue_status()
    return success_response({"queue": result.model_dump(mode="json")}, meta=_meta(request))


@router.get("/system-monitoring")
async def system_monitoring(request: Request, user: CurrentUser = Depends(require_admin)):
    result = await admin_operations_service.get_system_monitoring()
    return success_response({"system": result.model_dump(mode="json")}, meta=_meta(request))


@router.get("/deployments")
async def deployments(request: Request, user: CurrentUser = Depends(require_admin)):
    result = await admin_operations_service.list_deployments()
    return success_response({"items": [item.model_dump(mode="json") for item in result]}, meta=_meta(request))


@router.get("/users")
async def users(request: Request, user: CurrentUser = Depends(require_admin)):
    result = await admin_operations_service.list_users()
    return success_response({"items": [item.model_dump(mode="json") for item in result]}, meta=_meta(request))


@router.get("/audit-logs")
async def audit_logs(
    request: Request,
    event_name: str | None = None,
    actor_user_id: str | None = None,
    actor_type: str | None = None,
    target_type: str | None = None,
    target_id: str | None = None,
    trace_id: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    user: CurrentUser = Depends(require_admin),
    db: AsyncSession = Depends(get_db_session),
):
    _ = user
    filters = AuditLogFilters(
        event_name=event_name,
        actor_user_id=actor_user_id,
        actor_type=actor_type,  # type: ignore[arg-type]
        target_type=target_type,
        target_id=target_id,
        trace_id=trace_id,
        page=page,
        page_size=page_size,
    )
    result = await audit_service.list_audit_logs(db, filters=filters)
    return success_response({"items": [item.model_dump(mode="json") for item in result.items], "pagination": {"page": result.page, "page_size": result.page_size, "total_items": result.total_items, "total_pages": result.total_pages}}, meta=_meta(request))


@router.get("/settings")
async def settings(request: Request, user: CurrentUser = Depends(require_admin)):
    result = await admin_operations_service.get_settings_summary()
    return success_response({"settings": result.model_dump(mode="json")}, meta=_meta(request))


@router.get("/manifest")
async def manifest(request: Request, user: CurrentUser = Depends(require_admin)):
    result = await admin_operations_service.get_manifest()
    return success_response({"manifest": result.model_dump(mode="json")}, meta=_meta(request))
