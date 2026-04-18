from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from core.llm.factory import build_llm_provider
from core.memory.store import MemoryStore
from core.orchestrator.engine import Orchestrator
from core.orchestrator.policy import PolicyEngine
from core.plugin.manager import PluginManager
from core.plugin.registry import PluginRegistry
from core.runtime.executor import RuntimeExecutor


def load_environment(env_file: str) -> Dict[str, Any]:
    path = Path(env_file)
    if not path.exists():
        raise FileNotFoundError(f"Environment file not found: {env_file}")
    with path.open("r", encoding="utf-8-sig") as fp:
        return json.load(fp)


def boot_system(env_file: str) -> Dict[str, Any]:
    env = load_environment(env_file)
    data_dir = Path(env["data_dir"])
    data_dir.mkdir(parents=True, exist_ok=True)

    memory = MemoryStore(data_dir=data_dir)
    plugin_registry = PluginRegistry(allowed_capabilities=set(env["allowed_capabilities"]))
    plugin_manager = PluginManager(
        data_dir=data_dir,
        registry=plugin_registry,
        bootstrap_plugins=list(env.get("bootstrap_plugins", [])),
        trust_policy_config=(env.get("policy", {}) or {}).get("plugin_trust", {}),
        sandbox_policy_config=(env.get("policy", {}) or {}).get("program_sandbox", {}),
        external_program_registry_file=env.get("program_registry_file"),
    )
    plugin_manager.bootstrap_default_plugins()
    plugin_manager.sync_registry_from_installed()
    runtime = RuntimeExecutor()
    policy = PolicyEngine(config=env.get("policy", {}))
    llm_provider = build_llm_provider(env.get("llm", {}))
    orchestrator = Orchestrator(
        memory=memory,
        plugin_registry=plugin_registry,
        runtime=runtime,
        policy=policy,
        llm_provider=llm_provider,
    )

    return {
        "env": env,
        "memory": memory,
        "plugin_registry": plugin_registry,
        "plugin_manager": plugin_manager,
        "runtime": runtime,
        "policy": policy,
        "llm_provider": llm_provider,
        "orchestrator": orchestrator,
    }
