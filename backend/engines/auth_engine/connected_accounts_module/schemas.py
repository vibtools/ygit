from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, SecretStr

ProviderName = Literal["github", "cloudflare"]
ConnectedAccountStatus = Literal["connected", "disconnected", "error", "reconnect_required"]


class ConnectedAccountRecord(BaseModel):
    id: str
    user_id: str
    provider: ProviderName
    status: ConnectedAccountStatus
    provider_account_id: str | None = None
    provider_account_name: str | None = None
    token_secret_ref: str | None = None
    token_key_version: str | None = None
    scopes: list[str] = Field(default_factory=list)
    last_error_code: str | None = None
    last_checked_at: datetime | None = None
    connected_at: datetime | None = None
    disconnected_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted_at: datetime | None = None


class ResolvedProviderCredential(BaseModel):
    provider: Literal["cloudflare"]
    token_secret_ref: str
    access_token: SecretStr
    refresh_token: SecretStr | None = None
    token_type: str = "bearer"
    expires_at: datetime | None = None
    scopes: list[str] = Field(default_factory=list)


class ConnectedAccountSummary(BaseModel):
    provider: ProviderName
    connected: bool
    status: ConnectedAccountStatus
    account_name: str | None = None
    connected_at: datetime | None = None
    last_checked_at: datetime | None = None
    scopes: list[str] = Field(default_factory=list)
    last_error_code: str | None = None


class ConnectedAccountsList(BaseModel):
    accounts: list[ConnectedAccountSummary]


class ConnectProviderResult(BaseModel):
    provider: ProviderName
    status: Literal["oauth_redirect_ready"] = "oauth_redirect_ready"
    authorization_url: str
    state: str


class ProviderCallbackResult(BaseModel):
    provider: ProviderName
    connected: bool
    status: ConnectedAccountStatus
    account_name: str | None = None


class DisconnectProviderResult(BaseModel):
    provider: ProviderName
    connected: bool
    status: ConnectedAccountStatus


class ProviderConnectionHealth(BaseModel):
    provider: ProviderName
    status: ConnectedAccountStatus
    healthy: bool
    checked_at: datetime
    last_error_code: str | None = None
