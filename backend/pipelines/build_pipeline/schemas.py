from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


BuildStatus = Literal["succeeded", "failed", "timed_out", "invalid"]
PackageManagerName = Literal["npm", "pnpm", "yarn", "bun", "none", "unknown"]


class BuildPlan(BaseModel):
    package_manager: PackageManagerName = "unknown"
    install_command: str | None = None
    build_command: str = Field(min_length=1, max_length=256)
    output_directory: str = Field(min_length=1, max_length=256)
    root_directory: str = Field(default=".", min_length=1, max_length=256)
    timeout_seconds: int = Field(default=600, ge=5, le=1800)


class BuildExecutionInput(BaseModel):
    repository_path: str = Field(min_length=1)
    plan: BuildPlan
    environment: dict[str, str] = Field(default_factory=dict)


class BuildLogLine(BaseModel):
    stream: Literal["system", "stdout", "stderr"]
    message: str


class BuildExecutionResult(BaseModel):
    status: BuildStatus
    exit_code: int | None = None
    duration_ms: int
    output_directory: str
    artifact_ready: bool
    logs: list[BuildLogLine] = Field(default_factory=list)
    error_message: str | None = None
