from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from backend.pipelines.deploy_pipeline.internal.build_adapter import DeployPipelineBuildAdapter


DeployBuildStageStatus = Literal["succeeded", "failed"]


class DeployBuildStageInput(BaseModel):
    """Worker-owned build-stage input.

    The worker must provide repository_path after checkout. This module does not
    clone repositories, write deployment history, or call providers.
    """

    deployment_id: str = Field(min_length=1)
    repository_path: str = Field(min_length=1)
    package_manager: str | None = None
    build_command: str = Field(min_length=1, max_length=256)
    output_directory: str = Field(min_length=1, max_length=256)
    root_directory: str = Field(default=".", min_length=1, max_length=256)
    install_command: str | None = None
    timeout_seconds: int = Field(default=600, ge=5, le=1800)
    environment: dict[str, str] = Field(default_factory=dict)


class DeployBuildStageLog(BaseModel):
    stream: str
    message: str


class DeployBuildStageResult(BaseModel):
    deployment_id: str
    status: DeployBuildStageStatus
    build_status: str
    artifact_ready: bool
    output_directory: str
    duration_ms: int
    error_message: str | None = None
    logs: list[DeployBuildStageLog] = Field(default_factory=list)
    metadata: dict[str, object] = Field(default_factory=dict)


class DeployPipelineBuildStage:
    """Isolated Deploy Pipeline build stage.

    This is intentionally not wired into DeployPipelineService yet. It gives the
    worker/deploy integration a tested, provider-free build-stage contract before
    touching the existing service import chain.
    """

    def __init__(self, adapter: DeployPipelineBuildAdapter | None = None) -> None:
        self.adapter = adapter or DeployPipelineBuildAdapter()

    def run(self, input_data: DeployBuildStageInput) -> DeployBuildStageResult:
        build_result = self.adapter.run_repository_build(
            repository_path=input_data.repository_path,
            package_manager=input_data.package_manager,
            build_command=input_data.build_command,
            output_directory=input_data.output_directory,
            root_directory=input_data.root_directory,
            install_command=input_data.install_command,
            timeout_seconds=input_data.timeout_seconds,
            environment=input_data.environment,
        )

        stage_status: DeployBuildStageStatus = (
            "succeeded"
            if build_result.status == "succeeded" and build_result.artifact_ready
            else "failed"
        )

        logs = [
            DeployBuildStageLog(stream="system", message="Deploy Pipeline build stage started."),
            *[
                DeployBuildStageLog(stream=line.stream, message=line.message)
                for line in build_result.logs[:80]
            ],
            DeployBuildStageLog(
                stream="system",
                message=(
                    "Deploy Pipeline build artifact verified."
                    if stage_status == "succeeded"
                    else build_result.error_message or "Deploy Pipeline build artifact was not produced."
                ),
            ),
        ]

        return DeployBuildStageResult(
            deployment_id=input_data.deployment_id,
            status=stage_status,
            build_status=build_result.status,
            artifact_ready=build_result.artifact_ready,
            output_directory=build_result.output_directory,
            duration_ms=build_result.duration_ms,
            error_message=build_result.error_message,
            logs=logs,
            metadata={
                "stage": "build",
                "build_status": build_result.status,
                "build_artifact_ready": build_result.artifact_ready,
                "build_duration_ms": build_result.duration_ms,
                "build_output_directory": build_result.output_directory,
            },
        )
