from __future__ import annotations

import json
import subprocess
from dataclasses import asdict
from pathlib import Path
from typing import Dict, List

from core.platform.host import platform_key
from core.plugin.catalog import PLUGIN_CATALOG, available_plugins
from core.plugin.catalog_metadata import INTERNAL_PLUGIN_METADATA
from core.plugin.program_catalog import ProgramSpec, available_programs, merge_program_catalog
from core.plugin.program_plugin import ExternalProgramPlugin
from core.plugin.registry import PluginRegistry
from core.plugin.sandbox import ProgramSandboxPolicy
from core.plugin.trust import TrustPolicy, build_integrity_hash


class PluginManager:
    def __init__(
        self,
        data_dir: Path,
        registry: PluginRegistry,
        bootstrap_plugins: List[str] | None = None,
        trust_policy_config: Dict | None = None,
        sandbox_policy_config: Dict | None = None,
        external_program_registry_file: str | None = None,
    ) -> None:
        self.data_dir = data_dir
        self.registry = registry
        self.bootstrap_plugins = bootstrap_plugins or []
        self.trust_policy = TrustPolicy.from_config(trust_policy_config)
        self.sandbox_policy = ProgramSandboxPolicy.from_config(sandbox_policy_config)
        self.external_program_registry_file = external_program_registry_file
        self.program_catalog = merge_program_catalog(external_registry_file=external_program_registry_file)
        self.state_file = self.data_dir / "installed_plugins.json"
        self.lock_file = self.data_dir / "plugins.lock.json"
        self._ensure_files()

    def _ensure_files(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        if not self.state_file.exists():
            self.state_file.write_text(json.dumps({"installed": {}}, indent=2), encoding="utf-8")
        if not self.lock_file.exists():
            self.lock_file.write_text(json.dumps({"locked": {}}, indent=2), encoding="utf-8")

    def _read_state(self) -> Dict[str, Dict[str, dict]]:
        text = self.state_file.read_text(encoding="utf-8").strip()
        if not text:
            return {"installed": {}}
        value = json.loads(text)
        if "installed" not in value:
            value["installed"] = {}
        return value

    def _write_state(self, state: Dict[str, Dict[str, dict]]) -> None:
        self.state_file.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")

    def _read_lock(self) -> Dict[str, Dict[str, dict]]:
        text = self.lock_file.read_text(encoding="utf-8").strip()
        if not text:
            return {"locked": {}}
        value = json.loads(text)
        if "locked" not in value:
            value["locked"] = {}
        return value

    def _write_lock(self, lock: Dict[str, Dict[str, dict]]) -> None:
        self.lock_file.write_text(json.dumps(lock, indent=2, sort_keys=True), encoding="utf-8")

    def _build_internal_plugin(self, plugin_id: str):
        factory = PLUGIN_CATALOG.get(plugin_id)
        if not factory:
            raise KeyError(f"Internal plugin not found in catalog: {plugin_id}")
        plugin = factory()
        meta = INTERNAL_PLUGIN_METADATA.get(plugin_id)
        if not meta:
            raise PermissionError(f"Missing trust metadata for internal plugin: {plugin_id}")
        actual = build_integrity_hash(
            kind="internal",
            plugin_id=plugin.manifest.plugin_id,
            version=plugin.manifest.version,
            capabilities=plugin.manifest.capabilities,
            deterministic=plugin.manifest.deterministic,
        )
        self.trust_policy.assert_trusted(
            plugin_id=plugin_id,
            signer=meta.signer,
            expected_integrity=meta.integrity,
            actual_integrity=actual,
            signature=meta.signature,
        )
        return plugin

    def _build_program_plugin(self, plugin_id: str):
        spec = self.program_catalog.get(plugin_id)
        if not spec:
            raise KeyError(f"Program plugin not found in catalog: {plugin_id}")
        actual = build_integrity_hash(
            kind="program",
            plugin_id=spec.plugin_id,
            version=spec.version,
            capabilities=spec.capabilities,
            deterministic=spec.deterministic,
            platform_commands=spec.command_by_platform,
        )
        self.trust_policy.assert_trusted(
            plugin_id=plugin_id,
            signer=spec.signer,
            expected_integrity=spec.integrity,
            actual_integrity=actual,
            signature=spec.signature,
        )
        return ExternalProgramPlugin(spec, sandbox_policy=self.sandbox_policy)

    def _register_and_persist(self, *, plugin_id: str, kind: str, plugin_obj) -> Dict[str, str]:
        self.registry.register(plugin_obj)
        manifest = asdict(plugin_obj.manifest)

        state = self._read_state()
        state["installed"][plugin_id] = {"kind": kind, "manifest": manifest}
        self._write_state(state)

        lock = self._read_lock()
        lock["locked"][plugin_id] = {"version": manifest["version"], "kind": kind}
        self._write_lock(lock)

        return {"plugin_id": plugin_id, "version": manifest["version"], "status": "installed", "kind": kind}

    def install(self, plugin_id: str) -> Dict[str, str]:
        plugin = self._build_internal_plugin(plugin_id)
        return self._register_and_persist(plugin_id=plugin_id, kind="internal", plugin_obj=plugin)

    def install_program(self, plugin_id: str, execute_install: bool = False) -> Dict[str, str]:
        spec = self.program_catalog.get(plugin_id)
        if not spec:
            raise KeyError(f"Program plugin not found in catalog: {plugin_id}")
        pkey = platform_key()
        if pkey not in spec.command_by_platform:
            raise RuntimeError(f"Program {plugin_id} unsupported on platform {pkey}")

        install_cmd = spec.install_by_platform.get(pkey, [])
        if execute_install and install_cmd:
            proc = subprocess.run(install_cmd, capture_output=True, text=True, check=False)
            if proc.returncode != 0:
                raise RuntimeError(
                    f"Program install command failed for {plugin_id}: returncode={proc.returncode}, stderr={proc.stderr}"
                )

        plugin = self._build_program_plugin(plugin_id)
        return self._register_and_persist(plugin_id=plugin_id, kind="program", plugin_obj=plugin)

    def remove(self, plugin_id: str) -> Dict[str, str]:
        state = self._read_state()
        installed = state["installed"].get(plugin_id)
        if not installed:
            return {"plugin_id": plugin_id, "status": "not_installed"}
        del state["installed"][plugin_id]
        self._write_state(state)
        self.registry.unregister(plugin_id)

        lock = self._read_lock()
        if plugin_id in lock["locked"]:
            del lock["locked"][plugin_id]
            self._write_lock(lock)
        return {"plugin_id": plugin_id, "status": "removed"}

    def list_installed(self) -> Dict[str, dict]:
        state = self._read_state()
        out: Dict[str, dict] = {}
        for pid, row in state["installed"].items():
            kind = row.get("kind", "internal")
            manifest = row.get("manifest", {})
            out[pid] = {"kind": kind, **manifest}
        return out

    def upgrade(self, plugin_id: str) -> Dict[str, str]:
        state = self._read_state()
        row = state["installed"].get(plugin_id)
        if row and row.get("kind") == "program":
            return self.install_program(plugin_id)
        if plugin_id in self.program_catalog:
            return self.install_program(plugin_id)
        return self.install(plugin_id)

    def bootstrap_default_plugins(self) -> None:
        for plugin_id in self.bootstrap_plugins:
            if plugin_id in self.program_catalog:
                self.install_program(plugin_id)
            else:
                self.install(plugin_id)

    def sync_registry_from_installed(self) -> None:
        installed = self._read_state()["installed"]
        for plugin_id, row in sorted(installed.items()):
            kind = row.get("kind", "internal")
            if kind == "program":
                plugin = self._build_program_plugin(plugin_id)
            else:
                plugin = self._build_internal_plugin(plugin_id)
            self.registry.register(plugin)

    def list_catalog(self) -> List[str]:
        return available_plugins()

    def list_program_catalog(self) -> List[str]:
        return available_programs(self.external_program_registry_file)
