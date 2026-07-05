from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

HistoryStatus = Literal["created", "running", "completed", "failed", "cancelled"]
LogLevel = Literal["debug", "info", "warning", "error"]

SECRET_KEY_FRAGMENTS = (
    "token",
    "secret",
    "password",
    "authorization",
    "client_secret",
    "refresh_token",
    "access_token",
)


def ensure_safe_metadata(value: dict[str, Any]) -> dict[str, Any]:
    for key in value.keys():
        lowered = str(key).lower()
        if any(fragment in lowered for fragment in SECRET_KEY_FRAGMENTS):
            raise ValueError(f"metadata key is not allowed in Deployment History Engine: {key}")
    return value


class DeploymentHistoryCreateInput(BaseModel):
    deployment_id: str
    project_id: str
    status: HistoryStatus = "created"
    provider: Literal["cloudflare"] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata")
    @classmethod
    def validate_metadata(cls, value: dict[str, Any]) -> dict[str, Any]:
        return ensure_safe_metadata(value)


class DeploymentLogInput(BaseModel):
    level: LogLevel = "info"
    message: str
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata")
    @classmethod
    def validate_metadata(cls, value: dict[str, Any]) -> dict[str, Any]:
        return ensure_safe_metadata(value)


class ProviderResultSummary(BaseModel):
    provider: Literal["github", "cloudflare"] | None = None
    provider_project_id: str | None = None
    provider_deployment_id: str | None = None
    deployment_url: str | None = None
    status: str | None = None
    action: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata")
    @classmethod
    def validate_metadata(cls, value: dict[str, Any]) -> dict[str, Any]:
        return ensure_safe_metadata(value)


class DeploymentHistoryRecord(BaseModel):
    id: str
    deployment_id: str
    project_id: str
    status: HistoryStatus
    provider: str | None = None
    provider_project_id: str | None = None
    provider_deployment_id: str | None = None
    deployment_url: str | None = None
    duration_ms: int | None = None
    failure_code: str | None = None
    failure_summary: str | None = None
    provider_summary: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class DeploymentLogRecord(BaseModel):
    id: str
    deployment_id: str
    project_id: str
    level: LogLevel
    message: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    sequence: int
    created_at: datetime


class DeploymentSummary(BaseModel):
    deployment_id: str
    project_id: str
    status: HistoryStatus
    deployment_url: str | None = None
    duration_ms: int | None = None
    failure_code: str | None = None
    failure_summary: str | None = None
    created_at: datetime
    updated_at: datetime


class DeploymentHistoryDetail(BaseModel):
    history: DeploymentHistoryRecord
    logs: list[DeploymentLogRecord] = Field(default_factory=list)


class DeploymentLogList(BaseModel):
    deployment_id: str
    logs: list[DeploymentLogRecord] = Field(default_factory=list)


class DeploymentHistoryPage(BaseModel):
    items: list[DeploymentSummary]
    pagination: dict[str, int]


class HistoryWriteResult(BaseModel):
    deployment_id: str
    status: HistoryStatus
    logs_written: int = 0
    provider_summary_written: bool = False
