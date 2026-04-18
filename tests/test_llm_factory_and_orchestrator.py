from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from core.bootstrap.loader import boot_system


class LLMFactoryAndOrchestratorTest(unittest.TestCase):
    def setUp(self) -> None:
        root = Path("E:/OS/.test_tmp")
        root.mkdir(parents=True, exist_ok=True)
        self.base = Path(tempfile.mkdtemp(prefix="llm_", dir=str(root)))
        self.env_path = self.base / "runtime.env.json"
        self.env_path.write_text(
            json.dumps(
                {
                    "system_name": "MindOs-test",
                    "deterministic_mode": True,
                    "data_dir": str(self.base / ".runtime_data"),
                    "default_project": "demo-project",
                    "allowed_capabilities": ["document.generate", "presentation.generate", "program.echo.execute"],
                    "bootstrap_plugins": ["document.plugin.v1", "presentation.plugin.v1"],
                    "llm": {
                        "enabled": True,
                        "provider": "mock",
                        "model": "mock-v1",
                        "mock_response": "advisory: mock path",
                    },
                    "program_registry_file": "",
                    "policy": {
                        "blocked_actions": [],
                        "confirm_required_actions": ["delete", "destructive_write"],
                        "confirm_required_capabilities": [],
                        "acl": {
                            "users": {
                                "default": {
                                    "allowed_capabilities": ["document.generate", "presentation.generate", "program.echo.execute"],
                                    "denied_capabilities": [],
                                    "allowed_surfaces": ["cli", "ide", "desktop"],
                                }
                            }
                        },
                        "plugin_trust": {
                            "require_integrity": True,
                            "require_signature": True,
                            "trusted_signers": ["core-team"],
                            "revoked_signers": [],
                            "revoked_key_ids": [],
                            "signer_keys": {"core-team": {"core-v1": "core-team-dev-key"}},
                        },
                        "program_sandbox": {
                            "max_timeout_sec": 30,
                            "allow_real_execution": True,
                            "allowed_capabilities_for_real_execution": ["program.echo.execute"],
                        },
                    },
                }
            ),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.base, ignore_errors=True)

    def test_mock_llm_provider_is_initialized(self) -> None:
        system = boot_system(str(self.env_path))
        provider = system.get("llm_provider")
        self.assertIsNotNone(provider)
        health = provider.health()
        self.assertTrue(health["ok"])
        self.assertEqual(health["provider"], "mock")

    def test_orchestrator_emits_llm_advisory(self) -> None:
        system = boot_system(str(self.env_path))
        result = system["orchestrator"].execute_intent(
            {
                "user_id": "u1",
                "surface": "cli",
                "project": "p1",
                "action": "generate_document",
                "requested_capability": "document.generate",
                "payload": {"title": "X", "body": "Y"},
            }
        )
        self.assertEqual(result["status"], "completed")
        self.assertIsNotNone(result.get("llm_advisory"))
        self.assertEqual(result["llm_advisory"]["provider"], "mock")
        self.assertTrue(result["llm_advisory"]["prompt_hash"])
        self.assertTrue(result["llm_advisory"]["response_hash"])


if __name__ == "__main__":
    unittest.main()
