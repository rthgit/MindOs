from __future__ import annotations

import subprocess
from typing import Any, Dict, List

from core.platform.host import platform_key
from core.plugin.program_catalog import ProgramSpec
from core.plugin.sandbox import ProgramSandboxPolicy
from core.plugin.sdk import PluginManifest


class ExternalProgramPlugin:
    def __init__(self, spec: ProgramSpec, sandbox_policy: ProgramSandboxPolicy) -> None:
        self.spec = spec
        self.sandbox_policy = sandbox_policy
        self.manifest = PluginManifest(
            plugin_id=spec.plugin_id,
            version=spec.version,
            capabilities=spec.capabilities,
            deterministic=spec.deterministic,
        )

    def _command(self, args: List[str]) -> List[str]:
        key = platform_key()
        base = self.spec.command_by_platform.get(key)
        if not base:
            raise RuntimeError(f"Program {self.spec.plugin_id} not supported on platform {key}")
        return [*base, *args]

    def execute(self, action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if action != "execute_program":
            raise ValueError(f"Unsupported action for program plugin: {action}")
        args_raw = payload.get("args", [])
        if not isinstance(args_raw, list):
            raise ValueError("payload.args must be a list")
        args = [str(v) for v in args_raw]
        command = self._command(args)

        if bool(payload.get("dry_run", False)):
            return {
                "artifact_type": "program_execution_preview",
                "artifact": {"command": command, "mode": "dry_run"},
            }

        if not self.sandbox_policy.allow_real_execution:
            raise PermissionError("Program real execution disabled by sandbox policy")

        first_capability = self.spec.capabilities[0] if self.spec.capabilities else ""
        if first_capability not in self.sandbox_policy.allowed_capabilities_for_real_execution:
            raise PermissionError(
                f"Program capability not allowed for real execution: {first_capability}"
            )

        timeout = int(payload.get("timeout_sec", 30))
        if timeout > self.sandbox_policy.max_timeout_sec:
            raise PermissionError(
                f"Timeout exceeds sandbox max_timeout_sec={self.sandbox_policy.max_timeout_sec}"
            )
        proc = subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)
        return {
            "artifact_type": "program_execution_result",
            "artifact": {
                "command": command,
                "returncode": proc.returncode,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
            },
        }
