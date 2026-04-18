from __future__ import annotations

from typing import Any, Dict

from core.plugin.sdk import PluginManifest


class DocumentPlugin:
    manifest = PluginManifest(
        plugin_id="document.plugin.v1",
        version="1.0.0",
        capabilities=("document.generate",),
        deterministic=True,
    )

    def execute(self, action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if action != "generate_document":
            raise ValueError(f"Unsupported action: {action}")
        title = str(payload.get("title", "Untitled"))
        body = str(payload.get("body", ""))
        artifact = f"# {title}\n\n{body}".strip()
        return {
            "artifact_type": "document_markdown",
            "artifact": artifact,
        }
