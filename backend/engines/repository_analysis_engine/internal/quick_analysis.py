from __future__ import annotations

from backend.engines.repository_analysis_engine.internal.build_command_detection import detect_build_command
from backend.engines.repository_analysis_engine.internal.deploy_readiness import evaluate_deploy_readiness
from backend.engines.repository_analysis_engine.internal.file_index import extract_file_paths
from backend.engines.repository_analysis_engine.internal.framework_detection import detect_framework
from backend.engines.repository_analysis_engine.internal.output_directory_detection import detect_output_directory
from backend.engines.repository_analysis_engine.internal.package_manager_detection import detect_package_manager
from backend.engines.repository_analysis_engine.internal.recommendations import build_recommendations
from backend.engines.repository_analysis_engine.internal.repository_score import calculate_repository_score
from backend.engines.repository_analysis_engine.internal.static_dynamic_detection import detect_static_dynamic
from backend.engines.repository_analysis_engine.internal.warnings import collect_warnings
from backend.engines.repository_analysis_engine.schemas import QuickAnalysisResult
from backend.engines.repository_engine.schemas import RepositoryAnalysisInput


class QuickAnalysisRunner:
    def run(self, repository: RepositoryAnalysisInput) -> QuickAnalysisResult:
        files = extract_file_paths(repository.file_tree_snapshot)
        framework = detect_framework(files)
        package_manager = detect_package_manager(files)
        build_command = detect_build_command(framework, package_manager)
        output_directory = detect_output_directory(framework)
        static_dynamic = detect_static_dynamic(files, framework)
        warnings = collect_warnings(
            framework=framework,
            build_command=build_command,
            output_directory=output_directory,
            static_dynamic=static_dynamic,
        )
        deploy_readiness = evaluate_deploy_readiness(
            framework=framework,
            build_command=build_command,
            output_directory=output_directory,
            static_dynamic=static_dynamic,
            warnings=warnings,
        )
        repository_score = calculate_repository_score(
            framework=framework,
            build_command=build_command,
            output_directory=output_directory,
            static_dynamic=static_dynamic,
            deploy_readiness=deploy_readiness,
        )
        recommendations = build_recommendations(
            framework=framework,
            output_directory=output_directory,
            deploy_readiness=deploy_readiness,
        )
        return QuickAnalysisResult(
            framework=framework,
            package_manager=package_manager,
            build_command=build_command,
            output_directory=output_directory,
            static_dynamic=static_dynamic,
            deploy_readiness=deploy_readiness,
            repository_score=repository_score,
            warnings=warnings,
            recommendations=recommendations,
        )
