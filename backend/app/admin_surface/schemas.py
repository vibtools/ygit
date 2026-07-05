from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


AdminMetricStatus = Literal["ok", "warning", "critical", "unknown"]
AdminResourceStatus = Literal["ok", "configured", "not_checked", "empty", "restricted", "offline"]


class AdminMetric(BaseModel):
    key: str
    label: str
    value: int | str
    status: AdminMetricStatus = "unknown"
    description: str | None = None


class AdminHealthComponent(BaseModel):
    name: str
    status: AdminResourceStatus
    description: str


class AdminOverview(BaseModel):
    title: str = "Platform Operations Console"
    subtitle: str = "Monitor YGIT runtime health, queue status, deployments, users, audit logs, and system signals."
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metrics: list[AdminMetric]
    health: list[AdminHealthComponent]
    operations_focus: list[str]
    boundary: str


class AdminQueueStatus(BaseModel):
    status: AdminResourceStatus
    queues: list[AdminMetric]
    retry_policy: dict[str, str | int]
    notes: list[str]


class AdminDeploymentSummary(BaseModel):
    id: str | None = None
    project_id: str | None = None
    user_id: str | None = None
    status: str = "empty"
    source: str = "deployment_history_engine"
    message: str


class AdminUserSummary(BaseModel):
    id: str | None = None
    email: str | None = None
    status: str = "empty"
    source: str = "auth_engine"
    message: str


class AdminAuditLogEntry(BaseModel):
    id: str | None = None
    event_name: str
    actor_user_id: str | None = None
    target_type: str | None = None
    target_id: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    immutable: bool = True
    message: str


class AdminSystemMonitoring(BaseModel):
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    api: AdminResourceStatus
    database: AdminResourceStatus
    redis: AdminResourceStatus
    worker: AdminResourceStatus
    queue: AdminResourceStatus
    provider_checks: dict[str, AdminResourceStatus]
    notes: list[str]


class AdminSettingsSummary(BaseModel):
    maintenance_banner: bool
    registration_enabled: bool
    allowed_repository_providers: list[str]
    allowed_deployment_providers: list[str]
    templates_beta_enabled: bool
    sensitive_config_location: str
    mutable_in_mvp: bool


class AdminOperationsManifest(BaseModel):
    component: str = "admin_panel"
    version: str = "0.1.0"
    surface_type: str = "platform_operations_console"
    contract_version: str = "1.0"
    architecture_version: str = "1.1"
    uses_admin_engine: bool = False
    owns_tables: list[str] = Field(default_factory=list)
    protected_roles: list[str] = Field(default_factory=lambda: ["ygit_admin", "ygit_support", "ygit_readonly"])
    primary_sections: list[str]
