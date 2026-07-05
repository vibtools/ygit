from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from backend.app.dependencies.auth import require_user
from backend.core.responses import success_response
from backend.engines.auth_engine.schemas import CurrentUser
from backend.engines.platform_engine.public import platform_service

router = APIRouter(prefix="/platform", tags=["Platform"])


def _meta(request: Request) -> dict[str, str | None]:
    return {"trace_id": getattr(request.state, "trace_id", None)}


@router.get("/health")
async def health(request: Request):
    result = await platform_service.get_health()
    return success_response(result.model_dump(mode="json"), meta=_meta(request))


@router.get("/version")
async def version(request: Request):
    result = await platform_service.get_version()
    return success_response(result.model_dump(mode="json"), meta=_meta(request))


@router.get("/status")
async def status(request: Request, user: CurrentUser = Depends(require_user)):
    _ = user
    result = await platform_service.get_system_status()
    return success_response(result.model_dump(mode="json"), meta=_meta(request))


@router.get("/feature-flags")
async def feature_flags(request: Request, user: CurrentUser = Depends(require_user)):
    _ = user
    result = await platform_service.get_feature_flags()
    return success_response({"flags": result.flags, "items": [item.model_dump(mode="json") for item in result.items]}, meta=_meta(request))
