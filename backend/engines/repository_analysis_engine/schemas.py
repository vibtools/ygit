from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

AnalysisStage = Literal["quick", "deep"]
AnalysisStatus = Literal[
    "not_started",
    "quick_running",
    "quick_completed",
    "deep_queued",
    "deep_running",
    "deep_completed",
    "failed",
]
FrameworkName = Literal[
    "html",
    "react",
    "vue",
    "vite",
    "astro",
    "hugo",
    "docusaurus",
    "jekyll",
    "unknown",
]
PackageManager = Literal["npm", "pnpm", "yarn", "bun", "none", "unknown"]
RenderMode = Literal["static", "dynamic", "hybrid", "unknown"]
Severity = Literal["info", "warning", "error"]


class AnalysisInput(BaseModel):
    repository_id: str = Field(min_length=1)


class AnalysisRecalculateInput(BaseModel):
    force_deep: bool = False


class DetectionEvidence(BaseModel):
    source: str
    reason: str


class FrameworkDetection(BaseModel):
    framework: FrameworkName = "unknown"
    confidence: int = Field(default=0, ge=0, le=100)
    evidence: list[DetectionEvidence] = Field(default_factory=list)


class PackageManagerDetection(BaseModel):
    package_manager: PackageManager = "unknown"
    confidence: int = Field(default=0, ge=0, le=100)
    evidence: list[DetectionEvidence] = Field(default_factory=list)


class BuildCommandDetection(BaseModel):
    build_command: str | None = None
    confidence: int = Field(default=0, ge=0, le=100)
    evidence: list[DetectionEvidence] = Field(default_factory=list)


class OutputDirectoryDetection(BaseModel):
    output_directory: str | None = None
    confidence: int = Field(default=0, ge=0, le=100)
    evidence: list[DetectionEvidence] = Field(default_factory=list)


class StaticDynamicDetection(BaseModel):
    render_mode: RenderMode = "unknown"
    confidence: int = Field(default=0, ge=0, le=100)
    evidence: list[DetectionEvidence] = Field(default_factory=list)


class AnalysisWarning(BaseModel):
    code: str
    message: str
    severity: Severity = "warning"


class AnalysisRecommendation(BaseModel):
    code: str
    message: str
    priority: Literal["low", "medium", "high"] = "medium"


class DeployReadiness(BaseModel):
    deploy_ready: bool
    blocking_reasons: list[str] = Field(default_factory=list)
    warnings: list[AnalysisWarning] = Field(default_factory=list)


class RepositoryScore(BaseModel):
    score: int = Field(ge=0, le=100)
    grade: Literal["A", "B", "C", "D", "F"]
    factors: dict[str, int] = Field(default_factory=dict)


class QuickAnalysisResult(BaseModel):
    stage: Literal["quick"] = "quick"
    framework: FrameworkDetection
    package_manager: PackageManagerDetection
    build_command: BuildCommandDetection
    output_directory: OutputDirectoryDetection
    static_dynamic: StaticDynamicDetection
    deploy_readiness: DeployReadiness
    repository_score: RepositoryScore
    warnings: list[AnalysisWarning] = Field(default_factory=list)
    recommendations: list[AnalysisRecommendation] = Field(default_factory=list)


class DeepAnalysisResult(BaseModel):
    stage: Literal["deep"] = "deep"
    status: Literal["queued", "completed"]
    message: str


class AnalysisRecord(BaseModel):
    id: str
    repository_id: str
    user_id: str
    project_id: str | None = None
    stage: AnalysisStage
    status: AnalysisStatus
    framework: FrameworkName | None = None
    package_manager: PackageManager | None = None
    build_command: str | None = None
    output_directory: str | None = None
    deploy_ready: bool
    score: int | None = None
    explanation: dict[str, Any] | None = None
    warnings: list[dict[str, Any]] | None = None
    errors: list[dict[str, Any]] | None = None
    commit_sha: str | None = None
    is_latest: bool = True
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


class AnalysisDetail(AnalysisRecord):
    quick_analysis: QuickAnalysisResult | None = None
    recommendations: list[AnalysisRecommendation] = Field(default_factory=list)


class AnalysisJobRef(BaseModel):
    id: str
    type: Literal["repository_analysis.deep"] = "repository_analysis.deep"
    status: Literal["queued"] = "queued"


class AnalysisQueuedResult(BaseModel):
    job: AnalysisJobRef
