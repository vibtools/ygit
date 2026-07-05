from __future__ import annotations

from backend.engines.repository_analysis_engine.schemas import (
    AnalysisWarning,
    BuildCommandDetection,
    DeployReadiness,
    FrameworkDetection,
    OutputDirectoryDetection,
    StaticDynamicDetection,
)


def evaluate_deploy_readiness(
    *,
    framework: FrameworkDetection,
    build_command: BuildCommandDetection,
    output_directory: OutputDirectoryDetection,
    static_dynamic: StaticDynamicDetection,
    warnings: list[AnalysisWarning],
) -> DeployReadiness:
    blocking: list[str] = []
    if framework.framework == "unknown":
        blocking.append("Unsupported or unknown framework.")
    if output_directory.output_directory is None:
        blocking.append("Output directory is unknown.")
    if static_dynamic.render_mode == "dynamic":
        blocking.append("Dynamic server behavior detected; static deployment validation failed.")
    if framework.framework not in {"html", "unknown"} and build_command.build_command is None:
        blocking.append("Build command is unknown.")
    return DeployReadiness(deploy_ready=not blocking, blocking_reasons=blocking, warnings=warnings)
