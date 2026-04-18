from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class ProgramSandboxPolicy:
    max_timeout_sec: int
    allow_real_execution: bool
    allowed_capabilities_for_real_execution: tuple[str, ...]

    @classmethod
    def from_config(cls, cfg: Dict[str, Any] | None) -> "ProgramSandboxPolicy":
        c = cfg or {}
        allowed = c.get("allowed_capabilities_for_real_execution", ["program.echo.execute"])
        if not isinstance(allowed, list):
            allowed = [str(allowed)]
        return cls(
            max_timeout_sec=int(c.get("max_timeout_sec", 30)),
            allow_real_execution=bool(c.get("allow_real_execution", True)),
            allowed_capabilities_for_real_execution=tuple(str(v) for v in allowed),
        )
