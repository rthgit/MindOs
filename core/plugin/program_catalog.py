from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple
from urllib.request import urlopen

from core.plugin.trust import build_integrity_hash, sign_integrity


@dataclass(frozen=True)
class ProgramSpec:
    plugin_id: str
    version: str
    capabilities: tuple[str, ...]
    command_by_platform: Dict[str, List[str]]
    install_by_platform: Dict[str, List[str]]
    signer: str
    integrity: str
    signature: Any
    deterministic: bool = True


def _mk(
    *,
    plugin_id: str,
    version: str,
    capabilities: tuple[str, ...],
    command_by_platform: Dict[str, List[str]],
    install_by_platform: Dict[str, List[str]],
    signer: str,
    deterministic: bool = True,
) -> ProgramSpec:
    integrity = build_integrity_hash(
        kind="program",
        plugin_id=plugin_id,
        version=version,
        capabilities=capabilities,
        deterministic=deterministic,
        platform_commands=command_by_platform,
    )
    signature = sign_integrity(integrity=integrity, signer_key="core-team-dev-key", key_id="core-v1")
    return ProgramSpec(
        plugin_id=plugin_id,
        version=version,
        capabilities=capabilities,
        command_by_platform=command_by_platform,
        install_by_platform=install_by_platform,
        signer=signer,
        integrity=integrity,
        signature=signature,
        deterministic=deterministic,
    )


BUILTIN_PROGRAM_CATALOG: Dict[str, ProgramSpec] = {
    "shell.echo.program.v1": _mk(
        plugin_id="shell.echo.program.v1",
        version="1.0.0",
        capabilities=("program.echo.execute",),
        command_by_platform={
            "windows": ["powershell", "-NoProfile", "-Command", "Write-Output"],
            "linux": ["/bin/echo"],
        },
        install_by_platform={},
        signer="core-team",
        deterministic=True,
    ),
    "python.runner.program.v1": _mk(
        plugin_id="python.runner.program.v1",
        version="1.0.0",
        capabilities=("program.python.execute",),
        command_by_platform={
            "windows": ["python"],
            "linux": ["python3"],
        },
        install_by_platform={
            "windows": ["winget", "install", "-e", "--id", "Python.Python.3.12"],
            "linux": ["sudo", "apt-get", "install", "-y", "python3"],
        },
        signer="core-team",
        deterministic=True,
    ),
}


def _spec_from_row(row: dict) -> ProgramSpec:
    plugin_id = str(row["plugin_id"])
    version = str(row["version"])
    capabilities = tuple(str(c) for c in row["capabilities"])
    deterministic = bool(row.get("deterministic", True))
    command_by_platform = {str(k): [str(v) for v in vals] for k, vals in row["command_by_platform"].items()}
    install_by_platform = {str(k): [str(v) for v in vals] for k, vals in row.get("install_by_platform", {}).items()}
    signer = str(row.get("signer", "unknown"))
    integrity = str(row.get("integrity", ""))
    signature = row.get("signature", "")
    return ProgramSpec(
        plugin_id=plugin_id,
        version=version,
        capabilities=capabilities,
        command_by_platform=command_by_platform,
        install_by_platform=install_by_platform,
        signer=signer,
        integrity=integrity,
        signature=signature,
        deterministic=deterministic,
    )


def _read_registry_text(path: str) -> str:
    text = ""
    if path.startswith("http://") or path.startswith("https://"):
        with urlopen(path, timeout=10) as resp:
            text = resp.read().decode("utf-8").strip()
    elif path.startswith("file://"):
        p = Path(path.replace("file://", "", 1))
        if not p.exists():
            return ""
        text = p.read_text(encoding="utf-8").strip()
    else:
        p = Path(path)
        if not p.exists():
            return ""
        text = p.read_text(encoding="utf-8").strip()
    return text


def build_registry_integrity(program_rows: List[dict]) -> str:
    canonical_rows = sorted(program_rows, key=lambda r: str(r.get("plugin_id", "")))
    canonical = json.dumps(canonical_rows, sort_keys=True, separators=(",", ":"))
    return build_integrity_hash(
        kind="program-registry",
        plugin_id="external-registry",
        version="v1",
        capabilities=[canonical],
        deterministic=True,
    )


def load_external_program_catalog(path: str | None) -> Tuple[Dict[str, ProgramSpec], Dict[str, Any] | None]:
    if not path:
        return {}, None
    text = _read_registry_text(path)
    if not text:
        return {}, None
    payload = json.loads(text)
    rows: List[dict]
    metadata: Dict[str, Any] | None = None
    if isinstance(payload, list):
        rows = [r for r in payload if isinstance(r, dict)]
        metadata = {
            "mode": "legacy-list",
            "programs_integrity": build_registry_integrity(rows),
            "signer": "",
            "signature": None,
            "issued_at_epoch": int(time.time()),
            "expires_at_epoch": None,
        }
    elif isinstance(payload, dict):
        raw_rows = payload.get("programs", [])
        if not isinstance(raw_rows, list):
            raise ValueError("External program registry envelope must contain a 'programs' array")
        rows = [r for r in raw_rows if isinstance(r, dict)]
        metadata = dict(payload.get("meta", {}))
        metadata["mode"] = "signed-envelope"
        metadata["programs_integrity"] = build_registry_integrity(rows)
    else:
        raise ValueError("External program registry must be JSON array or signed envelope object")

    out: Dict[str, ProgramSpec] = {}
    for row in rows:
        spec = _spec_from_row(row)
        out[spec.plugin_id] = spec
    return out, metadata


def merge_program_catalog(external_registry_file: str | None = None) -> Tuple[Dict[str, ProgramSpec], Dict[str, Any] | None]:
    merged = dict(BUILTIN_PROGRAM_CATALOG)
    external, metadata = load_external_program_catalog(external_registry_file)
    merged.update(external)
    return merged, metadata


def available_programs(external_registry_file: str | None = None) -> list[str]:
    merged, _ = merge_program_catalog(external_registry_file)
    return sorted(merged.keys())
