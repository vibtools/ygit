from __future__ import annotations

import time
from typing import Any

from fastapi import Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import Settings, get_settings
from backend.engines.auth_engine.errors import (
    AdminRoleRequiredError,
    AuthConfigurationError,
    AuthInvalidSessionError,
    AuthOidcCallbackFailedError,
    AuthRequiredError,
    AuthRoleRequiredError,
    AuthUserSyncFailedError,
)
from backend.engines.auth_engine.internal.oidc import OIDCClient
from backend.engines.auth_engine.internal.pkce import generate_code_verifier
from backend.engines.auth_engine.internal.redirects import validate_local_next_path
from backend.engines.auth_engine.internal.session_store import (
    AuthSessionManager,
    MemoryJsonSessionStore,
    RedisJsonSessionStore,
)
from backend.engines.auth_engine.repository import AuthRepository
from backend.engines.auth_engine.schemas import CurrentUser, LogoutResult, OIDCUserClaims, UserRecord

ADMIN_ROLES = frozenset({"ygit_admin", "ygit_support", "ygit_readonly"})


class AuthInternalService:
    def __init__(
        self,
        *,
        settings: Settings | None = None,
        repository: AuthRepository | None = None,
        session_manager: AuthSessionManager | None = None,
        oidc_client: OIDCClient | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.repository = repository or AuthRepository()
        self.session_manager = session_manager or self._build_session_manager(self.settings)
        self.oidc_client = oidc_client or OIDCClient(self.settings)

    def _build_session_manager(self, settings: Settings) -> AuthSessionManager:
        if settings.app_env == "test" or not settings.redis_url:
            store = MemoryJsonSessionStore()
        else:
            try:
                store = RedisJsonSessionStore(settings.redis_url)
            except ModuleNotFoundError:
                if settings.app_env == "production":
                    raise
                store = MemoryJsonSessionStore()
        return AuthSessionManager(
            store=store,
            session_ttl_seconds=settings.session_ttl_seconds,
            auth_flow_ttl_seconds=settings.auth_flow_ttl_seconds,
        )

    def configure_app_state(self, app: Any) -> None:
        app.state.ygit_auth_service = self
        app.state.ygit_session_cookie_name = self.settings.session_cookie_name

    def _set_session_cookie(self, response: Response, session_id: str) -> None:
        response.set_cookie(
            key=self.settings.session_cookie_name,
            value=session_id,
            max_age=self.settings.session_ttl_seconds,
            httponly=True,
            secure=self.settings.session_cookie_secure,
            samesite=self.settings.session_cookie_samesite,
            path="/",
        )

    def _delete_session_cookie(self, response: Response) -> None:
        response.delete_cookie(
            key=self.settings.session_cookie_name,
            path="/",
            secure=self.settings.session_cookie_secure,
            httponly=True,
            samesite=self.settings.session_cookie_samesite,
        )

    async def build_login_redirect(self, request: Request, *, next_path: str | None) -> RedirectResponse:
        safe_next = validate_local_next_path(next_path, self.settings.post_login_redirect_path)
        nonce = generate_code_verifier()
        code_verifier = generate_code_verifier()
        state = await self.session_manager.create_login_flow(
            {
                "nonce": nonce,
                "code_verifier": code_verifier,
                "next_path": safe_next,
                "client_ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
                "trace_id": getattr(request.state, "trace_id", None),
            }
        )
        authorization_url = await self.oidc_client.build_authorization_url(
            state=state,
            nonce=nonce,
            code_verifier=code_verifier,
        )
        return RedirectResponse(authorization_url, status_code=status.HTTP_302_FOUND)

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
        if error:
            raise AuthOidcCallbackFailedError(error_description or error)
        if not code or not state:
            raise AuthOidcCallbackFailedError("Missing OIDC code or state.")
        flow = await self.session_manager.pop_login_flow(state)
        if flow is None:
            raise AuthOidcCallbackFailedError("Invalid or expired OIDC state.")

        code_verifier = str(flow.get("code_verifier") or "")
        nonce = str(flow.get("nonce") or "")
        next_path = validate_local_next_path(
            str(flow.get("next_path") or ""), self.settings.post_login_redirect_path
        )

        token_response = await self.oidc_client.exchange_code(code=code, code_verifier=code_verifier)
        if not token_response.id_token:
            raise AuthOidcCallbackFailedError("OIDC ID token missing.")
        claims = await self.oidc_client.validate_id_token(token_response.id_token, nonce=nonce)
        userinfo = None
        if token_response.access_token:
            userinfo = await self.oidc_client.userinfo(token_response.access_token)
        oidc_user = self.oidc_client.build_user_claims(claims=claims, userinfo=userinfo)
        user_record = await self.sync_identity_from_oidc(db=db, claims=oidc_user)
        await db.commit()

        current_user = CurrentUser(
            id=user_record.id,
            email=user_record.email,
            name=user_record.name,
            roles=oidc_user.roles,
            status=user_record.status,
        )
        if current_user.status != "active":
            raise AuthRoleRequiredError()

        expires_at = None
        if token_response.expires_in:
            expires_at = int(time.time()) + int(token_response.expires_in)
        session_id = await self.session_manager.create_session(
            {
                "user": current_user.model_dump(mode="json"),
                "access_token": token_response.access_token,
                "refresh_token": token_response.refresh_token,
                "id_token": token_response.id_token,
                "expires_at": expires_at,
                "token_type": token_response.token_type,
                "trace_id": getattr(request.state, "trace_id", None),
            }
        )
        response = RedirectResponse(next_path, status_code=status.HTTP_302_FOUND)
        self._set_session_cookie(response, session_id)
        return response

    async def logout_user(self, request: Request, response: Response) -> LogoutResult:
        session_id = request.cookies.get(self.settings.session_cookie_name)
        if session_id:
            await self.session_manager.delete_session(session_id)
        self._delete_session_cookie(response)
        return LogoutResult(logged_out=True)

    async def get_current_user(self, request: Request) -> CurrentUser:
        session_id = request.cookies.get(self.settings.session_cookie_name)
        if not session_id:
            raise AuthRequiredError()
        payload = await self.session_manager.get_session(session_id)
        if payload is None:
            raise AuthSessionExpiredError()
        user_payload = payload.get("user")
        if not isinstance(user_payload, dict):
            raise AuthInvalidSessionError()
        user = CurrentUser.model_validate(user_payload)
        if user.status != "active":
            raise AuthRoleRequiredError()
        return user

    async def require_user(self, request: Request) -> CurrentUser:
        return await self.get_current_user(request)

    async def require_admin(self, request: Request) -> CurrentUser:
        user = await self.require_user(request)
        if not ADMIN_ROLES.intersection(set(user.roles)):
            raise AdminRoleRequiredError()
        return user

    async def require_roles(self, request: Request, roles: set[str]) -> CurrentUser:
        user = await self.require_user(request)
        if not roles.intersection(set(user.roles)):
            raise AuthRoleRequiredError()
        return user

    async def sync_identity_from_oidc(
        self,
        *,
        db: AsyncSession,
        claims: OIDCUserClaims,
    ) -> UserRecord:
        try:
            return await self.repository.sync_identity_from_oidc(
                db,
                claims=claims,
                provider_realm=self.settings.keycloak_realm,
            )
        except Exception as exc:
            await db.rollback()
            raise AuthUserSyncFailedError() from exc

    async def health(self) -> dict[str, str]:
        metadata = await self.oidc_client.metadata()
        if metadata.issuer.rstrip("/") != str(self.settings.keycloak_issuer).rstrip("/"):
            raise AuthConfigurationError("OIDC issuer discovery did not match configured issuer.")
        return {
            "status": "ok",
            "issuer": metadata.issuer,
            "client_id": self.settings.keycloak_client_id,
        }
