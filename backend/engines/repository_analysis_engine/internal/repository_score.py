from __future__ import annotations

from backend.engines.repository_analysis_engine.schemas import (
    BuildCommandDetection,
    DeployReadiness,
    FrameworkDetection,
    OutputDirectoryDetection,
    RepositoryScore,
    StaticDynamicDetection,
)


def calculate_repository_score(
    *,
    framework: FrameworkDetection,
    build_command: BuildCommandDetection,
    output_directory: OutputDirectoryDetection,
    static_dynamic: StaticDynamicDetection,
    deploy_readiness: DeployReadiness,
) -> RepositoryScore:
    factors = {
        "framework": framework.confidence,
        "package_build": build_command.confidence,
        "output_directory": output_directory.confidence,
        "static_compatibility": 100 if static_dynamic.render_mode == "static" else 30 if static_dynamic.render_mode == "dynamic" else 50,
        "deploy_readiness": 100 if deploy_readiness.deploy_ready else 35,
    }
    score = max(0, min(100, round(sum(factors.values()) / len(factors))))
    grade = "A" if score >= 90 else "B" if score >= 80 else "C" if score >= 70 else "D" if score >= 60 else "F"
    return RepositoryScore(score=score, grade=grade, factors=factors)
