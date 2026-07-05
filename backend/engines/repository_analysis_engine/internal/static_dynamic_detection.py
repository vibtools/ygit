from __future__ import annotations

from backend.engines.repository_analysis_engine.internal.file_index import has_file, has_prefix
from backend.engines.repository_analysis_engine.schemas import DetectionEvidence, FrameworkDetection, StaticDynamicDetection


def detect_static_dynamic(files: set[str], framework: FrameworkDetection) -> StaticDynamicDetection:
    evidence: list[DetectionEvidence] = []
    if framework.framework in {"html", "hugo", "jekyll"}:
        evidence.append(DetectionEvidence(source="framework", reason="Framework normally produces static output."))
        return StaticDynamicDetection(render_mode="static", confidence=90, evidence=evidence)
    if has_file(files, "next.config.js", "next.config.mjs", "next.config.ts") or has_prefix(files, "pages/api", "app/api"):
        evidence.append(DetectionEvidence(source="file_tree", reason="Detected Next/API-style dynamic routes."))
        return StaticDynamicDetection(render_mode="dynamic", confidence=82, evidence=evidence)
    if framework.framework in {"vite", "react", "vue", "astro", "docusaurus"}:
        evidence.append(DetectionEvidence(source="framework", reason="Detected frontend framework can be deployed as static build output."))
        return StaticDynamicDetection(render_mode="static", confidence=75, evidence=evidence)
    return StaticDynamicDetection(render_mode="unknown", confidence=0, evidence=[])
