from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

DeploymentStatus = Literal["draft", "queued", "running", "completed", "failed", "cancelled"]
DeploymentRequestedBy = Literal["user", "admin", "system"]
DeployJobType = Literal["deploy_project", "redeploy_project"]


class DeploymentRequestInput(BaseModel):
    force: bool = False
    idempotency_key: str | None = Field(default=None, max_length=128)


class RedeployRequestInput(BaseModel):
    force: bool = False
    idempotency_key: str | None = Field(default=None, max_length=128)


class DeploymentRecord(BaseModel):
    id: str
    project_id: str
    user_id: str
    repository_id: str
    analysis_id: str
    domain_id: str | None = None
    job_id: str | None = None
    status: DeploymentStatus
    requested_by: DeploymentRequestedBy = "user"
    source_deployment_id: str | None = None
    queued_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    cancelled_at: datetime | None = None
    failure_code: str | None = None
    failure_summary: str | None = None
    created_at: datetime
    updated_at: datetime
    version: int = 1


class DeploymentSummary(BaseModel):
    id: str
    project_id: str
    status: DeploymentStatus
    job_id: str | None = None
    queued_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    cancelled_at: datetime | None = None
    failure_code: str | None = None
    failure_summary: str | None = None
    created_at: datetime
    updated_at: datetime


class DeploymentDetail(DeploymentSummary):
    user_id: str
    repository_id: str
    analysis_id: str
    domain_id: str | None = None
    requested_by: DeploymentRequestedBy = "user"
    source_deployment_id: str | None = None
    version: int = 1


class DeployReadyResult(BaseModel):
    project_id: str
    repository_id: str
    analysis_id: str
    github_connected: bool
    cloudflare_connected: bool
    deploy_ready: bool
    blocking_reasons: list[str] = Field(default_factory=list)


class DeploymentJobRef(BaseModel):
    id: str
    type: DeployJobType
    status: Literal["queued"] = "queued"


class DeploymentQueued(BaseModel):
    deployment: DeploymentDetail
    job: DeploymentJobRef


class DeploymentCancelled(BaseModel):
    deployment_id: str
    status: Literal["cancelled"] = "cancelled"
    cancelled: bool = True
