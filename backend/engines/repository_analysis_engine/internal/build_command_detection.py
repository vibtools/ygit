from __future__ import annotations

from backend.engines.repository_analysis_engine.schemas import BuildCommandDetection, DetectionEvidence, FrameworkDetection, PackageManagerDetection


def detect_build_command(framework: FrameworkDetection, package_manager: PackageManagerDetection) -> BuildCommandDetection:
    if framework.framework in {"html", "unknown"}:
        return BuildCommandDetection(build_command=None, confidence=80 if framework.framework == "html" else 0, evidence=[DetectionEvidence(source="framework", reason="Static HTML or unknown repository does not require a detected build command.")])
    runner = {
        "npm": "npm run build",
        "pnpm": "pnpm build",
        "yarn": "yarn build",
        "bun": "bun run build",
    }.get(package_manager.package_manager, "npm run build")
    return BuildCommandDetection(build_command=runner, confidence=75, evidence=[DetectionEvidence(source="framework_package_manager", reason="Default build command inferred from framework and package manager.")])
