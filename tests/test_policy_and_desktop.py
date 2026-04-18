from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from core.bootstrap.loader import boot_system
from plugins.document_plugin import DocumentPlugin
from plugins.presentation_plugin import PresentationPlugin


class PolicyAndDesktopWorkflowTest(unittest.TestCase):
    def setUp(self) -> None:
        root = Path("E:/OS/.test_tmp")
        root.mkdir(parents=True, exist_ok=True)
        self.base = Path(tempfile.mkdtemp(prefix="pd_", dir=str(root)))
        self.env_path = self.base / "runtime.env.json"
        self.env_path.write_text(
            json.dumps(
                {
                    "system_name": "test-os",
                    "deterministic_mode": True,
                    "data_dir": str(self.base / ".runtime_data"),
                    "default_project": "demo-project",
                    "allowed_capabilities": ["document.generate", "presentation.generate"],
                    "policy": {
                        "blocked_actions": [],
                        "confirm_required_actions": ["delete"],
                        "confirm_required_capabilities": [],
                        "acl": {
                            "users": {
                                "default": {
                                    "allowed_capabilities": ["document.generate", "presentation.generate"],
                                    "denied_capabilities": [],
                                    "allowed_surfaces": ["cli", "desktop"],
                                },
                                "restricted-user": {
                                    "allowed_capabilities": ["document.generate"],
                                    "denied_capabilities": ["presentation.generate"],
                                    "allowed_surfaces": ["cli"],
                                },
                            }
                        },
                    },
                }
            ),
            encoding="utf-8",
        )
        self.system = boot_system(str(self.env_path))
        self.system["plugin_registry"].register(DocumentPlugin())
        self.system["plugin_registry"].register(PresentationPlugin())

    def tearDown(self) -> None:
        shutil.rmtree(self.base, ignore_errors=True)

    def test_policy_autonomy_is_exposed(self) -> None:
        result = self.system["orchestrator"].execute_intent(
            {
                "user_id": "u1",
                "surface": "cli",
                "project": "p1",
                "action": "generate_document",
                "requested_capability": "document.generate",
                "payload": {"title": "T", "body": "B"},
            }
        )
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["autonomy_level"], "automatic")

    def test_document_to_presentation_workflow(self) -> None:
        result = self.system["orchestrator"].execute_workflow_document_to_presentation(
            user_id="u2",
            surface="desktop",
            project="p2",
            document_title="Doc",
            document_body="A\nB\nC",
            presentation_title="Deck",
        )
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["presentation_run"]["output"]["artifact_type"], "presentation_outline")
        ctx = self.system["orchestrator"].retrieve_context(user_id="u2", project="p2")
        self.assertEqual(ctx["latest_run"]["plugin_id"], "presentation.plugin.v1")

    def test_acl_blocks_denied_capability(self) -> None:
        with self.assertRaises(PermissionError):
            self.system["orchestrator"].execute_intent(
                {
                    "user_id": "restricted-user",
                    "surface": "cli",
                    "project": "p3",
                    "action": "generate_presentation",
                    "requested_capability": "presentation.generate",
                    "payload": {"title": "Denied", "source_document": "x"},
                }
            )

    def test_acl_blocks_surface(self) -> None:
        with self.assertRaises(PermissionError):
            self.system["orchestrator"].execute_intent(
                {
                    "user_id": "restricted-user",
                    "surface": "desktop",
                    "project": "p4",
                    "action": "generate_document",
                    "requested_capability": "document.generate",
                    "payload": {"title": "Denied", "body": "x"},
                }
            )


if __name__ == "__main__":
    unittest.main()
