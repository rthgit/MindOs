from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional

from core.contracts import Intent


@dataclass(frozen=True)
class PolicyDecision:
    autonomy_level: str
    confirmation_used: bool


class PolicyEngine:
    def __init__(self, config: Dict[str, Any] | None = None) -> None:
        cfg = config or {}
        self.blocked_actions = set(self._to_list(cfg.get("blocked_actions")))
        self.confirm_required_actions = set(
            self._to_list(cfg.get("confirm_required_actions", ["delete", "destructive_write"]))
        )
        self.confirm_required_capabilities = set(self._to_list(cfg.get("confirm_required_capabilities")))
        self.acl = cfg.get("acl", {}) if isinstance(cfg.get("acl", {}), dict) else {}

    def _to_list(self, value: Any) -> Iterable[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(v) for v in value]
        return [str(value)]

    def _get_acl_for_user(self, user_id: str) -> Dict[str, Any]:
        users = self.acl.get("users", {}) if isinstance(self.acl.get("users", {}), dict) else {}
        user_rule = users.get(user_id)
        if isinstance(user_rule, dict):
            return user_rule
        default_rule = users.get("default", {})
        if isinstance(default_rule, dict):
            return default_rule
        return {}

    def _is_allowed_by_acl(self, user_id: str, intent: Intent) -> Optional[str]:
        acl = self._get_acl_for_user(user_id)
        allowed_capabilities = set(self._to_list(acl.get("allowed_capabilities")))
        denied_capabilities = set(self._to_list(acl.get("denied_capabilities")))
        allowed_surfaces = set(self._to_list(acl.get("allowed_surfaces")))

        if allowed_capabilities and intent.requested_capability not in allowed_capabilities:
            return f"Capability not allowed by ACL: user={user_id}, capability={intent.requested_capability}"
        if intent.requested_capability in denied_capabilities:
            return f"Capability denied by ACL: user={user_id}, capability={intent.requested_capability}"
        if allowed_surfaces and intent.surface not in allowed_surfaces:
            return f"Surface not allowed by ACL: user={user_id}, surface={intent.surface}"
        return None

    def evaluate(self, user_id: str, intent: Intent, require_confirmation: bool) -> PolicyDecision:
        if intent.action in self.blocked_actions:
            raise PermissionError(f"Action blocked by policy: {intent.action}")
        acl_error = self._is_allowed_by_acl(user_id=user_id, intent=intent)
        if acl_error:
            raise PermissionError(acl_error)

        needs_confirmation = (
            intent.action in self.confirm_required_actions
            or intent.requested_capability in self.confirm_required_capabilities
        )
        if needs_confirmation and not require_confirmation:
            raise PermissionError(
                f"Action requires explicit confirmation: action={intent.action}, capability={intent.requested_capability}"
            )

        return PolicyDecision(
            autonomy_level="confirm_required" if needs_confirmation else "automatic",
            confirmation_used=require_confirmation,
        )
