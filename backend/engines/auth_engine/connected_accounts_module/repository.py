from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.ids import new_id
from backend.engines.auth_engine.connected_accounts_module.models import ConnectedAccountModel
from backend.engines.auth_engine.connected_accounts_module.schemas import ConnectedAccountRecord, ProviderName


class ConnectedAccountRepository:
    """Database repository owned by Auth Engine / Connected Accounts Module only."""

    async def get_by_user_provider(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        provider: ProviderName,
    ) -> ConnectedAccountModel | None:
        result = await db.execute(
            select(ConnectedAccountModel).where(
                ConnectedAccountModel.user_id == user_id,
                ConnectedAccountModel.provider == provider,
                ConnectedAccountModel.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def list_by_user(self, db: AsyncSession, *, user_id: str) -> list[ConnectedAccountModel]:
        result = await db.execute(
            select(ConnectedAccountModel)
            .where(
                ConnectedAccountModel.user_id == user_id,
                ConnectedAccountModel.deleted_at.is_(None),
            )
            .order_by(ConnectedAccountModel.provider.asc())
        )
        return list(result.scalars().all())

    async def upsert_connected(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        provider: ProviderName,
        provider_account_id: str | None,
        provider_account_name: str | None,
        token_secret_ref: str,
        token_key_version: str,
        scopes: list[str],
        token_ciphertext: str | None = None,
    ) -> ConnectedAccountRecord:
        now = datetime.now(timezone.utc)
        model = await self.get_by_user_provider(
            db,
            user_id=user_id,
            provider=provider,
        )

        if model is None:
            model = ConnectedAccountModel(
                id=new_id("acct"),
                user_id=user_id,
                provider=provider,
            )
            db.add(model)

        model.status = "connected"
        model.provider_account_id = provider_account_id
        model.provider_account_name = provider_account_name
        model.token_secret_ref = token_secret_ref
        model.token_key_version = token_key_version
        model.scopes = scopes
        model.last_error_code = None
        model.last_checked_at = now
        model.connected_at = now
        model.disconnected_at = None

        setattr(
            model,
            "token_ciphertext",
            token_ciphertext,
        )

        await db.flush()
        return self.to_record(model)

    async def get_credential_storage(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        provider: ProviderName,
    ) -> tuple[
        ConnectedAccountRecord,
        str | None,
    ] | None:
        model = await self.get_by_user_provider(
            db,
            user_id=user_id,
            provider=provider,
        )

        if model is None:
            return None

        return (
            self.to_record(model),
            model.token_ciphertext,
        )

    async def mark_disconnected(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        provider: ProviderName,
    ) -> ConnectedAccountRecord:
        model = await self.get_by_user_provider(db, user_id=user_id, provider=provider)
        if model is None:
            model = ConnectedAccountModel(
                id=new_id("acct"),
                user_id=user_id,
                provider=provider,
            )
            db.add(model)
        now = datetime.now(timezone.utc)
        model.status = "disconnected"
        model.token_secret_ref = None
        model.token_ciphertext = None
        model.token_key_version = None
        model.last_error_code = None
        model.disconnected_at = now
        await db.flush()
        return self.to_record(model)

    async def mark_provider_error(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        provider: ProviderName,
        error_code: str,
    ) -> ConnectedAccountRecord:
        model = await self.get_by_user_provider(db, user_id=user_id, provider=provider)
        if model is None:
            model = ConnectedAccountModel(id=new_id("acct"), user_id=user_id, provider=provider)
            db.add(model)
        model.status = "error"
        model.last_error_code = error_code
        model.last_checked_at = datetime.now(timezone.utc)
        await db.flush()
        return self.to_record(model)

    def to_record(self, model: ConnectedAccountModel) -> ConnectedAccountRecord:
        return ConnectedAccountRecord(
            id=model.id,
            user_id=model.user_id,
            provider=model.provider,  # type: ignore[arg-type]
            status=model.status,  # type: ignore[arg-type]
            provider_account_id=model.provider_account_id,
            provider_account_name=model.provider_account_name,
            token_secret_ref=model.token_secret_ref,
            token_key_version=model.token_key_version,
            scopes=list(model.scopes or []),
            last_error_code=model.last_error_code,
            last_checked_at=model.last_checked_at,
            connected_at=model.connected_at,
            disconnected_at=model.disconnected_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
            deleted_at=model.deleted_at,
        )
