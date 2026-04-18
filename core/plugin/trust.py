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


def sign_integrity(*, integrity: str, signer_key: str, key_id: str = "default") -> Dict[str, str]:
    message = f"{key_id}:{integrity}"
    sig = hmac.new(signer_key.encode("utf-8"), message.encode("utf-8"), hashlib.sha256).hexdigest()
    return {"alg": "hmac-sha256-v1", "key_id": key_id, "sig": sig}


@dataclass(frozen=True)
class TrustPolicy:
    require_integrity: bool
    trusted_signers: tuple[str, ...]
    revoked_signers: tuple[str, ...]
    require_signature: bool
    signer_keys: Dict[str, Any]
    revoked_key_ids: tuple[str, ...]

    @classmethod
    def from_config(cls, cfg: Dict[str, Any] | None) -> "TrustPolicy":
        c = cfg or {}
        signers = c.get("trusted_signers", ["core-team"])
        if not isinstance(signers, list):
            signers = [str(signers)]
        revoked = c.get("revoked_signers", [])
        if not isinstance(revoked, list):
            revoked = [str(revoked)]
        signer_keys_raw = c.get("signer_keys", {"core-team": {"core-v1": "core-team-dev-key"}})
        if not isinstance(signer_keys_raw, dict):
            signer_keys_raw = {"core-team": {"core-v1": "core-team-dev-key"}}
        signer_keys: Dict[str, Any] = {}
        for signer, val in signer_keys_raw.items():
            if isinstance(val, dict):
                signer_keys[str(signer)] = {str(k): str(v) for k, v in val.items()}
            else:
                signer_keys[str(signer)] = str(val)
        revoked_key_ids_raw = c.get("revoked_key_ids", [])
        if not isinstance(revoked_key_ids_raw, list):
            revoked_key_ids_raw = [str(revoked_key_ids_raw)]
        return cls(
            require_integrity=bool(c.get("require_integrity", True)),
            trusted_signers=tuple(str(s) for s in signers),
            revoked_signers=tuple(str(s) for s in revoked),
            require_signature=bool(c.get("require_signature", True)),
            signer_keys=signer_keys,
            revoked_key_ids=tuple(str(v) for v in revoked_key_ids_raw),
        )

    def _resolve_signer_key(self, signer: str, key_id: str) -> str | None:
        raw = self.signer_keys.get(signer)
        if raw is None:
            return None
        if isinstance(raw, str):
            return raw if key_id in {"default", "legacy"} else None
        if isinstance(raw, dict):
            key = raw.get(key_id)
            if key is not None:
                return str(key)
            return None
        return None

    def assert_trusted(
        self,
        *,
        plugin_id: str,
        signer: str,
        expected_integrity: str,
        actual_integrity: str,
        signature: Any = None,
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
            key_id = "legacy"
            sig_value: str | None = None
            if isinstance(signature, dict):
                alg = str(signature.get("alg", ""))
                if alg != "hmac-sha256-v1":
                    raise PermissionError(f"Unsupported signature algorithm for plugin {plugin_id}: {alg}")
                key_id = str(signature.get("key_id", ""))
                sig_value = str(signature.get("sig", ""))
            elif isinstance(signature, str):
                sig_value = signature
                key_id = "legacy"
            else:
                sig_value = None

            if f"{signer}:{key_id}" in self.revoked_key_ids:
                raise PermissionError(f"Revoked signer key for plugin {plugin_id}: {signer}:{key_id}")

            key = self._resolve_signer_key(signer, key_id)
            if not key:
                raise PermissionError(f"Missing signer key for plugin {plugin_id}: signer={signer}, key_id={key_id}")
            expected_sig = sign_integrity(integrity=expected_integrity, signer_key=key, key_id=key_id)["sig"]
            if sig_value != expected_sig:
                raise PermissionError(
                    f"Signature mismatch for plugin {plugin_id}: signer={signer}, expected_sig={expected_sig}, got={sig_value}"
                )
