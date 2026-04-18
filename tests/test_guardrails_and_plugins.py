from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from core.bootstrap.loader import boot_system
from core.plugin.sdk import PluginManifest
from plugins.document_plugin import DocumentPlugin


class NonDeterministicPlugin:
    manifest = PluginManifest(
        plugin_id="bad.plugin",
        version="0.1.0",
        capabilities=("document.generate",),
        deterministic=False,
    )

    def execute(self, action, payload):
        return {"artifact": "x"}


class GuardrailTest(unittest.TestCase):
    def setUp(self) -> None:
        root = Path("E:/OS/.test_tmp")
        root.mkdir(parents=True, exist_ok=True)
        self.base = Path(tempfile.mkdtemp(prefix="gr_", dir=str(root)))
        self.env_path = self.base / "runtime.env.json"
        self.env_path.write_text(
            json.dumps(
                {
                    "system_name": "test-os",
                    "deterministic_mode": True,
                    "data_dir": str(self.base / ".runtime_data"),
                    "default_project": "demo-project",
                    "allowed_capabilities": ["document.generate"],
                }
            ),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.base, ignore_errors=True)

    def test_non_deterministic_plugin_is_rejected(self) -> None:
        system = boot_system(str(self.env_path))
        with self.assertRaises(ValueError):
            system["plugin_registry"].register(NonDeterministicPlugin())

    def test_confirm_required_action(self) -> None:
        system = boot_system(str(self.env_path))
        system["plugin_registry"].register(DocumentPlugin())
        with self.assertRaises(PermissionError):
            system["orchestrator"].execute_intent(
                {
                    "user_id": "u1",
                    "surface": "cli",
                    "project": "p1",
                    "action": "delete",
                    "requested_capability": "document.generate",
                    "payload": {"title": "x", "body": "y"},
                },
                require_confirmation=False,
            )


if __name__ == "__main__":
    unittest.main()
