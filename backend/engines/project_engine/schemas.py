from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

ProjectStatus = Literal[
    "draft",
    "repository_attached",
    "analysis_ready",
    "deploy_ready",
    "deployed",
    "failed",
    "deleted",
]


class ProjectCreateInput(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    repository_url: str | None = Field(default=None, max_length=2048)
    slug: str = Field(min_length=3, max_length=64)

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        return " ".join(value.strip().split())

    @field_validator("slug")
    @classmethod
    def clean_slug(cls, value: str) -> str:
        return value.strip().lower()


class ProjectUpdateInput(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return " ".join(value.strip().split())


class ProjectListFilters(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    status: ProjectStatus | None = None
    search: str | None = Field(default=None, max_length=120)


class ProjectRecord(BaseModel):
    id: str
    user_id: str
    name: str
    slug: str
    status: ProjectStatus
    repository_id: str | None = None
    analysis_id: str | None = None
    current_deployment_id: str | None = None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None
    version: int = 1


class ProjectSummary(BaseModel):
    id: str
    name: str
    slug: str
    status: ProjectStatus
    repository_id: str | None = None
    analysis_id: str | None = None
    current_deployment_id: str | None = None
    created_at: datetime
    updated_at: datetime


class ProjectDetail(ProjectSummary):
    user_id: str
    deleted_at: datetime | None = None
    version: int = 1


class ProjectAccess(BaseModel):
    project_id: str
    user_id: str
    allowed: bool = True


class ProjectDeleteResult(BaseModel):
    deleted: bool
    project_id: str
