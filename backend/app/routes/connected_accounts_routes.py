from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.dependencies.auth import require_user
from backend.core.database import get_db_session
from backend.core.responses import success_response
from backend.engines.auth_engine.connected_accounts_module.public import connected_accounts_service

router = APIRouter(prefix="/connected-accounts", tags=["Connected Accounts"])


@router.get("")
async def list_connected_accounts(
    user = Depends(require_user),
    db: AsyncSession = Depends(get_db_session),
):
    accounts = await connected_accounts_service.get_connected_accounts(db, user_id=user.id)
    return success_response(accounts.model_dump(mode="json"))


@router.get("/{provider}/connect")
async def connect_provider(
    provider: str,
    user = Depends(require_user),
):
    result = await connected_accounts_service.connect_provider(user_id=user.id, provider=provider)
    return success_response(result.model_dump(mode="json"))


@router.get("/{provider}/callback", status_code=status.HTTP_201_CREATED)
async def provider_callback(
    provider: str,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    error_description: str | None = Query(default=None, alias="error_description"),
    user = Depends(require_user),
    db: AsyncSession = Depends(get_db_session),
):
    result = await connected_accounts_service.handle_provider_callback(
        db,
        user_id=user.id,
        provider=provider,
        code=code,
        state=state,
        error=error,
        error_description=error_description,
    )
    return success_response(result.model_dump(mode="json"), status_code=status.HTTP_201_CREATED)


@router.delete("/{provider}")
async def disconnect_provider(
    provider: str,
    user = Depends(require_user),
    db: AsyncSession = Depends(get_db_session),
):
    result = await connected_accounts_service.disconnect_provider(db, user_id=user.id, provider=provider)
    return success_response(result.model_dump(mode="json"))
