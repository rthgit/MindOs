from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from core.bootstrap.loader import boot_system


class ProgramPluginCrossPlatformTest(unittest.TestCase):
    def setUp(self) -> None:
        root = Path("E:/OS/.test_tmp")
        root.mkdir(parents=True, exist_ok=True)
        self.base = Path(tempfile.mkdtemp(prefix="pp_", dir=str(root)))
        self.env_path = self.base / "runtime.env.json"
        self.env_path.write_text(
            json.dumps(
                {
                    "system_name": "test-os",
                    "deterministic_mode": True,
                    "data_dir": str(self.base / ".runtime_data"),
                    "default_project": "demo-project",
                    "allowed_capabilities": [
                        "document.generate",
                        "presentation.generate",
                        "program.echo.execute",
                        "program.python.execute",
                    ],
                    "bootstrap_plugins": ["document.plugin.v1"],
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
                                        "program.python.execute",
                                    ],
                                    "denied_capabilities": [],
                                    "allowed_surfaces": ["cli", "desktop", "ide"],
                                }
                            }
                        },
                    },
                }
            ),
            encoding="utf-8",
        )
        self.system = boot_system(str(self.env_path))

    def tearDown(self) -> None:
        shutil.rmtree(self.base, ignore_errors=True)

    def test_program_install_and_run_via_orchestrator(self) -> None:
        install = self.system["plugin_manager"].install_program("shell.echo.program.v1")
        self.assertEqual(install["status"], "installed")
        self.assertEqual(install["kind"], "program")

        run = self.system["orchestrator"].execute_intent(
            {
                "user_id": "u1",
                "surface": "cli",
                "project": "p1",
                "action": "execute_program",
                "requested_capability": "program.echo.execute",
                "payload": {"args": ["hello"], "dry_run": True},
            }
        )
        self.assertEqual(run["status"], "completed")
        self.assertEqual(run["output"]["artifact_type"], "program_execution_preview")


if __name__ == "__main__":
    unittest.main()
