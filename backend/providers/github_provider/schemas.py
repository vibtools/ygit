from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel


class GitHubRepository(BaseModel):
    provider: Literal["github"] = "github"
    repository_url: str
    owner: str
    name: str
    default_branch: str | None = None
    visibility: Literal["public", "private", "internal", "unknown"] = "unknown"
    latest_commit_sha: str | None = None
    file_tree_snapshot: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None


class ProviderResponse(BaseModel):
    provider: str
    ok: bool
