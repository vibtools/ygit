from __future__ import annotations

from backend.pipelines.build_pipeline.public import BuildPipelinePublicService
from backend.pipelines.build_pipeline.schemas import BuildExecutionInput, BuildExecutionResult, BuildPlan


class DeployPipelineBuildAdapter:
    """Deploy Pipeline boundary adapter for real build execution.

    The deploy pipeline owns orchestration. The build pipeline owns controlled
    subprocess execution. This adapter keeps that boundary explicit and prevents
    API routes, engines, or worker jobs from reaching into build internals.
    """

    def __init__(self, build_service: BuildPipelinePublicService | None = None) -> None:
        self.build_service = build_service or BuildPipelinePublicService()

    def run_repository_build(
        self,
        *,
        repository_path: str,
        package_manager: str | None,
        build_command: str | None,
        output_directory: str | None,
        root_directory: str = ".",
        install_command: str | None = None,
        timeout_seconds: int = 600,
        environment: dict[str, str] | None = None,
    ) -> BuildExecutionResult:
        if not build_command:
            raise ValueError("Deploy pipeline build command is required.")
        if not output_directory:
            raise ValueError("Deploy pipeline output directory is required.")

        plan = BuildPlan(
            package_manager=self._normalize_package_manager(package_manager),
            install_command=install_command,
            build_command=build_command,
            output_directory=output_directory,
            root_directory=root_directory or ".",
            timeout_seconds=timeout_seconds,
        )
        return self.build_service.run_build(
            BuildExecutionInput(
                repository_path=repository_path,
                plan=plan,
                environment=environment or {},
            )
        )

    def _normalize_package_manager(self, value: str | None) -> str:
        normalized = (value or "unknown").strip().lower()
        if normalized in {"npm", "pnpm", "yarn", "bun", "none"}:
            return normalized
        return "unknown"
