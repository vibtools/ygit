from __future__ import annotations

from pydantic import BaseModel, Field


class CloudflareOAuthResponse(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"
    expires_in: int | None = None
    scope: str | None = None


class CloudflareAccount(BaseModel):
    account_id: str
    account_name: str


class CloudflareAccountValidation(BaseModel):
    provider: str = "cloudflare"
    account_id: str
    account_name: str
    scopes: list[str] = Field(default_factory=list)
