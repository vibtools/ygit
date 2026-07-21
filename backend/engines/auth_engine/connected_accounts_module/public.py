from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from backend.engines.auth_engine.connected_accounts_module.internal.service import ConnectedAccountsInternalService
from backend.engines.auth_engine.connected_accounts_module.schemas import (
    ConnectProviderResult,
    ConnectedAccountRecord,
    ConnectedAccountsList,
    DisconnectProviderResult,
    ProviderCallbackResult,
    ProviderConnectionHealth,
    ResolvedProviderCredential,
)


class ConnectedAccountsPublicService:
    """Public Connected Accounts Module API.

    This module belongs under Auth Engine. Other engines may call this public API only;
    internal services and repositories remain module-private.
    """

    def __init__(self, internal: ConnectedAccountsInternalService | None = None) -> None:
        self._internal = internal or ConnectedAccountsInternalService()

    async def get_connected_accounts(self, db: AsyncSession, *, user_id: str) -> ConnectedAccountsList:
        return await self._internal.list_connected_accounts(db, user_id=user_id)

    async def connect_provider(self, *, user_id: str, provider: str) -> ConnectProviderResult:
        return await self._internal.start_provider_connect(user_id=user_id, provider=provider)

    async def handle_provider_callback(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        provider: str,
        code: str | None,
        state: str | None,
        installation_id: str | None = None,
        error: str | None = None,
        error_description: str | None = None,
    ) -> ProviderCallbackResult:
        return await self._internal.handle_provider_callback(
            db,
            user_id=user_id,
            provider=provider,
            code=code,
            state=state,
            installation_id=installation_id,
            error=error,
            error_description=error_description,
        )

    async def disconnect_provider(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        provider: str,
    ) -> DisconnectProviderResult:
        return await self._internal.disconnect_provider(db, user_id=user_id, provider=provider)

    async def require_provider_connected(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        provider: str,
    ) -> ConnectedAccountRecord:
        return await self._internal.require_provider_connected(db, user_id=user_id, provider=provider)

    async def resolve_cloudflare_credential(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        token_secret_ref: str,
    ) -> ResolvedProviderCredential:
        return await self._internal.resolve_cloudflare_credential(
            db,
            user_id=user_id,
            token_secret_ref=token_secret_ref,
        )

    async def acquire_cloudflare_deployment_credential(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        token_secret_ref: str,
    ) -> ResolvedProviderCredential:
        return (
            await self._internal
            .acquire_cloudflare_deployment_credential(
                db,
                user_id=user_id,
                token_secret_ref=token_secret_ref,
            )
        )

    async def refresh_cloudflare_credential(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        token_secret_ref: str,
    ) -> ResolvedProviderCredential:
        return await self._internal.refresh_cloudflare_credential(
            db,
            user_id=user_id,
            token_secret_ref=token_secret_ref,
        )

    async def check_provider_health(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        provider: str,
    ) -> ProviderConnectionHealth:
        return await self._internal.check_provider_health(db, user_id=user_id, provider=provider)

    async def mark_provider_error(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        provider: str,
        error_summary: str,
    ) -> None:
        await self._internal.mark_provider_error(
            db,
            user_id=user_id,
            provider=provider,
            error_summary=error_summary,
        )


connected_accounts_service = ConnectedAccountsPublicService()
