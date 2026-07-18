from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import get_settings
from backend.engines.auth_engine.connected_accounts_module.errors import (
    ConnectedAccountNotFoundError,
    ProviderConnectionFailedError,
    ProviderNotConnectedError,
    ProviderNotSupportedError,
    ProviderOAuthFailedError,
)
from backend.engines.auth_engine.connected_accounts_module.internal.oauth_state import (
    ConnectedAccountInstallState,
    ConnectedAccountOAuthState,
    TokenReferenceFactory,
)
from backend.engines.auth_engine.connected_accounts_module.repository import ConnectedAccountRepository
from backend.engines.auth_engine.connected_accounts_module.schemas import (
    ConnectProviderResult,
    ConnectedAccountRecord,
    ConnectedAccountStatus,
    ConnectedAccountSummary,
    ConnectedAccountsList,
    DisconnectProviderResult,
    ProviderCallbackResult,
    ProviderConnectionHealth,
    ProviderName,
)
from backend.providers.cloudflare_provider.client import CloudflareProviderClient
from backend.providers.github_provider.client import GitHubProviderClient

SUPPORTED_PROVIDERS: tuple[ProviderName, ...] = ("github", "cloudflare")


class ConnectedAccountsInternalService:
    def __init__(
        self,
        *,
        repository: ConnectedAccountRepository | None = None,
        github_provider: GitHubProviderClient | None = None,
        cloudflare_provider: CloudflareProviderClient | None = None,
    ) -> None:
        self.repository = repository or ConnectedAccountRepository()
        self.github_provider = github_provider or GitHubProviderClient()
        self.cloudflare_provider = cloudflare_provider or CloudflareProviderClient()

    def parse_provider(self, provider: str) -> ProviderName:
        normalized = provider.strip().lower().replace("_", "-")
        if normalized not in SUPPORTED_PROVIDERS:
            raise ProviderNotSupportedError()
        return normalized  # type: ignore[return-value]

    async def list_connected_accounts(self, db: AsyncSession, *, user_id: str) -> ConnectedAccountsList:
        records = [self.repository.to_record(model) for model in await self.repository.list_by_user(db, user_id=user_id)]
        by_provider = {record.provider: record for record in records}
        return ConnectedAccountsList(
            accounts=[self.to_summary(by_provider.get(provider), provider=provider) for provider in SUPPORTED_PROVIDERS]
        )

    async def start_provider_connect(
        self,
        *,
        user_id: str,
        provider: str,
    ) -> ConnectProviderResult:
        provider_name = self.parse_provider(provider)
        settings = get_settings()

        if provider_name == "github":
            state = ConnectedAccountInstallState.new_state(user_id=user_id, provider=provider_name)
            authorization_url = self.github_provider.build_app_installation_url(
                install_url=str(settings.github_app_install_url),
                state=state,
            )
            return ConnectProviderResult(provider=provider_name, authorization_url=authorization_url, state=state)

        state = ConnectedAccountOAuthState.new_state(user_id=user_id, provider=provider_name)
        # Cloudflare remains placeholder-backed until its provider integration is implemented.
        redirect_base = str(settings.app_base_url).rstrip("/")
        authorization_url = f"{redirect_base}{settings.api_prefix}/connected-accounts/{provider_name}/callback?state={state}"
        return ConnectProviderResult(provider=provider_name, authorization_url=authorization_url, state=state)

    async def handle_provider_callback(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        provider: str,
        code: str | None,
        state: str | None,
        error: str | None,
        error_description: str | None,
    ) -> ProviderCallbackResult:
        provider_name = self.parse_provider(provider)
        if error:
            raise ProviderOAuthFailedError(error_description or error)
        if not code:
            raise ProviderOAuthFailedError("Provider OAuth callback is missing code.")
        if not state or not ConnectedAccountOAuthState.validate_state(
            state=state,
            user_id=user_id,
            provider=provider_name,
        ):
            raise ProviderOAuthFailedError("Provider OAuth state is invalid.")

        token_ref = TokenReferenceFactory.new_token_ref(provider=provider_name)
        validation = await self._validate_provider_account(provider_name, token_ref)
        account_name = validation.get("account_name") or f"{provider_name}-account"
        provider_account_id = validation.get("account_id") or f"{provider_name}:{user_id}"

        record = await self.repository.upsert_connected(
            db,
            user_id=user_id,
            provider=provider_name,
            provider_account_id=provider_account_id,
            provider_account_name=account_name,
            token_secret_ref=token_ref,
            token_key_version=TokenReferenceFactory.key_version(),
            scopes=self._default_scopes(provider_name),
        )
        await db.commit()
        return ProviderCallbackResult(
            provider=record.provider,
            connected=True,
            status=record.status,
            account_name=record.provider_account_name,
        )

    async def disconnect_provider(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        provider: str,
    ) -> DisconnectProviderResult:
        provider_name = self.parse_provider(provider)
        existing = await self.repository.get_by_user_provider(db, user_id=user_id, provider=provider_name)
        if existing is None:
            raise ConnectedAccountNotFoundError()
        record = await self.repository.mark_disconnected(db, user_id=user_id, provider=provider_name)
        await db.commit()
        return DisconnectProviderResult(provider=record.provider, connected=False, status=record.status)

    async def require_provider_connected(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        provider: str,
    ) -> ConnectedAccountRecord:
        provider_name = self.parse_provider(provider)
        model = await self.repository.get_by_user_provider(db, user_id=user_id, provider=provider_name)
        if model is None:
            raise ConnectedAccountNotFoundError()
        record = self.repository.to_record(model)
        if record.status != "connected" or not record.token_secret_ref:
            raise ProviderNotConnectedError()
        return record

    async def check_provider_health(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        provider: str,
    ) -> ProviderConnectionHealth:
        record = await self.require_provider_connected(db, user_id=user_id, provider=provider)
        try:
            await self._validate_provider_account(record.provider, record.token_secret_ref or "")
        except Exception as exc:  # provider errors are intentionally sanitized here
            await self.repository.mark_provider_error(
                db,
                user_id=user_id,
                provider=record.provider,
                error_code="PROVIDER_CONNECTION_FAILED",
            )
            await db.commit()
            raise ProviderConnectionFailedError() from exc
        return ProviderConnectionHealth(
            provider=record.provider,
            status="connected",
            healthy=True,
            checked_at=datetime.now(timezone.utc),
        )

    async def mark_provider_error(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        provider: str,
        error_summary: str,
    ) -> None:
        provider_name = self.parse_provider(provider)
        error_code = error_summary.strip().upper().replace(" ", "_")[:128] or "PROVIDER_ERROR"
        await self.repository.mark_provider_error(db, user_id=user_id, provider=provider_name, error_code=error_code)
        await db.commit()

    async def _validate_provider_account(self, provider: ProviderName, token_ref: str) -> dict[str, str]:
        if provider == "github":
            return await self.github_provider.validate_account(token_ref)
        return await self.cloudflare_provider.validate_account(token_ref)

    def _default_scopes(self, provider: ProviderName) -> list[str]:
        if provider == "github":
            return ["repo:read", "user:read"]
        return ["pages:write", "account:read"]

    def to_summary(
        self,
        record: ConnectedAccountRecord | None,
        *,
        provider: ProviderName,
    ) -> ConnectedAccountSummary:
        if record is None:
            return ConnectedAccountSummary(
                provider=provider,
                connected=False,
                status="disconnected",
                account_name=None,
                connected_at=None,
            )
        connected = record.status == "connected"
        status: ConnectedAccountStatus = record.status
        return ConnectedAccountSummary(
            provider=record.provider,
            connected=connected,
            status=status,
            account_name=record.provider_account_name if connected else None,
            connected_at=record.connected_at if connected else None,
            last_error_code=record.last_error_code,
        )
