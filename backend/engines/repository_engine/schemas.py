from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

RepositoryProvider = Literal["github"]
RepositoryVisibility = Literal["public", "private", "internal", "unknown"]


class RepositoryValidateInput(BaseModel):
    repository_url: str = Field(min_length=1, max_length=2048)

    @field_validator("repository_url")
    @classmethod
    def clean_repository_url(cls, value: str) -> str:
        return value.strip()


class RepositoryMetadataInput(RepositoryValidateInput):
    pass


class ParsedRepositoryUrl(BaseModel):
    provider: RepositoryProvider = "github"
    owner: str
    repo: str
    normalized_url: str


class RepositoryValidationResult(BaseModel):
    valid: bool
    provider: RepositoryProvider
    owner: str
    repo: str
    normalized_url: str


class RepositoryProviderMetadata(BaseModel):
    provider: RepositoryProvider = "github"
    repository_url: str
    owner: str
    name: str
    default_branch: str | None = None
    visibility: RepositoryVisibility = "unknown"
    latest_commit_sha: str | None = None
    file_tree_snapshot: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None


class RepositoryRecord(BaseModel):
    id: str
    user_id: str
    provider: RepositoryProvider = "github"
    repository_url: str
    owner: str
    name: str
    default_branch: str | None = None
    visibility: RepositoryVisibility = "unknown"
    latest_commit_sha: str | None = None
    file_tree_snapshot: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None
    fetched_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


class RepositorySummary(BaseModel):
    id: str
    provider: RepositoryProvider
    repository_url: str
    owner: str
    name: str
    default_branch: str | None = None
    visibility: RepositoryVisibility
    latest_commit_sha: str | None = None
    fetched_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class RepositoryDetail(RepositorySummary):
    user_id: str
    file_tree_snapshot: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None
    deleted_at: datetime | None = None


class RepositoryAnalysisInput(BaseModel):
    repository_id: str
    provider: RepositoryProvider = "github"
    repository_url: str
    owner: str
    repo: str
    default_branch: str | None = None
    visibility: RepositoryVisibility
    latest_commit_sha: str | None = None
    file_tree_snapshot: dict[str, Any] | None = None
