from __future__ import annotations

import json
import unittest
from pathlib import Path


class ContractsAndStructureTest(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path("E:/OS")

    def test_required_paths_exist(self) -> None:
        required = [
            "runtime.env.json",
            "core/orchestrator/engine.py",
            "core/memory/store.py",
            "core/plugin/registry.py",
            "surfaces/cli/main.py",
            "surfaces/desktop/shell.py",
            "surfaces/ide/view.py",
            "docs/contracts/interfaces.md",
            "docs/contracts/events.md",
        ]
        for rel in required:
            self.assertTrue((self.repo_root / rel).exists(), f"Missing required path: {rel}")

    def test_runtime_env_contract(self) -> None:
        env = json.loads((self.repo_root / "runtime.env.json").read_text(encoding="utf-8"))
        self.assertTrue(env.get("deterministic_mode") is True)
        self.assertTrue(isinstance(env.get("allowed_capabilities"), list))
        self.assertGreaterEqual(len(env.get("allowed_capabilities")), 1)
        self.assertTrue(isinstance(env.get("policy"), dict))
        self.assertTrue(isinstance(env["policy"].get("acl"), dict))
        self.assertTrue(isinstance(env["policy"]["acl"].get("users"), dict))
        self.assertTrue(isinstance(env["policy"].get("plugin_trust"), dict))
        self.assertTrue(env["policy"]["plugin_trust"].get("require_signature") is True)
        self.assertTrue(isinstance(env["policy"]["plugin_trust"].get("signer_keys"), dict))

    def test_events_contract_contains_required_events(self) -> None:
        text = (self.repo_root / "docs/contracts/events.md").read_text(encoding="utf-8")
        for ev in ("IntentAccepted", "PlanCreated", "RunStarted", "RunFinished"):
            self.assertIn(ev, text)


if __name__ == "__main__":
    unittest.main()
