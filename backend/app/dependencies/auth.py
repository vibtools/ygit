from __future__ import annotations

from fastapi import Request

from backend.engines.auth_engine.public import auth_service
from backend.engines.auth_engine.schemas import CurrentUser


async def require_user(request: Request) -> CurrentUser:
    return await auth_service.require_user(request)


async def require_admin(request: Request) -> CurrentUser:
    return await auth_service.require_admin(request)


async def require_roles(request: Request, roles: set[str]) -> CurrentUser:
    return await auth_service.require_roles(request, roles)
