from __future__ import annotations

from backend.engines.repository_analysis_engine.schemas import AnalysisRecommendation, DeployReadiness, FrameworkDetection, OutputDirectoryDetection


def build_recommendations(*, framework: FrameworkDetection, output_directory: OutputDirectoryDetection, deploy_readiness: DeployReadiness) -> list[AnalysisRecommendation]:
    recommendations: list[AnalysisRecommendation] = []
    if framework.framework == "unknown":
        recommendations.append(AnalysisRecommendation(code="ADD_SUPPORTED_FRAMEWORK_FILES", message="Add framework/build configuration files so YGIT can detect deployment settings.", priority="high"))
    if output_directory.output_directory is None:
        recommendations.append(AnalysisRecommendation(code="CONFIGURE_OUTPUT_DIRECTORY", message="Define or confirm the static output directory before deployment.", priority="high"))
    if not deploy_readiness.deploy_ready:
        recommendations.append(AnalysisRecommendation(code="RESOLVE_BLOCKING_ANALYSIS_ITEMS", message="Resolve blocking deploy-readiness items before starting deployment.", priority="high"))
    if deploy_readiness.deploy_ready:
        recommendations.append(AnalysisRecommendation(code="READY_FOR_DEEP_ANALYSIS", message="Run deep analysis before deployment to validate build files and output settings.", priority="medium"))
    return recommendations
