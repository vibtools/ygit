from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from backend.engines.platform_engine.internal.service import PlatformInternalService
from backend.engines.platform_engine.schemas import (
    FeatureFlagSet,
    PlatformHealth,
    PlatformRuntimeSummary,
    PlatformSettingsSummary,
    PlatformVersion,
    SystemStatus,
)


class PlatformPublicService:
    """Public Platform Engine API.

    Approved consumers: API routes, Admin Surface, approved engines, and worker/job
    runtime status adapters. Consumers must not import Platform Engine internals,
    repository, or models directly.
    """

    def __init__(self, internal: PlatformInternalService | None = None) -> None:
        self.internal = internal or PlatformInternalService()

    async def get_health(self, *, check_runtime: bool = False) -> PlatformHealth:
        return await self.internal.get_health(check_runtime=check_runtime)

    async def get_version(self) -> PlatformVersion:
        return await self.internal.get_version()

    async def get_system_status(self, db: AsyncSession | None = None) -> SystemStatus:
        return await self.internal.get_system_status(db)

    async def get_feature_flags(self, db: AsyncSession | None = None) -> FeatureFlagSet:
        return await self.internal.get_feature_flags(db)

    async def get_settings_summary(self, db: AsyncSession | None = None) -> PlatformSettingsSummary:
        return await self.internal.get_settings_summary(db)

    async def get_runtime_summary(self, db: AsyncSession | None = None) -> PlatformRuntimeSummary:
        return await self.internal.get_runtime_summary(db)


platform_service = PlatformPublicService()
