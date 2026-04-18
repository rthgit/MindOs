from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Protocol


@dataclass(frozen=True)
class PluginManifest:
    plugin_id: str
    version: str
    capabilities: tuple[str, ...]
    deterministic: bool


class Plugin(Protocol):
    manifest: PluginManifest

    def execute(self, action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        ...
