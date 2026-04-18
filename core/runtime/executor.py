from __future__ import annotations

from typing import Dict

from core.contracts import Plan, RunResult
from core.plugin.sdk import Plugin


class RuntimeExecutor:
    def run_step(self, run_id: str, plan: Plan, plugin: Plugin) -> RunResult:
        output = plugin.execute(plan.action, plan.payload)
        return RunResult(
            run_id=run_id,
            status="completed",
            output=output,
            plugin_id=plugin.manifest.plugin_id,
            warnings=[],
        )
