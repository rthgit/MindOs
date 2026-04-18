from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from core.bootstrap.loader import boot_system
from plugins.document_plugin import DocumentPlugin
from plugins.presentation_plugin import PresentationPlugin


class SchedulerTest(unittest.TestCase):
    def setUp(self) -> None:
        root = Path("E:/OS/.test_tmp")
        root.mkdir(parents=True, exist_ok=True)
        self.base = Path(tempfile.mkdtemp(prefix="sch_", dir=str(root)))
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
        self.system["plugin_registry"].register(DocumentPlugin())
        self.system["plugin_registry"].register(PresentationPlugin())

    def tearDown(self) -> None:
        shutil.rmtree(self.base, ignore_errors=True)

    def test_scheduler_executes_pattern_once_and_disables(self) -> None:
        self.system["orchestrator"].promote_to_procedural_memory(
            "sched_doc",
            {
                "project": "p1",
                "surface_origin": "cli",
                "action": "generate_document",
                "requested_capability": "document.generate",
                "template": {"title": "Scheduled", "body": "Body"},
            },
        )
        schedule = self.system["orchestrator"].create_schedule(
            schedule_id="s1",
            pattern_id="sched_doc",
            user_id="u1",
            surface="cli",
            interval_seconds=60,
            start_at_epoch=100,
            max_runs=1,
        )
        self.assertTrue(schedule["enabled"])

        tick_1 = self.system["orchestrator"].run_scheduler_tick(now_epoch=100)
        self.assertEqual(len(tick_1["executed"]), 1)
        self.assertEqual(tick_1["executed"][0]["status"], "executed")

        schedule_state = self.system["orchestrator"].list_schedules()["s1"]
        self.assertFalse(schedule_state["enabled"])
        self.assertEqual(schedule_state["runs_count"], 1)

        tick_2 = self.system["orchestrator"].run_scheduler_tick(now_epoch=200)
        self.assertEqual(len(tick_2["executed"]), 0)


if __name__ == "__main__":
    unittest.main()
