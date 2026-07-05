from __future__ import annotations

import asyncio
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import get_settings
from backend.engines.platform_engine.repository import PlatformRepository
from backend.engines.platform_engine.schemas import (
    FeatureFlag,
    FeatureFlagSet,
    PlatformHealth,
    PlatformHealthComponent,
    PlatformRuntimeSummary,
    PlatformSetting,
    PlatformSettingsSummary,
    PlatformVersion,
    SystemStatus,
)


DEFAULT_FEATURE_FLAGS: tuple[FeatureFlag, ...] = (
    FeatureFlag(key="templates_beta", enabled=True, description="Official templates beta preview."),
    FeatureFlag(key="marketplace_preview", enabled=False, description="Marketplace preview is future scope."),
    FeatureFlag(key="plugins_preview", enabled=False, description="Plugins preview is future scope."),
    FeatureFlag(key="ai_builder_preview", enabled=False, description="AI Builder preview is future scope."),
    FeatureFlag(key="analytics_preview", enabled=False, description="Analytics preview is future scope."),
    FeatureFlag(key="teams_preview", enabled=False, description="Teams preview is future scope."),
    FeatureFlag(key="developer_portal_link", enabled=True, description="Show ygit.dev developer portal link."),
)

DEFAULT_SETTINGS: tuple[PlatformSetting, ...] = (
    PlatformSetting(key="maintenance_enabled", value=False, description="Global maintenance flag.", is_editable=False),
    PlatformSetting(key="maintenance_message", value=None, description="Optional public maintenance message.", is_editable=False),
    PlatformSetting(key="registration_enabled", value=True, description="Allow new authenticated users to enter YGIT.", is_editable=False),
    PlatformSetting(key="allowed_repository_providers", value=["github"], description="Repository providers enabled for MVP.", is_editable=False),
    PlatformSetting(key="allowed_deployment_providers", value=["cloudflare"], description="Deployment providers enabled for MVP.", is_editable=False),
    PlatformSetting(key="max_projects_per_user", value=20, description="Default project quota placeholder.", is_editable=False),
    PlatformSetting(key="max_deployments_per_project_per_hour", value=30, description="Default deployment rate placeholder.", is_editable=False),
)


class PlatformInternalService:
    """Internal implementation for Platform Engine.

    Runtime health checks are deliberately adapter-based. The engine may read health
    state for database, Redis, and worker/queue signals, but it must not mutate other
    engine-owned state or call external providers.
    """

    def __init__(self, repository: PlatformRepository | None = None) -> None:
        self.repository = repository or PlatformRepository()

    async def get_health(self, *, check_runtime: bool = False) -> PlatformHealth:
        database = "not_checked"
        redis = "not_checked"
        worker = "configured"
        if check_runtime:
            database = await self._safe_check(database_health)
            redis = await self._safe_check(redis_health)
        components = [
            PlatformHealthComponent(name="api", status="ok", checked=True, message="FastAPI application is running."),
            PlatformHealthComponent(name="database", status=database, checked=check_runtime, message="PostgreSQL health adapter."),
            PlatformHealthComponent(name="redis", status=redis, checked=check_runtime, message="Redis health adapter."),
            PlatformHealthComponent(name="worker", status=worker, checked=False, message="Worker runtime configured; heartbeat check is future runtime adapter."),
        ]
        aggregate = "ok" if all(item.status in {"ok", "configured", "not_checked"} for item in components) else "warning"
        return PlatformHealth(status=aggregate, database=database, redis=redis, worker=worker, components=components)  # type: ignore[arg-type]

    async def get_version(self) -> PlatformVersion:
        settings = get_settings()
        return PlatformVersion(
            app="ygit",
            version=settings.app_version,
            api_contract="1.0",
            engine_contract="1.0",
            database_architecture="1.0",
            architecture_freeze="1.1",
            platform_engine="0.1.0",
        )

    async def get_system_status(self, db: AsyncSession | None = None) -> SystemStatus:
        settings = await self.get_settings_summary(db)
        queue_status = "configured"
        worker_status = "configured"
        runtime_status = "maintenance" if settings.maintenance_enabled else "ok"
        return SystemStatus(
            maintenance=settings.maintenance_enabled,
            message=settings.maintenance_message,
            queue_status=queue_status,
            worker_status=worker_status,
            runtime_status=runtime_status,
        )

    async def get_feature_flags(self, db: AsyncSession | None = None) -> FeatureFlagSet:
        items = list(DEFAULT_FEATURE_FLAGS)
        if db is not None:
            rows = await self.repository.ensure_default_feature_flags(db, DEFAULT_FEATURE_FLAGS)
            items = [self.repository.to_feature_flag(row) for row in rows if row.is_public]
        return FeatureFlagSet(flags={item.key: item.enabled for item in items}, items=items)

    async def get_settings_summary(self, db: AsyncSession | None = None) -> PlatformSettingsSummary:
        items = list(DEFAULT_SETTINGS)
        if db is not None:
            rows = await self.repository.ensure_default_settings(db, DEFAULT_SETTINGS)
            items = [self.repository.to_setting(row) for row in rows if not row.is_sensitive]
        values: dict[str, Any] = {item.key: item.value for item in items}
        return PlatformSettingsSummary(
            maintenance_enabled=bool(values.get("maintenance_enabled", False)),
            maintenance_message=values.get("maintenance_message"),
            registration_enabled=bool(values.get("registration_enabled", True)),
            allowed_repository_providers=list(values.get("allowed_repository_providers") or ["github"]),
            allowed_deployment_providers=list(values.get("allowed_deployment_providers") or ["cloudflare"]),
            max_projects_per_user=int(values.get("max_projects_per_user") or 20),
            max_deployments_per_project_per_hour=int(values.get("max_deployments_per_project_per_hour") or 30),
            items=items,
        )

    async def get_runtime_summary(self, db: AsyncSession | None = None) -> PlatformRuntimeSummary:
        return PlatformRuntimeSummary(
            health=await self.get_health(),
            version=await self.get_version(),
            system=await self.get_system_status(db),
            feature_flags=await self.get_feature_flags(db),
            settings=await self.get_settings_summary(db),
        )

    async def _safe_check(self, check_fn: Any) -> str:
        try:
            return await asyncio.wait_for(check_fn(), timeout=2.0)
        except Exception:
            return "error"
