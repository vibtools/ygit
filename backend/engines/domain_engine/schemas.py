from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

DomainStatus = Literal["reserved", "attached", "released"]


class DomainCheckInput(BaseModel):
    slug: str = Field(min_length=3, max_length=64)
    base_domain: str = Field(default="ygit.net", min_length=3, max_length=255)

    @field_validator("slug")
    @classmethod
    def clean_slug(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("base_domain")
    @classmethod
    def clean_base_domain(cls, value: str) -> str:
        return value.strip().lower().removeprefix("https://").removeprefix("http://").strip("/")


class DomainReserveInput(BaseModel):
    slug: str = Field(min_length=3, max_length=64)
    base_domain: str = Field(default="ygit.net", min_length=3, max_length=255)

    @field_validator("slug")
    @classmethod
    def clean_slug(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("base_domain")
    @classmethod
    def clean_base_domain(cls, value: str) -> str:
        return value.strip().lower().removeprefix("https://").removeprefix("http://").strip("/")


class DomainAvailability(BaseModel):
    slug: str
    base_domain: str
    available: bool
    preview_url: str
    reason: str | None = None


class DomainRecord(BaseModel):
    id: str
    project_id: str
    user_id: str
    slug: str
    base_domain: str
    full_url: str
    status: DomainStatus
    created_at: datetime
    updated_at: datetime
    released_at: datetime | None = None


class DomainDetail(DomainRecord):
    pass


class DomainReleaseResult(BaseModel):
    released: bool
    domain_id: str
    project_id: str
    slug: str
    full_url: str


class DomainPreview(BaseModel):
    slug: str
    base_domain: str
    full_url: str
