from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from core.bootstrap.loader import boot_system
from plugins.document_plugin import DocumentPlugin
from plugins.presentation_plugin import PresentationPlugin


class WorkflowAndPresentationTest(unittest.TestCase):
    def setUp(self) -> None:
        root = Path("E:/OS/.test_tmp")
        root.mkdir(parents=True, exist_ok=True)
        self.base = Path(tempfile.mkdtemp(prefix="wf_", dir=str(root)))
        self.env_path = self.base / "runtime.env.json"
        self.env_path.write_text(
            json.dumps(
                {
                    "system_name": "test-os",
                    "deterministic_mode": True,
                    "data_dir": str(self.base / ".runtime_data"),
                    "default_project": "demo-project",
                    "allowed_capabilities": ["document.generate", "presentation.generate"],
                }
            ),
            encoding="utf-8",
        )
        self.system = boot_system(str(self.env_path))
        self.system["plugin_registry"].register(DocumentPlugin())
        self.system["plugin_registry"].register(PresentationPlugin())

    def tearDown(self) -> None:
        shutil.rmtree(self.base, ignore_errors=True)

    def test_promote_and_run_procedural_pattern(self) -> None:
        self.system["orchestrator"].promote_to_procedural_memory(
            "doc_pattern",
            {
                "project": "p1",
                "surface_origin": "cli",
                "action": "generate_document",
                "requested_capability": "document.generate",
                "template": {"title": "Base", "body": "Base body"},
            },
        )

        result = self.system["orchestrator"].run_procedural_pattern(
            pattern_id="doc_pattern",
            user_id="u1",
            surface="cli",
            overrides={"title": "Overridden"},
        )
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["output"]["artifact"], "# Overridden\n\nBase body")

    def test_document_to_presentation_flow(self) -> None:
        doc_result = self.system["orchestrator"].execute_intent(
            {
                "user_id": "u2",
                "surface": "cli",
                "project": "p2",
                "action": "generate_document",
                "requested_capability": "document.generate",
                "payload": {"title": "Doc", "body": "Line A\nLine B\nLine C"},
            }
        )
        self.assertEqual(doc_result["status"], "completed")

        context = self.system["orchestrator"].retrieve_context(user_id="u2", project="p2")
        source_document = context["latest_run"]["output"]["artifact"]

        deck_result = self.system["orchestrator"].execute_intent(
            {
                "user_id": "u2",
                "surface": "cli",
                "project": "p2",
                "action": "generate_presentation",
                "requested_capability": "presentation.generate",
                "payload": {"title": "Deck", "source_document": source_document},
            }
        )
        self.assertEqual(deck_result["status"], "completed")
        self.assertEqual(deck_result["output"]["artifact_type"], "presentation_outline")
        self.assertGreaterEqual(len(deck_result["output"]["artifact"]["slides"]), 1)


if __name__ == "__main__":
    unittest.main()
