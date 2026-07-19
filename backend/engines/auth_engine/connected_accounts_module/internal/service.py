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
        if settings.cloudflare_oauth_client_id:
            authorization_url = self.cloudflare_provider.build_oauth_authorization_url(
                client_id=settings.cloudflare_oauth_client_id,
                redirect_uri=settings.cloudflare_oauth_redirect_uri,
                scopes=settings.cloudflare_oauth_scopes,
                state=state,
            )
        else:
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
        installation_id: str | None = None,
        error: str | None = None,
        error_description: str | None = None,
    ) -> ProviderCallbackResult:
        provider_name = self.parse_provider(provider)
        if error:
            raise ProviderOAuthFailedError(error_description or error)

        if provider_name == "github":
            return await self._handle_github_app_callback(
                db,
                user_id=user_id,
                state=state,
                installation_id=installation_id,
            )

        return await self._handle_cloudflare_oauth_callback(
            db,
            user_id=user_id,
            state=state,
            code=code,
        )

    async def _handle_cloudflare_oauth_callback(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        state: str | None,
        code: str | None,
    ) -> ProviderCallbackResult:
        provider_name: ProviderName = "cloudflare"

        if not code:
            raise ProviderOAuthFailedError("Cloudflare OAuth callback is missing code.")
        if not state or not ConnectedAccountOAuthState.validate_state(
            state=state,
            user_id=user_id,
            provider=provider_name,
        ):
            raise ProviderOAuthFailedError("Cloudflare OAuth state is invalid.")

        settings = get_settings()
        has_oauth_config = bool(
            settings.cloudflare_oauth_client_id
            and settings.cloudflare_oauth_client_secret.get_secret_value()
        )
        provider_supports_oauth = bool(
            hasattr(self.cloudflare_provider, "exchange_oauth_code")
            and hasattr(self.cloudflare_provider, "validate_oauth_access")
        )

        if has_oauth_config and provider_supports_oauth:
            exchange_kwargs = {
                "code_value": code,
                "client_id": settings.cloudflare_oauth_client_id,
                "client_secret": settings.cloudflare_oauth_client_secret.get_secret_value(),
                "redirect_uri": settings.cloudflare_oauth_redirect_uri,
            }
            oauth_payload = await self.cloudflare_provider.exchange_oauth_code(**exchange_kwargs)
            scopes = (oauth_payload.scope or settings.cloudflare_oauth_scopes or "").split()
            bearer_value = oauth_payload.access_token
            validation = await self.cloudflare_provider.validate_oauth_access(
                bearer_value=bearer_value,
                scopes=scopes,
            )
            safe_reference = f"cloudflare_oauth_account:{validation.account_id}"
            provider_account_id = validation.account_id
            account_name = validation.account_name
            stored_scopes = validation.scopes or scopes
        else:
            safe_reference = TokenReferenceFactory.new_token_ref(provider=provider_name)
            validation = await self._validate_provider_account(provider_name, safe_reference)
            account_name = validation.get("account_name") or f"{provider_name}-account"
            provider_account_id = validation.get("account_id") or f"{provider_name}:{user_id}"
            stored_scopes = self._default_scopes(provider_name)

        record = await self.repository.upsert_connected(
            db,
            user_id=user_id,
            provider=provider_name,
            provider_account_id=provider_account_id,
            provider_account_name=account_name,
            token_secret_ref=safe_reference,
            token_key_version=TokenReferenceFactory.key_version(),
            scopes=stored_scopes,
        )
        await db.commit()
        return ProviderCallbackResult(
            provider=record.provider,
            connected=True,
            status=record.status,
            account_name=record.provider_account_name,
        )

    async def _handle_github_app_callback(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        state: str | None,
        installation_id: str | None,
    ) -> ProviderCallbackResult:
        provider_name: ProviderName = "github"

        if not installation_id:
            raise ProviderOAuthFailedError("GitHub App callback is missing installation_id.")
        if not installation_id.isdigit():
            raise ProviderOAuthFailedError("GitHub App callback installation_id is invalid.")
        if not state or not ConnectedAccountInstallState.validate_state(
            state=state,
            user_id=user_id,
            provider=provider_name,
        ):
            raise ProviderOAuthFailedError("GitHub App installation state is invalid.")

        settings = get_settings()
        app_jwt = self.github_provider.create_app_jwt(
            app_id=settings.github_app_id,
            private_key_pem=settings.github_app_private_key.get_secret_value(),
        )
        installation = await self.github_provider.get_app_installation(
            installation_id=installation_id,
            app_jwt=app_jwt,
        )

        # token_secret_ref stores a safe installation reference, not a GitHub token.
        # Installation access tokens are generated server-side only when needed.
        token_ref = f"github_app_installation:{installation.installation_id}"
        scopes = [
            "github_app:installation",
            f"repositories:{installation.repository_selection or 'unknown'}",
        ]

        record = await self.repository.upsert_connected(
            db,
            user_id=user_id,
            provider=provider_name,
            provider_account_id=str(installation.installation_id),
            provider_account_name=installation.account_login,
            token_secret_ref=token_ref,
            token_key_version=TokenReferenceFactory.key_version(),
            scopes=scopes,
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

        existing_record = self.repository.to_record(existing)
        if provider_name == "github":
            await self._delete_github_app_installation(existing_record.token_secret_ref)

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

    async def _delete_github_app_installation(self, token_secret_ref: str | None) -> None:
        if not token_secret_ref:
            return

        prefix = "github_app_installation:"
        if not token_secret_ref.startswith(prefix):
            return

        installation_id = token_secret_ref.removeprefix(prefix).strip()
        if not installation_id.isdigit():
            raise ProviderConnectionFailedError()

        settings = get_settings()
        app_jwt = self.github_provider.create_app_jwt(
            app_id=settings.github_app_id,
            private_key_pem=settings.github_app_private_key.get_secret_value(),
        )

        try:
            await self.github_provider.delete_app_installation(
                installation_id=installation_id,
                app_jwt=app_jwt,
            )
        except Exception as exc:
            raise ProviderConnectionFailedError() from exc

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
