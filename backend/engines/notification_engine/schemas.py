from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


NotificationType = Literal[
    "deployment_success",
    "deployment_failure",
    "connected_account_warning",
    "platform_notice",
    "system_notice",
]
NotificationStatus = Literal["unread", "read", "failed"]
NotificationSeverity = Literal["info", "success", "warning", "error"]
NotificationChannel = Literal["in_app"]

_FORBIDDEN_METADATA_KEYS = {
    "token",
    "access_token",
    "refresh_token",
    "secret",
    "password",
    "authorization",
    "cookie",
    "client_secret",
    "token_secret_ref",
    "token_ciphertext",
}


class EngineContract(BaseModel):
    name: str
    version: str = "1.0"


class NotificationCreateInput(BaseModel):
    type: NotificationType
    title: str = Field(min_length=1, max_length=160)
    message: str = Field(min_length=1, max_length=1000)
    severity: NotificationSeverity = "info"
    related_resource_type: str | None = Field(default=None, max_length=80)
    related_resource_id: str | None = Field(default=None, max_length=128)
    metadata: dict[str, Any] = Field(default_factory=dict)
    channel: NotificationChannel = "in_app"

    @field_validator("metadata")
    @classmethod
    def validate_metadata_is_secret_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        def walk(item: Any, path: str = "metadata") -> None:
            if isinstance(item, dict):
                for key, nested in item.items():
                    normalized = str(key).lower()
                    if normalized in _FORBIDDEN_METADATA_KEYS or "token" in normalized or "secret" in normalized:
                        raise ValueError(f"Secret-like metadata field is not allowed: {path}.{key}")
                    walk(nested, f"{path}.{key}")
            elif isinstance(item, list):
                for idx, nested in enumerate(item):
                    walk(nested, f"{path}[{idx}]")

        walk(value)
        return value

    @field_validator("channel")
    @classmethod
    def validate_mvp_channel(cls, value: str) -> str:
        if value != "in_app":
            raise ValueError("Only in_app notifications are supported in MVP.")
        return value


class NotificationFilters(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    status: NotificationStatus | None = None
    type: NotificationType | None = None


class Notification(BaseModel):
    id: str
    user_id: str
    type: NotificationType
    title: str
    message: str
    severity: NotificationSeverity
    status: NotificationStatus
    channel: NotificationChannel = "in_app"
    delivery_status: str = "delivered"
    related_resource_type: str | None = None
    related_resource_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    read_at: datetime | None = None


class NotificationPage(BaseModel):
    items: list[Notification]
    page: int
    page_size: int
    total_items: int
    total_pages: int


class UnreadCount(BaseModel):
    unread_count: int


class NotificationEventInput(BaseModel):
    event_name: str
    recipient_user_id: str
    title: str
    message: str
    type: NotificationType
    severity: NotificationSeverity = "info"
    related_resource_type: str | None = None
    related_resource_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
