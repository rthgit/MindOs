from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class Intent:
    surface: str
    project: str
    action: str
    payload: Dict[str, Any]
    requested_capability: str


@dataclass(frozen=True)
class Plan:
    plan_id: str
    requested_capability: str
    plugin_id: str
    action: str
    payload: Dict[str, Any]


@dataclass(frozen=True)
class Event:
    sequence: int
    event_type: str
    correlation_id: str
    payload: Dict[str, Any]


@dataclass(frozen=True)
class RunResult:
    run_id: str
    status: str
    output: Dict[str, Any]
    plugin_id: str
    warnings: Optional[List[str]] = None
