from __future__ import annotations

from backend.pipelines.build_pipeline.internal.runner import BuildRunner
from backend.pipelines.build_pipeline.schemas import BuildExecutionInput, BuildExecutionResult


class BuildPipelinePublicService:
    """Public boundary for worker/deploy pipeline build execution."""

    def __init__(self, runner: BuildRunner | None = None) -> None:
        self.runner = runner or BuildRunner()

    def run_build(self, input_data: BuildExecutionInput) -> BuildExecutionResult:
        return self.runner.run(input_data)


build_pipeline_service = BuildPipelinePublicService()
