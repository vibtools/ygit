from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, EmailStr, Field


UserStatus = Literal["active", "disabled", "deleted"]
IdentityProvider = Literal["keycloak"]


class CurrentUser(BaseModel):
    id: str
    email: EmailStr
    name: str | None = None
    roles: tuple[str, ...] = ()
    status: UserStatus = "active"


class UserRecord(BaseModel):
    id: str
    email: EmailStr
    name: str | None = None
    avatar_url: str | None = None
    status: UserStatus = "active"
    email_verified: bool = False
    last_login_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class UserIdentityRecord(BaseModel):
    id: str
    user_id: str
    provider: IdentityProvider = "keycloak"
    provider_subject: str
    provider_realm: str = "vib"
    created_at: datetime | None = None
    updated_at: datetime | None = None


class OIDCUserClaims(BaseModel):
    subject: str
    email: EmailStr
    email_verified: bool = False
    name: str | None = None
    avatar_url: str | None = None
    roles: tuple[str, ...] = ()
    raw_claims: dict[str, Any] = Field(default_factory=dict)


class LoginFlow(BaseModel):
    state: str
    nonce: str
    code_verifier: str
    next_path: str
    created_at: int
    client_ip: str | None = None
    user_agent: str | None = None


class AuthenticatedSession(BaseModel):
    session_id: str
    user: CurrentUser
    id_token: str | None = None
    access_token: str | None = None
    refresh_token: str | None = None
    expires_at: int | None = None
    created_at: int
    last_seen_at: int


class LogoutResult(BaseModel):
    logged_out: bool


class TokenResponse(BaseModel):
    access_token: str | None = None
    refresh_token: str | None = None
    id_token: str | None = None
    expires_in: int | None = None
    token_type: str | None = None


class OIDCProviderMetadata(BaseModel):
    issuer: str
    authorization_endpoint: str
    token_endpoint: str
    jwks_uri: str
    userinfo_endpoint: str | None = None
    end_session_endpoint: str | None = None
