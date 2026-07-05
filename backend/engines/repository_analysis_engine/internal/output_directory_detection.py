from __future__ import annotations

from backend.engines.repository_analysis_engine.schemas import DetectionEvidence, FrameworkDetection, OutputDirectoryDetection


def detect_output_directory(framework: FrameworkDetection) -> OutputDirectoryDetection:
    mapping = {
        "html": (".", 85, "Static HTML can deploy from repository root."),
        "react": ("build", 65, "React default output is commonly build."),
        "vue": ("dist", 75, "Vue output is commonly dist."),
        "vite": ("dist", 90, "Vite default output is dist."),
        "astro": ("dist", 90, "Astro default output is dist."),
        "hugo": ("public", 90, "Hugo default output is public."),
        "docusaurus": ("build", 90, "Docusaurus default output is build."),
        "jekyll": ("_site", 90, "Jekyll default output is _site."),
    }
    output, confidence, reason = mapping.get(framework.framework, (None, 0, "Output directory cannot be inferred."))
    return OutputDirectoryDetection(output_directory=output, confidence=confidence, evidence=[DetectionEvidence(source="framework", reason=reason)])
