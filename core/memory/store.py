from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class MemoryStore:
    """
    Memoria multi-livello senza separazione artificiale tra software e memoria:
    ogni transizione operativa rilevante viene persistita e collegata.
    """

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.events_file = self.data_dir / "episodic_events.jsonl"
        self.operational_file = self.data_dir / "operational_state.json"
        self.context_file = self.data_dir / "active_context.json"
        self.semantic_file = self.data_dir / "semantic_memory.json"
        self.procedural_file = self.data_dir / "procedural_memory.json"
        self.scheduler_file = self.data_dir / "scheduler_state.json"
        self.audit_file = self.data_dir / "audit_log.jsonl"
        self._ensure_files()

    def _ensure_files(self) -> None:
        for p, default in (
            (self.operational_file, {}),
            (self.context_file, {}),
            (self.semantic_file, {}),
            (self.procedural_file, {}),
            (self.scheduler_file, {}),
        ):
            if not p.exists():
                p.write_text(json.dumps(default, indent=2), encoding="utf-8")
        for p in (self.events_file, self.audit_file):
            if not p.exists():
                p.write_text("", encoding="utf-8")

    def _read_json(self, path: Path) -> Dict[str, Any]:
        text = path.read_text(encoding="utf-8").strip()
        if not text:
            return {}
        return json.loads(text)

    def _write_json(self, path: Path, value: Dict[str, Any]) -> None:
        path.write_text(json.dumps(value, indent=2, sort_keys=True), encoding="utf-8")

    def next_sequence(self) -> int:
        if not self.events_file.exists():
            return 1
        count = 0
        with self.events_file.open("r", encoding="utf-8") as fp:
            for line in fp:
                if line.strip():
                    count += 1
        return count + 1

    def append_event(self, event_type: str, correlation_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        event = {
            "sequence": self.next_sequence(),
            "event_type": event_type,
            "correlation_id": correlation_id,
            "payload": payload,
        }
        with self.events_file.open("a", encoding="utf-8") as fp:
            fp.write(json.dumps(event, sort_keys=True) + "\n")
        return event

    def append_audit(self, record_type: str, correlation_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        record = {
            "record_type": record_type,
            "correlation_id": correlation_id,
            "payload": payload,
        }
        with self.audit_file.open("a", encoding="utf-8") as fp:
            fp.write(json.dumps(record, sort_keys=True) + "\n")
        return record

    def update_operational_run(self, run_id: str, run_state: Dict[str, Any]) -> None:
        data = self._read_json(self.operational_file)
        data.setdefault("runs", {})
        data["runs"][run_id] = run_state
        self._write_json(self.operational_file, data)

    def get_operational_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        data = self._read_json(self.operational_file)
        return data.get("runs", {}).get(run_id)

    def bind_context(self, user_id: str, project: str, surface: str, extra: Optional[Dict[str, Any]] = None) -> None:
        data = self._read_json(self.context_file)
        data.setdefault(user_id, {})
        data[user_id][project] = {
            "surface": surface,
            "extra": extra or {},
        }
        self._write_json(self.context_file, data)

    def get_context(self, user_id: str, project: str) -> Dict[str, Any]:
        data = self._read_json(self.context_file)
        return data.get(user_id, {}).get(project, {})

    def upsert_semantic_fact(self, key: str, value: Dict[str, Any]) -> None:
        data = self._read_json(self.semantic_file)
        data[key] = value
        self._write_json(self.semantic_file, data)

    def get_semantic_fact(self, key: str) -> Optional[Dict[str, Any]]:
        data = self._read_json(self.semantic_file)
        return data.get(key)

    def upsert_procedural_pattern(self, pattern_id: str, value: Dict[str, Any]) -> None:
        data = self._read_json(self.procedural_file)
        data[pattern_id] = value
        self._write_json(self.procedural_file, data)

    def get_procedural_pattern(self, pattern_id: str) -> Optional[Dict[str, Any]]:
        data = self._read_json(self.procedural_file)
        return data.get(pattern_id)

    def upsert_schedule(self, schedule_id: str, value: Dict[str, Any]) -> None:
        data = self._read_json(self.scheduler_file)
        data[schedule_id] = value
        self._write_json(self.scheduler_file, data)

    def get_schedule(self, schedule_id: str) -> Optional[Dict[str, Any]]:
        data = self._read_json(self.scheduler_file)
        return data.get(schedule_id)

    def list_schedules(self) -> Dict[str, Dict[str, Any]]:
        return self._read_json(self.scheduler_file)

    def list_events(self, correlation_id: Optional[str] = None) -> List[Dict[str, Any]]:
        events: List[Dict[str, Any]] = []
        with self.events_file.open("r", encoding="utf-8") as fp:
            for line in fp:
                if not line.strip():
                    continue
                event = json.loads(line)
                if correlation_id and event["correlation_id"] != correlation_id:
                    continue
                events.append(event)
        return events

    def retrieve_cross_surface_context(self, user_id: str, project: str) -> Dict[str, Any]:
        context = self.get_context(user_id, project)
        operational = self._read_json(self.operational_file)
        latest_run = None
        for run in operational.get("runs", {}).values():
            if run.get("project") == project and run.get("user_id") == user_id:
                if latest_run is None or run.get("sequence", 0) > latest_run.get("sequence", 0):
                    latest_run = run
        return {
            "context": context,
            "latest_run": latest_run,
        }
