from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from core.plugin.trust import build_integrity_hash, sign_integrity


@dataclass(frozen=True)
class InternalPluginMetadata:
    plugin_id: str
    version: str
    capabilities: tuple[str, ...]
    deterministic: bool
    signer: str
    integrity: str
    signature: Any


def _mk(plugin_id: str, version: str, capabilities: tuple[str, ...], deterministic: bool, signer: str) -> InternalPluginMetadata:
    integrity = build_integrity_hash(
        kind="internal",
        plugin_id=plugin_id,
        version=version,
        capabilities=capabilities,
        deterministic=deterministic,
    )
    signature = sign_integrity(integrity=integrity, signer_key="core-team-dev-key", key_id="core-v1")
    return InternalPluginMetadata(
        plugin_id=plugin_id,
        version=version,
        capabilities=capabilities,
        deterministic=deterministic,
        signer=signer,
        integrity=integrity,
        signature=signature,
    )


INTERNAL_PLUGIN_METADATA: Dict[str, InternalPluginMetadata] = {
    "document.plugin.v1": _mk(
        plugin_id="document.plugin.v1",
        version="1.0.0",
        capabilities=("document.generate",),
        deterministic=True,
        signer="core-team",
    ),
    "presentation.plugin.v1": _mk(
        plugin_id="presentation.plugin.v1",
        version="1.0.0",
        capabilities=("presentation.generate",),
        deterministic=True,
        signer="core-team",
    ),
}
