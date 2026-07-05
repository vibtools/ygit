from __future__ import annotations

from backend.engines.repository_analysis_engine.schemas import (
    AnalysisWarning,
    BuildCommandDetection,
    FrameworkDetection,
    OutputDirectoryDetection,
    StaticDynamicDetection,
)


def collect_warnings(
    *,
    framework: FrameworkDetection,
    build_command: BuildCommandDetection,
    output_directory: OutputDirectoryDetection,
    static_dynamic: StaticDynamicDetection,
) -> list[AnalysisWarning]:
    warnings: list[AnalysisWarning] = []
    if framework.framework == "unknown":
        warnings.append(AnalysisWarning(code="ANALYSIS_FRAMEWORK_UNKNOWN", message="YGIT could not confidently detect the repository framework."))
    if build_command.build_command is None and framework.framework not in {"html", "unknown"}:
        warnings.append(AnalysisWarning(code="ANALYSIS_BUILD_COMMAND_UNKNOWN", message="Build command could not be detected."))
    if output_directory.output_directory is None:
        warnings.append(AnalysisWarning(code="ANALYSIS_OUTPUT_DIRECTORY_UNKNOWN", message="Output directory could not be detected."))
    if static_dynamic.render_mode == "dynamic":
        warnings.append(AnalysisWarning(code="ANALYSIS_DYNAMIC_APP_WARNING", message="Dynamic server behavior may not be supported by Cloudflare Pages static deployment."))
    return warnings
