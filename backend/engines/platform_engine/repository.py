from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.ids import new_id
from backend.engines.platform_engine.models import FeatureFlagModel, PlatformSettingModel
from backend.engines.platform_engine.schemas import FeatureFlag, PlatformSetting


class PlatformRepository:
    """Database repository owned by Platform Engine.

    External consumers must use Platform Engine public service. Direct imports of this
    repository from API routes, worker runtime, providers, or other engines are forbidden.
    """

    async def list_settings(self, db: AsyncSession) -> list[PlatformSettingModel]:
        result = await db.execute(select(PlatformSettingModel).order_by(PlatformSettingModel.key.asc()))
        return list(result.scalars().all())

    async def list_feature_flags(self, db: AsyncSession, *, public_only: bool = True) -> list[FeatureFlagModel]:
        stmt = select(FeatureFlagModel).order_by(FeatureFlagModel.key.asc())
        if public_only:
            stmt = stmt.where(FeatureFlagModel.is_public.is_(True))
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def ensure_default_settings(
        self,
        db: AsyncSession,
        defaults: Iterable[PlatformSetting],
    ) -> list[PlatformSettingModel]:
        existing = {item.key: item for item in await self.list_settings(db)}
        for item in defaults:
            if item.key in existing:
                continue
            model = PlatformSettingModel(
                id=new_id("setting"),
                key=item.key,
                value={"value": item.value},
                description=item.description,
                is_sensitive=item.is_sensitive,
                is_editable=item.is_editable,
            )
            db.add(model)
            existing[item.key] = model
        await db.flush()
        return [existing[item.key] for item in defaults if item.key in existing]

    async def ensure_default_feature_flags(
        self,
        db: AsyncSession,
        defaults: Iterable[FeatureFlag],
    ) -> list[FeatureFlagModel]:
        existing = {item.key: item for item in await self.list_feature_flags(db, public_only=False)}
        for item in defaults:
            if item.key in existing:
                continue
            model = FeatureFlagModel(
                id=new_id("flag"),
                key=item.key,
                enabled=item.enabled,
                description=item.description,
                is_public=item.is_public,
            )
            db.add(model)
            existing[item.key] = model
        await db.flush()
        return [existing[item.key] for item in defaults if item.key in existing]

    def to_setting(self, model: PlatformSettingModel) -> PlatformSetting:
        raw = dict(model.value or {})
        return PlatformSetting(
            key=model.key,
            value=raw.get("value"),
            description=model.description,
            is_sensitive=model.is_sensitive,
            is_editable=model.is_editable,
        )

    def to_feature_flag(self, model: FeatureFlagModel) -> FeatureFlag:
        return FeatureFlag(
            key=model.key,
            enabled=model.enabled,
            description=model.description,
            is_public=model.is_public,
        )
