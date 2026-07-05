from __future__ import annotations

from backend.engines.repository_analysis_engine.internal.file_index import has_file
from backend.engines.repository_analysis_engine.schemas import DetectionEvidence, PackageManagerDetection


def detect_package_manager(files: set[str]) -> PackageManagerDetection:
    if has_file(files, "pnpm-lock.yaml"):
        return PackageManagerDetection(package_manager="pnpm", confidence=98, evidence=[DetectionEvidence(source="file_tree", reason="Detected pnpm-lock.yaml.")])
    if has_file(files, "yarn.lock"):
        return PackageManagerDetection(package_manager="yarn", confidence=98, evidence=[DetectionEvidence(source="file_tree", reason="Detected yarn.lock.")])
    if has_file(files, "bun.lockb", "bun.lock"):
        return PackageManagerDetection(package_manager="bun", confidence=96, evidence=[DetectionEvidence(source="file_tree", reason="Detected Bun lockfile.")])
    if has_file(files, "package-lock.json", "package.json"):
        return PackageManagerDetection(package_manager="npm", confidence=88, evidence=[DetectionEvidence(source="file_tree", reason="Detected npm package files.")])
    return PackageManagerDetection(package_manager="none", confidence=70, evidence=[DetectionEvidence(source="file_tree", reason="No package manager files detected.")])
