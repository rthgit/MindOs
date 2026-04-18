from __future__ import annotations

from dataclasses import asdict
from typing import Dict, Set

from core.plugin.sdk import Plugin


class PluginRegistry:
    def __init__(self, allowed_capabilities: Set[str]) -> None:
        self.allowed_capabilities = allowed_capabilities
        self._plugins: Dict[str, Plugin] = {}
        self._capability_to_plugin: Dict[str, str] = {}

    def register(self, plugin: Plugin) -> None:
        manifest = plugin.manifest
        if not manifest.deterministic:
            raise ValueError(f"Plugin {manifest.plugin_id} rejected: deterministic=false")
        for cap in manifest.capabilities:
            if cap not in self.allowed_capabilities:
                raise ValueError(f"Plugin {manifest.plugin_id} rejected: capability {cap} not allowed")
            self._capability_to_plugin[cap] = manifest.plugin_id
        self._plugins[manifest.plugin_id] = plugin

    def resolve_by_capability(self, capability: str) -> Plugin:
        plugin_id = self._capability_to_plugin.get(capability)
        if not plugin_id:
            raise KeyError(f"No plugin registered for capability {capability}")
        return self._plugins[plugin_id]

    def describe(self) -> Dict[str, dict]:
        out: Dict[str, dict] = {}
        for pid, plugin in self._plugins.items():
            out[pid] = asdict(plugin.manifest)
        return out

    def unregister(self, plugin_id: str) -> None:
        plugin = self._plugins.pop(plugin_id, None)
        if not plugin:
            return
        for cap in plugin.manifest.capabilities:
            owner = self._capability_to_plugin.get(cap)
            if owner == plugin_id:
                del self._capability_to_plugin[cap]
