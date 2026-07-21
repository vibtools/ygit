from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import (
    BaseModel,
    Field,
    field_validator,
    model_validator,
)

from backend.pipelines.deploy_pipeline.contract import (
    CLOUDFLARE_PROVIDER_OPERATION_ORDER,
    CloudflareProviderOperation,
    DeployPipelineEventName,
    DeployPipelineStage,
)

SECRET_KEY_FRAGMENTS = (
    "token",
    "secret",
    "password",
    "authorization",
    "client_secret",
    "refresh_token",
    "access_token",
)


def _ensure_safe_metadata(value: dict[str, Any]) -> dict[str, Any]:
    for key in value.keys():
        lowered = str(key).lower()
        if any(fragment in lowered for fragment in SECRET_KEY_FRAGMENTS):
            raise ValueError(f"metadata key is not allowed in deploy pipeline contract: {key}")
    return value


class ProviderTokenReference(BaseModel):
    provider: Literal["github", "cloudflare"]
    token_secret_ref: str
    account_name: str | None = None


class DeploymentPipelineContext(BaseModel):
    deployment_id: str
    project_id: str | None = None
    user_id: str | None = None
    repository_id: str | None = None
    analysis_id: str | None = None
    domain_id: str | None = None
    source_deployment_id: str | None = None
    repository_url: str | None = None
    branch: str | None = None
    commit_sha: str | None = None
    repository_path: str | None = None
    workspace_path: str | None = None
    artifacts_path: str | None = None
    artifact_path: str | None = None
    framework: str | None = None
    package_manager: str | None = None
    build_command: str | None = None
    output_directory: str | None = None
    deployment_url: str | None = None
    github_token_ref: ProviderTokenReference | None = None
    cloudflare_token_ref: ProviderTokenReference | None = None
    trace_id: str | None = None
    execution_mode: Literal["contract_skeleton", "provider_enabled"] = "contract_skeleton"



CloudflareProviderPlanBlocker = Literal[
    "user_context_missing",
    "project_context_missing",
    "artifact_context_missing",
    "branch_context_missing",
    "cloudflare_reference_missing",
    "provider_execution_disabled",
]


class CloudflareProviderExecutionPlan(BaseModel):
    deployment_id: str
    execution_mode: Literal[
        "contract_skeleton",
        "provider_enabled",
    ]
    operations: list[
        CloudflareProviderOperation
    ]
    ready_to_execute: bool
    blockers: list[
        CloudflareProviderPlanBlocker
    ] = Field(default_factory=list)

    @field_validator("deployment_id")
    @classmethod
    def validate_deployment_id(
        cls,
        value: str,
    ) -> str:
        normalized = str(value or "").strip()

        if (
            not normalized
            or any(
                character in normalized
                for character in (
                    "\x00",
                    "\r",
                    "\n",
                )
            )
        ):
            raise ValueError(
                "deployment ID is invalid"
            )

        return normalized

    @model_validator(mode="after")
    def validate_plan_consistency(
        self,
    ) -> "CloudflareProviderExecutionPlan":
        expected_operations = list(
            CLOUDFLARE_PROVIDER_OPERATION_ORDER
        )

        if self.operations != expected_operations:
            raise ValueError(
                "Cloudflare provider operation order is invalid"
            )

        if self.ready_to_execute == bool(
            self.blockers
        ):
            raise ValueError(
                "Cloudflare provider plan readiness is inconsistent"
            )

        if len(self.blockers) != len(
            set(self.blockers)
        ):
            raise ValueError(
                "Cloudflare provider plan blockers are duplicated"
            )

        return self


class PipelineLogEntry(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    level: Literal["debug", "info", "warning", "error"] = "info"
    message: str
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata")
    @classmethod
    def validate_metadata(cls, value: dict[str, Any]) -> dict[str, Any]:
        return _ensure_safe_metadata(value)


class PipelineProviderSummary(BaseModel):
    provider: Literal["github", "cloudflare"]
    action: str
    status: Literal["pending", "skipped", "succeeded", "failed"]
    provider_project_id: str | None = None
    provider_deployment_id: str | None = None
    deployment_url: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata")
    @classmethod
    def validate_metadata(cls, value: dict[str, Any]) -> dict[str, Any]:
        return _ensure_safe_metadata(value)


class PipelineEvent(BaseModel):
    event_name: DeployPipelineEventName
    stage: DeployPipelineStage
    deployment_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    trace_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata")
    @classmethod
    def validate_metadata(cls, value: dict[str, Any]) -> dict[str, Any]:
        return _ensure_safe_metadata(value)


class HistoryWriteIntent(BaseModel):
    """Contract object consumed by Deployment History Engine in the next phase."""

    deployment_id: str
    stage: DeployPipelineStage
    history_status: Literal["created", "running", "completed", "failed", "cancelled"]
    event_name: DeployPipelineEventName
    log_entries: list[PipelineLogEntry] = Field(default_factory=list)
    provider_summary: PipelineProviderSummary | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata")
    @classmethod
    def validate_metadata(cls, value: dict[str, Any]) -> dict[str, Any]:
        return _ensure_safe_metadata(value)


class DeploymentPipelineResult(BaseModel):
    deployment_id: str
    status: Literal["prepared", "completed", "failed"]
    stage: DeployPipelineStage
    deployment_url: str | None = None
    events: list[PipelineEvent] = Field(default_factory=list)
    logs: list[PipelineLogEntry] = Field(default_factory=list)
    provider_summaries: list[PipelineProviderSummary] = Field(default_factory=list)
    history_writes: list[HistoryWriteIntent] = Field(default_factory=list)
    failure_code: str | None = None
    failure_summary: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata")
    @classmethod
    def validate_metadata(cls, value: dict[str, Any]) -> dict[str, Any]:
        return _ensure_safe_metadata(value)
