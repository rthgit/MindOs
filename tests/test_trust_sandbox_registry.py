from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from core.bootstrap.loader import boot_system
from core.plugin.trust import build_integrity_hash, sign_integrity


class TrustSandboxRegistryTest(unittest.TestCase):
    def setUp(self) -> None:
        root = Path("E:/OS/.test_tmp")
        root.mkdir(parents=True, exist_ok=True)
        self.base = Path(tempfile.mkdtemp(prefix="tsr_", dir=str(root)))
        self.registry_file = self.base / "external_programs.json"

    def tearDown(self) -> None:
        shutil.rmtree(self.base, ignore_errors=True)

    def _write_env(
        self,
        *,
        trusted_signers: list[str],
        allow_real_execution: bool,
        allowed_exec_caps: list[str],
        bootstrap_plugins: list[str] | None = None,
    ) -> Path:
        env_path = self.base / "runtime.env.json"
        env = {
            "system_name": "test-os",
            "deterministic_mode": True,
            "data_dir": str(self.base / ".runtime_data"),
            "default_project": "demo-project",
            "allowed_capabilities": [
                "document.generate",
                "presentation.generate",
                "program.echo.execute",
                "program.custom.execute",
            ],
            "bootstrap_plugins": bootstrap_plugins if bootstrap_plugins is not None else ["document.plugin.v1"],
            "program_registry_file": str(self.registry_file),
            "policy": {
                "blocked_actions": [],
                "confirm_required_actions": ["delete"],
                "confirm_required_capabilities": [],
                "acl": {
                    "users": {
                        "default": {
                            "allowed_capabilities": [
                                "document.generate",
                                "presentation.generate",
                                "program.echo.execute",
                                "program.custom.execute",
                            ],
                            "denied_capabilities": [],
                            "allowed_surfaces": ["cli", "desktop", "ide"],
                        }
                    }
                },
                "plugin_trust": {"require_integrity": True, "trusted_signers": trusted_signers},
                "program_sandbox": {
                    "max_timeout_sec": 5,
                    "allow_real_execution": allow_real_execution,
                    "allowed_capabilities_for_real_execution": allowed_exec_caps,
                },
            },
        }
        env["policy"]["plugin_trust"]["require_signature"] = True
        env["policy"]["plugin_trust"]["revoked_signers"] = []
        env["policy"]["plugin_trust"]["signer_keys"] = {
            "core-team": "core-team-dev-key",
            "unknown-signer": "unknown-signer-dev-key",
        }
        env_path.write_text(json.dumps(env), encoding="utf-8")
        return env_path

    def _write_external_registry(self, signer: str = "core-team") -> None:
        command_by_platform = {
            "windows": ["powershell", "-NoProfile", "-Command", "Write-Output"],
            "linux": ["/bin/echo"],
        }
        integrity = build_integrity_hash(
            kind="program",
            plugin_id="custom.echo.program.v1",
            version="1.0.0",
            capabilities=["program.custom.execute"],
            deterministic=True,
            platform_commands=command_by_platform,
        )
        signer_key = "core-team-dev-key" if signer == "core-team" else "unknown-signer-dev-key"
        row = {
            "plugin_id": "custom.echo.program.v1",
            "version": "1.0.0",
            "capabilities": ["program.custom.execute"],
            "deterministic": True,
            "command_by_platform": command_by_platform,
            "install_by_platform": {},
            "signer": signer,
            "integrity": integrity,
            "signature": sign_integrity(integrity=integrity, signer_key=signer_key),
        }
        self.registry_file.write_text(json.dumps([row]), encoding="utf-8")

    def test_untrusted_signer_is_blocked(self) -> None:
        self._write_external_registry(signer="unknown-signer")
        env = self._write_env(
            trusted_signers=["core-team"],
            allow_real_execution=True,
            allowed_exec_caps=["program.echo.execute"],
            bootstrap_plugins=[],
        )
        system = boot_system(str(env))
        with self.assertRaises(PermissionError):
            system["plugin_manager"].install_program("custom.echo.program.v1")

    def test_external_registry_install_and_dry_run(self) -> None:
        self._write_external_registry(signer="core-team")
        env = self._write_env(trusted_signers=["core-team"], allow_real_execution=True, allowed_exec_caps=["program.echo.execute"])
        system = boot_system(str(env))
        install = system["plugin_manager"].install_program("custom.echo.program.v1")
        self.assertEqual(install["status"], "installed")
        run = system["orchestrator"].execute_intent(
            {
                "user_id": "u1",
                "surface": "cli",
                "project": "p1",
                "action": "execute_program",
                "requested_capability": "program.custom.execute",
                "payload": {"args": ["hello"], "dry_run": True},
            }
        )
        self.assertEqual(run["status"], "completed")
        self.assertEqual(run["output"]["artifact_type"], "program_execution_preview")

    def test_sandbox_blocks_real_execution_for_not_allowed_capability(self) -> None:
        self._write_external_registry(signer="core-team")
        env = self._write_env(trusted_signers=["core-team"], allow_real_execution=True, allowed_exec_caps=["program.echo.execute"])
        system = boot_system(str(env))
        system["plugin_manager"].install_program("custom.echo.program.v1")
        with self.assertRaises(PermissionError):
            system["orchestrator"].execute_intent(
                {
                    "user_id": "u1",
                    "surface": "cli",
                    "project": "p1",
                    "action": "execute_program",
                    "requested_capability": "program.custom.execute",
                    "payload": {"args": ["hello"], "dry_run": False},
                }
            )

    def test_revoked_signer_is_blocked(self) -> None:
        self._write_external_registry(signer="core-team")
        env = self._write_env(
            trusted_signers=["core-team"],
            allow_real_execution=True,
            allowed_exec_caps=["program.echo.execute"],
            bootstrap_plugins=[],
        )
        env_obj = json.loads(Path(env).read_text(encoding="utf-8"))
        env_obj["policy"]["plugin_trust"]["revoked_signers"] = ["core-team"]
        Path(env).write_text(json.dumps(env_obj), encoding="utf-8")
        system = boot_system(str(env))
        with self.assertRaises(PermissionError):
            system["plugin_manager"].install_program("custom.echo.program.v1")


if __name__ == "__main__":
    unittest.main()
