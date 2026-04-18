from __future__ import annotations

import hmac
import hashlib
import json
from dataclasses import dataclass
from typing import Any, Dict, Iterable


def build_integrity_payload(
    *,
    kind: str,
    plugin_id: str,
    version: str,
    capabilities: Iterable[str],
    deterministic: bool,
    platform_commands: Dict[str, list[str]] | None = None,
) -> str:
    payload = {
        "kind": kind,
        "plugin_id": plugin_id,
        "version": version,
        "capabilities": sorted([str(c) for c in capabilities]),
        "deterministic": bool(deterministic),
        "platform_commands": platform_commands or {},
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def build_integrity_hash(
    *,
    kind: str,
    plugin_id: str,
    version: str,
    capabilities: Iterable[str],
    deterministic: bool,
    platform_commands: Dict[str, list[str]] | None = None,
) -> str:
    payload = build_integrity_payload(
        kind=kind,
        plugin_id=plugin_id,
        version=version,
        capabilities=capabilities,
        deterministic=deterministic,
        platform_commands=platform_commands,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def sign_integrity(*, integrity: str, signer_key: str) -> str:
    return hmac.new(signer_key.encode("utf-8"), integrity.encode("utf-8"), hashlib.sha256).hexdigest()


@dataclass(frozen=True)
class TrustPolicy:
    require_integrity: bool
    trusted_signers: tuple[str, ...]
    revoked_signers: tuple[str, ...]
    require_signature: bool
    signer_keys: Dict[str, str]

    @classmethod
    def from_config(cls, cfg: Dict[str, Any] | None) -> "TrustPolicy":
        c = cfg or {}
        signers = c.get("trusted_signers", ["core-team"])
        if not isinstance(signers, list):
            signers = [str(signers)]
        revoked = c.get("revoked_signers", [])
        if not isinstance(revoked, list):
            revoked = [str(revoked)]
        signer_keys_raw = c.get("signer_keys", {"core-team": "core-team-dev-key"})
        if not isinstance(signer_keys_raw, dict):
            signer_keys_raw = {"core-team": "core-team-dev-key"}
        signer_keys = {str(k): str(v) for k, v in signer_keys_raw.items()}
        return cls(
            require_integrity=bool(c.get("require_integrity", True)),
            trusted_signers=tuple(str(s) for s in signers),
            revoked_signers=tuple(str(s) for s in revoked),
            require_signature=bool(c.get("require_signature", True)),
            signer_keys=signer_keys,
        )

    def assert_trusted(
        self,
        *,
        plugin_id: str,
        signer: str,
        expected_integrity: str,
        actual_integrity: str,
        signature: str | None = None,
    ) -> None:
        if signer in self.revoked_signers:
            raise PermissionError(f"Revoked signer for plugin {plugin_id}: {signer}")
        if signer not in self.trusted_signers:
            raise PermissionError(f"Untrusted signer for plugin {plugin_id}: {signer}")
        if self.require_integrity and expected_integrity != actual_integrity:
            raise PermissionError(
                f"Integrity mismatch for plugin {plugin_id}: expected={expected_integrity}, actual={actual_integrity}"
            )
        if self.require_signature:
            key = self.signer_keys.get(signer)
            if not key:
                raise PermissionError(f"Missing signer key for plugin {plugin_id}: signer={signer}")
            expected_sig = sign_integrity(integrity=expected_integrity, signer_key=key)
            if signature != expected_sig:
                raise PermissionError(
                    f"Signature mismatch for plugin {plugin_id}: signer={signer}, expected_sig={expected_sig}, got={signature}"
                )
