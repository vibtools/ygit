from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


HealthStatus = Literal["ok", "warning", "critical", "not_checked", "error", "configured"]
RuntimeStatus = Literal["ok", "maintenance", "degraded", "unknown"]
PlatformSettingKey = Literal[
    "maintenance_enabled",
    "maintenance_message",
    "registration_enabled",
    "allowed_repository_providers",
    "allowed_deployment_providers",
    "max_projects_per_user",
    "max_deployments_per_project_per_hour",
]
FeatureFlagKey = Literal[
    "templates_beta",
    "marketplace_preview",
    "plugins_preview",
    "ai_builder_preview",
    "analytics_preview",
    "teams_preview",
    "developer_portal_link",
]


class EngineContract(BaseModel):
    name: str
    version: str = "1.0"


class PlatformHealthComponent(BaseModel):
    name: str
    status: HealthStatus
    checked: bool = False
    message: str | None = None


class PlatformHealth(BaseModel):
    status: HealthStatus
    database: HealthStatus
    redis: HealthStatus
    worker: HealthStatus
    components: list[PlatformHealthComponent] = Field(default_factory=list)


class PlatformVersion(BaseModel):
    app: str
    version: str
    api_contract: str
    engine_contract: str
    database_architecture: str
    architecture_freeze: str
    platform_engine: str = "0.1.0"


class SystemStatus(BaseModel):
    maintenance: bool
    message: str | None
    queue_status: str
    worker_status: str
    runtime_status: RuntimeStatus = "unknown"
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class FeatureFlag(BaseModel):
    key: str
    enabled: bool
    description: str | None = None
    is_public: bool = True

    @field_validator("key")
    @classmethod
    def validate_key(cls, value: str) -> str:
        if not value or any(ch in value for ch in " /\\\r\n\t"):
            raise ValueError("Feature flag key is invalid.")
        return value


class FeatureFlagSet(BaseModel):
    flags: dict[str, bool]
    items: list[FeatureFlag]


class PlatformSetting(BaseModel):
    key: str
    value: Any
    description: str | None = None
    is_sensitive: bool = False
    is_editable: bool = False

    @field_validator("key")
    @classmethod
    def validate_key(cls, value: str) -> str:
        if not value or any(ch in value for ch in " /\\\r\n\t"):
            raise ValueError("Platform setting key is invalid.")
        return value


class PlatformSettingsSummary(BaseModel):
    maintenance_enabled: bool
    maintenance_message: str | None
    registration_enabled: bool
    allowed_repository_providers: list[str]
    allowed_deployment_providers: list[str]
    max_projects_per_user: int
    max_deployments_per_project_per_hour: int
    sensitive_config_location: str = "environment / secret store"
    mutable_in_mvp: bool = False
    items: list[PlatformSetting] = Field(default_factory=list)


class PlatformRuntimeSummary(BaseModel):
    health: PlatformHealth
    version: PlatformVersion
    system: SystemStatus
    feature_flags: FeatureFlagSet
    settings: PlatformSettingsSummary
