from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict
from typing import Any, Dict, List

from core.contracts import Intent, Plan, RunResult
from core.memory.store import MemoryStore
from core.orchestrator.policy import PolicyDecision, PolicyEngine
from core.plugin.registry import PluginRegistry
from core.runtime.executor import RuntimeExecutor


class Orchestrator:
    def __init__(
        self,
        memory: MemoryStore,
        plugin_registry: PluginRegistry,
        runtime: RuntimeExecutor,
        policy: PolicyEngine,
    ) -> None:
        self.memory = memory
        self.plugin_registry = plugin_registry
        self.runtime = runtime
        self.policy = policy

    def _hash(self, value: Dict[str, Any]) -> str:
        canonical = json.dumps(value, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def _capture(self, raw_intent: Dict[str, Any]) -> Dict[str, Any]:
        if "user_id" not in raw_intent:
            raw_intent["user_id"] = "local-user"
        return raw_intent

    def _normalize(self, captured: Dict[str, Any]) -> Intent:
        required = ["surface", "project", "action", "payload", "requested_capability"]
        missing = [k for k in required if k not in captured]
        if missing:
            raise ValueError(f"Missing intent keys: {missing}")
        return Intent(
            surface=str(captured["surface"]),
            project=str(captured["project"]),
            action=str(captured["action"]),
            payload=dict(captured["payload"]),
            requested_capability=str(captured["requested_capability"]),
        )

    def _link(self, intent: Intent, user_id: str) -> Dict[str, Any]:
        self.memory.bind_context(user_id=user_id, project=intent.project, surface=intent.surface)
        context = self.memory.get_context(user_id=user_id, project=intent.project)
        return {
            "user_id": user_id,
            "context": context,
            "intent": asdict(intent),
        }

    def _build_plan(self, intent: Intent) -> Plan:
        plugin = self.plugin_registry.resolve_by_capability(intent.requested_capability)
        plan_seed = {
            "capability": intent.requested_capability,
            "plugin_id": plugin.manifest.plugin_id,
            "action": intent.action,
            "payload": intent.payload,
        }
        plan_id = self._hash(plan_seed)[:16]
        return Plan(
            plan_id=plan_id,
            requested_capability=intent.requested_capability,
            plugin_id=plugin.manifest.plugin_id,
            action=intent.action,
            payload=intent.payload,
        )

    def _persist_pre_run(self, correlation_id: str, linked: Dict[str, Any], plan: Plan) -> None:
        self.memory.append_event("IntentAccepted", correlation_id, linked)
        self.memory.append_event("PlanCreated", correlation_id, asdict(plan))

    def _act(self, run_id: str, plan: Plan) -> RunResult:
        plugin = self.plugin_registry.resolve_by_capability(plan.requested_capability)
        return self.runtime.run_step(run_id=run_id, plan=plan, plugin=plugin)

    def _persist_post_run(self, sequence: int, user_id: str, project: str, correlation_id: str, result: RunResult) -> None:
        run_state = {
            "sequence": sequence,
            "user_id": user_id,
            "project": project,
            "run_id": result.run_id,
            "status": result.status,
            "plugin_id": result.plugin_id,
            "output": result.output,
        }
        self.memory.update_operational_run(result.run_id, run_state)
        self.memory.append_event("RunFinished", correlation_id, asdict(result))

        artifact = result.output.get("artifact")
        if artifact:
            semantic_key = f"{project}:latest_artifact"
            self.memory.upsert_semantic_fact(
                semantic_key,
                {"artifact": artifact, "run_id": result.run_id, "plugin_id": result.plugin_id},
            )

    def _audit(
        self,
        correlation_id: str,
        intent: Intent,
        plan: Plan,
        run_id: str,
        result: RunResult,
        policy_decision: PolicyDecision,
    ) -> None:
        self.memory.append_audit(
            "decision_trace",
            correlation_id,
            {
                "intent": asdict(intent),
                "plan": asdict(plan),
                "run_id": run_id,
                "result_status": result.status,
                "rollback_possible": True,
                "autonomy_level": policy_decision.autonomy_level,
                "confirmation_used": policy_decision.confirmation_used,
            },
        )

    def execute_intent(self, raw_intent: Dict[str, Any], require_confirmation: bool = False) -> Dict[str, Any]:
        captured = self._capture(dict(raw_intent))
        intent = self._normalize(captured)
        user_id = str(captured["user_id"])
        policy_decision = self.policy.evaluate(user_id=user_id, intent=intent, require_confirmation=require_confirmation)

        correlation_id = self._hash(
            {
                "user_id": user_id,
                "surface": intent.surface,
                "project": intent.project,
                "action": intent.action,
                "payload": intent.payload,
            }
        )[:20]
        linked = self._link(intent=intent, user_id=user_id)
        plan = self._build_plan(intent)
        self._persist_pre_run(correlation_id=correlation_id, linked=linked, plan=plan)

        run_id = f"run-{self.memory.next_sequence()}"
        self.memory.append_event("RunStarted", correlation_id, {"run_id": run_id, "plan_id": plan.plan_id})
        result = self._act(run_id=run_id, plan=plan)
        self._persist_post_run(
            sequence=self.memory.next_sequence(),
            user_id=user_id,
            project=intent.project,
            correlation_id=correlation_id,
            result=result,
        )
        self._audit(
            correlation_id=correlation_id,
            intent=intent,
            plan=plan,
            run_id=run_id,
            result=result,
            policy_decision=policy_decision,
        )

        return {
            "correlation_id": correlation_id,
            "plan_id": plan.plan_id,
            "run_id": run_id,
            "status": result.status,
            "output": result.output,
            "autonomy_level": policy_decision.autonomy_level,
        }

    def execute_workflow_document_to_presentation(
        self,
        *,
        user_id: str,
        surface: str,
        project: str,
        document_title: str,
        document_body: str,
        presentation_title: str,
    ) -> Dict[str, Any]:
        doc = self.execute_intent(
            {
                "user_id": user_id,
                "surface": surface,
                "project": project,
                "action": "generate_document",
                "requested_capability": "document.generate",
                "payload": {"title": document_title, "body": document_body},
            }
        )
        source_document = str(doc["output"]["artifact"])
        deck = self.execute_intent(
            {
                "user_id": user_id,
                "surface": surface,
                "project": project,
                "action": "generate_presentation",
                "requested_capability": "presentation.generate",
                "payload": {"title": presentation_title, "source_document": source_document},
            }
        )
        return {
            "workflow": "document_to_presentation",
            "document_run": doc,
            "presentation_run": deck,
            "status": "completed",
        }

    def retrieve_context(self, user_id: str, project: str) -> Dict[str, Any]:
        return self.memory.retrieve_cross_surface_context(user_id=user_id, project=project)

    def promote_to_procedural_memory(self, pattern_id: str, definition: Dict[str, Any]) -> None:
        self.memory.upsert_procedural_pattern(pattern_id=pattern_id, value=definition)

    def run_procedural_pattern(self, pattern_id: str, user_id: str, surface: str, overrides: Dict[str, Any] | None = None) -> Dict[str, Any]:
        pattern = self.memory.get_procedural_pattern(pattern_id)
        if not pattern:
            raise KeyError(f"Pattern not found: {pattern_id}")

        template = dict(pattern.get("template", {}))
        if overrides:
            template.update(overrides)

        raw_intent = {
            "user_id": user_id,
            "surface": surface,
            "project": pattern["project"],
            "action": pattern["action"],
            "requested_capability": pattern["requested_capability"],
            "payload": template,
        }
        return self.execute_intent(raw_intent)

    def create_schedule(
        self,
        *,
        schedule_id: str,
        pattern_id: str,
        user_id: str,
        surface: str,
        interval_seconds: int,
        start_at_epoch: int | None = None,
        max_runs: int | None = None,
    ) -> Dict[str, Any]:
        if interval_seconds <= 0:
            raise ValueError("interval_seconds must be > 0")
        pattern = self.memory.get_procedural_pattern(pattern_id)
        if not pattern:
            raise KeyError(f"Pattern not found: {pattern_id}")
        now = int(time.time())
        schedule = {
            "schedule_id": schedule_id,
            "pattern_id": pattern_id,
            "project": pattern["project"],
            "user_id": user_id,
            "surface": surface,
            "interval_seconds": int(interval_seconds),
            "next_run_epoch": int(start_at_epoch if start_at_epoch is not None else now),
            "last_run_epoch": None,
            "runs_count": 0,
            "max_runs": int(max_runs) if max_runs is not None else None,
            "enabled": True,
            "last_error": None,
        }
        self.memory.upsert_schedule(schedule_id, schedule)
        self.memory.append_audit("schedule_created", schedule_id, schedule)
        return schedule

    def list_schedules(self) -> Dict[str, Dict[str, Any]]:
        return self.memory.list_schedules()

    def run_scheduler_tick(self, now_epoch: int | None = None) -> Dict[str, Any]:
        now = int(now_epoch if now_epoch is not None else time.time())
        schedules = self.memory.list_schedules()
        executed: List[Dict[str, Any]] = []
        for schedule_id in sorted(schedules.keys()):
            schedule = schedules[schedule_id]
            if not schedule.get("enabled", False):
                continue
            if now < int(schedule.get("next_run_epoch", 0)):
                continue
            max_runs = schedule.get("max_runs")
            runs_count = int(schedule.get("runs_count", 0))
            if max_runs is not None and runs_count >= int(max_runs):
                schedule["enabled"] = False
                self.memory.upsert_schedule(schedule_id, schedule)
                continue
            try:
                run_out = self.run_procedural_pattern(
                    pattern_id=str(schedule["pattern_id"]),
                    user_id=str(schedule["user_id"]),
                    surface=str(schedule["surface"]),
                )
                schedule["runs_count"] = runs_count + 1
                schedule["last_run_epoch"] = now
                schedule["next_run_epoch"] = now + int(schedule["interval_seconds"])
                if max_runs is not None and schedule["runs_count"] >= int(max_runs):
                    schedule["enabled"] = False
                schedule["last_error"] = None
                self.memory.upsert_schedule(schedule_id, schedule)
                self.memory.append_audit(
                    "schedule_executed",
                    schedule_id,
                    {"schedule_id": schedule_id, "run_id": run_out["run_id"], "status": run_out["status"]},
                )
                executed.append({"schedule_id": schedule_id, "status": "executed", "run_id": run_out["run_id"]})
            except Exception as exc:
                schedule["last_error"] = str(exc)
                schedule["enabled"] = False
                self.memory.upsert_schedule(schedule_id, schedule)
                self.memory.append_audit(
                    "schedule_failed",
                    schedule_id,
                    {"schedule_id": schedule_id, "error": str(exc)},
                )
                executed.append({"schedule_id": schedule_id, "status": "failed", "error": str(exc)})
        return {"tick_epoch": now, "executed": executed}

    def resume_run(self, run_id: str) -> Dict[str, Any]:
        run = self.memory.get_operational_run(run_id)
        if not run:
            raise KeyError(f"Run not found: {run_id}")
        return {"run_id": run_id, "status": run["status"], "output": run["output"]}

    def rollback_internal(self, run_id: str) -> Dict[str, Any]:
        run = self.memory.get_operational_run(run_id)
        if not run:
            raise KeyError(f"Run not found: {run_id}")
        run["status"] = "rolled_back"
        self.memory.update_operational_run(run_id, run)
        self.memory.append_audit("rollback", run_id, {"run_id": run_id, "result": "rolled_back"})
        return {"run_id": run_id, "status": "rolled_back"}
