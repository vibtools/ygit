from __future__ import annotations

from typing import Any

from fastapi import Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.engines.auth_engine.internal.service import AuthInternalService
from backend.engines.auth_engine.schemas import CurrentUser, LogoutResult, OIDCUserClaims, UserRecord


class AuthPublicService:
    """Public Auth Engine API. Other layers must not import internal services directly."""

    def __init__(self, internal: AuthInternalService | None = None) -> None:
        self._internal = internal or AuthInternalService()

    def configure_app_state(self, app: Any) -> None:
        self._internal.configure_app_state(app)

    async def login_redirect(self, request: Request, *, next_path: str | None) -> RedirectResponse:
        return await self._internal.build_login_redirect(request, next_path=next_path)

    async def handle_callback(
        self,
        *,
        request: Request,
        db: AsyncSession,
        code: str | None,
        state: str | None,
        error: str | None,
        error_description: str | None,
    ) -> RedirectResponse:
        return await self._internal.handle_callback(
            request=request,
            db=db,
            code=code,
            state=state,
            error=error,
            error_description=error_description,
        )

    async def logout_user(self, request: Request, response: Response) -> LogoutResult:
        return await self._internal.logout_user(request, response)

    async def get_current_user(self, request: Request) -> CurrentUser:
        return await self._internal.get_current_user(request)

    async def require_user(self, request: Request) -> CurrentUser:
        return await self._internal.require_user(request)

    async def require_admin(self, request: Request) -> CurrentUser:
        return await self._internal.require_admin(request)

    async def require_roles(self, request: Request, roles: set[str]) -> CurrentUser:
        return await self._internal.require_roles(request, roles)

    async def sync_identity_from_oidc(
        self,
        *,
        db: AsyncSession,
        claims: OIDCUserClaims,
    ) -> UserRecord:
        return await self._internal.sync_identity_from_oidc(db=db, claims=claims)

    async def health(self) -> dict[str, str]:
        return await self._internal.health()


auth_service = AuthPublicService()
