from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from core.bootstrap.loader import boot_system
from plugins.document_plugin import DocumentPlugin


class VerticalSliceE2ETest(unittest.TestCase):
    def setUp(self) -> None:
        root = Path("E:/OS/.test_tmp")
        root.mkdir(parents=True, exist_ok=True)
        self.base = Path(tempfile.mkdtemp(prefix="vs_", dir=str(root)))
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

        self.system = boot_system(str(self.env_path))
        self.system["plugin_registry"].register(DocumentPlugin())

    def tearDown(self) -> None:
        shutil.rmtree(self.base, ignore_errors=True)

    def test_cli_to_ide_continuity_and_audit(self) -> None:
        result = self.system["orchestrator"].execute_intent(
            {
                "user_id": "u1",
                "surface": "cli",
                "project": "p1",
                "action": "generate_document",
                "requested_capability": "document.generate",
                "payload": {"title": "T1", "body": "B1"},
            }
        )
        self.assertEqual(result["status"], "completed")
        self.assertIn("artifact", result["output"])

        ide_context = self.system["orchestrator"].retrieve_context("u1", "p1")
        self.assertEqual(ide_context["latest_run"]["status"], "completed")
        self.assertEqual(ide_context["latest_run"]["output"]["artifact"], "# T1\n\nB1")

        events = self.system["memory"].list_events(correlation_id=result["correlation_id"])
        event_types = [e["event_type"] for e in events]
        self.assertEqual(event_types, ["IntentAccepted", "PlanCreated", "RunStarted", "RunFinished"])

    def test_deterministic_plan_id(self) -> None:
        intent = {
            "user_id": "u2",
            "surface": "cli",
            "project": "p2",
            "action": "generate_document",
            "requested_capability": "document.generate",
            "payload": {"title": "Same", "body": "Same"},
        }
        result1 = self.system["orchestrator"].execute_intent(intent)
        result2 = self.system["orchestrator"].execute_intent(intent)
        self.assertEqual(result1["plan_id"], result2["plan_id"])
        self.assertEqual(result1["output"], result2["output"])

    def test_rollback_internal(self) -> None:
        result = self.system["orchestrator"].execute_intent(
            {
                "user_id": "u3",
                "surface": "cli",
                "project": "p3",
                "action": "generate_document",
                "requested_capability": "document.generate",
                "payload": {"title": "Rollback", "body": "Case"},
            }
        )
        rollback = self.system["orchestrator"].rollback_internal(result["run_id"])
        self.assertEqual(rollback["status"], "rolled_back")


if __name__ == "__main__":
    unittest.main()
