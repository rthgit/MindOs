from __future__ import annotations

from typing import Any, Dict, List

from core.plugin.sdk import PluginManifest


class PresentationPlugin:
    manifest = PluginManifest(
        plugin_id="presentation.plugin.v1",
        version="1.0.0",
        capabilities=("presentation.generate",),
        deterministic=True,
    )

    def execute(self, action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if action != "generate_presentation":
            raise ValueError(f"Unsupported action: {action}")

        title = str(payload.get("title", "Presentation"))
        source_document = str(payload.get("source_document", "")).strip()
        lines = [line.strip() for line in source_document.splitlines() if line.strip()]
        bullet_lines: List[str] = [line for line in lines if not line.startswith("#")]

        if not bullet_lines:
            bullet_lines = ["No content extracted from source document."]

        slides = []
        for idx, chunk_start in enumerate(range(0, len(bullet_lines), 4), start=1):
            chunk = bullet_lines[chunk_start : chunk_start + 4]
            slide = {"slide_title": f"{title} - Part {idx}", "bullets": chunk}
            slides.append(slide)

        return {
            "artifact_type": "presentation_outline",
            "artifact": {
                "title": title,
                "slides": slides,
            },
        }
