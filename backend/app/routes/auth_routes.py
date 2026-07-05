from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db_session
from backend.core.responses import success_response
from backend.engines.auth_engine.public import auth_service

router = APIRouter(prefix="/auth", tags=["Auth"])
me_router = APIRouter(tags=["Auth"])


@router.get("/login")
async def login(request: Request, next: Annotated[str | None, Query()] = None):
    return await auth_service.login_redirect(request, next_path=next)


@router.get("/callback")
async def callback(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    code: Annotated[str | None, Query()] = None,
    state: Annotated[str | None, Query()] = None,
    error: Annotated[str | None, Query()] = None,
    error_description: Annotated[str | None, Query()] = None,
):
    return await auth_service.handle_callback(
        request=request,
        db=db,
        code=code,
        state=state,
        error=error,
        error_description=error_description,
    )


@router.post("/logout")
async def logout(request: Request):
    response = success_response(
        {"logged_out": True},
        meta={"trace_id": request.state.trace_id},
    )
    await auth_service.logout_user(request, response)
    return response


@me_router.get("/me")
async def current_user(request: Request):
    user = await auth_service.get_current_user(request)
    return success_response(
        {"user": user.model_dump(mode="json")},
        meta={"trace_id": request.state.trace_id},
    )
