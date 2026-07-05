from __future__ import annotations

from backend.engines.repository_analysis_engine.internal.file_index import has_file, has_prefix, has_suffix
from backend.engines.repository_analysis_engine.schemas import DetectionEvidence, FrameworkDetection


def detect_framework(files: set[str]) -> FrameworkDetection:
    evidence: list[DetectionEvidence] = []
    framework = "unknown"
    confidence = 0
    if has_file(files, "astro.config.mjs", "astro.config.ts"):
        framework, confidence = "astro", 95
        evidence.append(DetectionEvidence(source="file_tree", reason="Detected Astro configuration."))
    elif has_file(files, "docusaurus.config.js", "docusaurus.config.ts"):
        framework, confidence = "docusaurus", 95
        evidence.append(DetectionEvidence(source="file_tree", reason="Detected Docusaurus configuration."))
    elif has_file(files, "hugo.toml", "config.toml", "config.yaml") and has_prefix(files, "layouts", "content"):
        framework, confidence = "hugo", 90
        evidence.append(DetectionEvidence(source="file_tree", reason="Detected Hugo layout/content structure."))
    elif has_file(files, "_config.yml"):
        framework, confidence = "jekyll", 90
        evidence.append(DetectionEvidence(source="file_tree", reason="Detected Jekyll _config.yml."))
    elif has_file(files, "vite.config.js", "vite.config.ts", "vite.config.mjs"):
        framework, confidence = "vite", 88
        evidence.append(DetectionEvidence(source="file_tree", reason="Detected Vite configuration."))
    elif has_file(files, "package.json") and (has_suffix(files, ".jsx", ".tsx") or has_prefix(files, "src")):
        framework, confidence = "react", 76
        evidence.append(DetectionEvidence(source="file_tree", reason="Detected package.json with React-style source layout."))
    elif has_suffix(files, ".vue"):
        framework, confidence = "vue", 84
        evidence.append(DetectionEvidence(source="file_tree", reason="Detected Vue single-file components."))
    elif has_file(files, "index.html"):
        framework, confidence = "html", 80
        evidence.append(DetectionEvidence(source="file_tree", reason="Detected static index.html."))
    return FrameworkDetection(framework=framework, confidence=confidence, evidence=evidence)
