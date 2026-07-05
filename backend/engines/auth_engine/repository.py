from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.ids import new_id
from backend.engines.auth_engine.models import UserIdentityModel, UserModel
from backend.engines.auth_engine.schemas import OIDCUserClaims, UserRecord


class AuthRepository:
    """Database repository owned by Auth Engine only."""

    async def get_user_by_id(self, db: AsyncSession, user_id: str) -> UserModel | None:
        result = await db.execute(select(UserModel).where(UserModel.id == user_id))
        return result.scalar_one_or_none()

    async def get_user_by_email(self, db: AsyncSession, email: str) -> UserModel | None:
        result = await db.execute(select(UserModel).where(UserModel.email == email.lower()))
        return result.scalar_one_or_none()

    async def get_identity(
        self,
        db: AsyncSession,
        *,
        provider: str,
        provider_realm: str,
        provider_subject: str,
    ) -> UserIdentityModel | None:
        result = await db.execute(
            select(UserIdentityModel).where(
                UserIdentityModel.provider == provider,
                UserIdentityModel.provider_realm == provider_realm,
                UserIdentityModel.provider_subject == provider_subject,
            )
        )
        return result.scalar_one_or_none()

    async def sync_identity_from_oidc(
        self,
        db: AsyncSession,
        *,
        claims: OIDCUserClaims,
        provider_realm: str,
    ) -> UserRecord:
        identity = await self.get_identity(
            db,
            provider="keycloak",
            provider_realm=provider_realm,
            provider_subject=claims.subject,
        )

        now = datetime.now(timezone.utc)
        if identity is not None:
            user = await self.get_user_by_id(db, identity.user_id)
            if user is None:
                # Broken identity mapping should not create a silent duplicate.
                raise RuntimeError("User identity points to a missing user")
            user.email = claims.email.lower()
            user.name = claims.name
            user.avatar_url = claims.avatar_url
            user.email_verified = claims.email_verified
            user.last_login_at = now
            await db.flush()
            return self.to_record(user)

        existing = await self.get_user_by_email(db, claims.email)
        if existing is None:
            existing = UserModel(
                id=new_id("user"),
                email=claims.email.lower(),
                name=claims.name,
                avatar_url=claims.avatar_url,
                status="active",
                email_verified=claims.email_verified,
                last_login_at=now,
            )
            db.add(existing)
            await db.flush()
        else:
            existing.name = claims.name
            existing.avatar_url = claims.avatar_url
            existing.email_verified = claims.email_verified
            existing.last_login_at = now
            await db.flush()

        db.add(
            UserIdentityModel(
                id=new_id("identity"),
                user_id=existing.id,
                provider="keycloak",
                provider_realm=provider_realm,
                provider_subject=claims.subject,
            )
        )
        await db.flush()
        return self.to_record(existing)

    def to_record(self, user: UserModel) -> UserRecord:
        return UserRecord(
            id=user.id,
            email=user.email,
            name=user.name,
            avatar_url=user.avatar_url,
            status=user.status,  # type: ignore[arg-type]
            email_verified=user.email_verified,
            last_login_at=user.last_login_at,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
