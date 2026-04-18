from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from core.bootstrap.loader import boot_system


class PluginManagerTest(unittest.TestCase):
    def setUp(self) -> None:
        root = Path("E:/OS/.test_tmp")
        root.mkdir(parents=True, exist_ok=True)
        self.base = Path(tempfile.mkdtemp(prefix="pm_", dir=str(root)))
        self.env_path = self.base / "runtime.env.json"
        self.env_path.write_text(
            json.dumps(
                {
                    "system_name": "test-os",
                    "deterministic_mode": True,
                    "data_dir": str(self.base / ".runtime_data"),
                    "default_project": "demo-project",
                    "allowed_capabilities": ["document.generate", "presentation.generate"],
                    "bootstrap_plugins": ["document.plugin.v1"],
                    "policy": {
                        "blocked_actions": [],
                        "confirm_required_actions": ["delete"],
                        "confirm_required_capabilities": [],
                        "acl": {
                            "users": {
                                "default": {
                                    "allowed_capabilities": ["document.generate", "presentation.generate"],
                                    "denied_capabilities": [],
                                    "allowed_surfaces": ["cli", "ide", "desktop"],
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

    def test_bootstrap_install_and_list(self) -> None:
        installed = self.system["plugin_manager"].list_installed()
        self.assertIn("document.plugin.v1", installed)

    def test_install_remove_upgrade(self) -> None:
        install = self.system["plugin_manager"].install("presentation.plugin.v1")
        self.assertEqual(install["status"], "installed")
        installed = self.system["plugin_manager"].list_installed()
        self.assertIn("presentation.plugin.v1", installed)

        upgrade = self.system["plugin_manager"].upgrade("presentation.plugin.v1")
        self.assertEqual(upgrade["status"], "installed")

        remove = self.system["plugin_manager"].remove("presentation.plugin.v1")
        self.assertEqual(remove["status"], "removed")
        installed_after = self.system["plugin_manager"].list_installed()
        self.assertNotIn("presentation.plugin.v1", installed_after)


if __name__ == "__main__":
    unittest.main()
