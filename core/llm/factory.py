from __future__ import annotations

from typing import Any, Dict

from core.llm.base import LLMProvider
from core.llm.providers import LlamaCppProvider, MockProvider, OllamaProvider, OpenAICompatibleProvider


def _merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(base)
    out.update(override)
    return out


def _normalize_config(cfg: Dict[str, Any]) -> Dict[str, Any]:
    # Backward compatible:
    # - old flat config: {"enabled": true, "provider": "...", ...}
    # - new source-aware config:
    #   {
    #     "source": "env|api|local",
    #     "env": {...},
    #     "api": {...},
    #     "local": {...}
    #   }
    source = str(cfg.get("source", "env")).strip().lower()
    if source not in {"env", "api", "local"}:
        source = "env"

    if source == "env":
        env_cfg = cfg.get("env", {})
        if isinstance(env_cfg, dict) and env_cfg:
            merged = _merge(cfg, env_cfg)
            merged.pop("api", None)
            merged.pop("local", None)
            merged.pop("env", None)
            return merged
        return cfg

    if source == "api":
        api_cfg = cfg.get("api", {})
        if not isinstance(api_cfg, dict):
            api_cfg = {}
        merged = _merge(cfg, api_cfg)
        merged["enabled"] = bool(api_cfg.get("enabled", True))
        merged["provider"] = str(api_cfg.get("provider", "openai_compatible"))
        merged.pop("api", None)
        merged.pop("local", None)
        merged.pop("env", None)
        return merged

    # source == local
    local_cfg = cfg.get("local", {})
    if not isinstance(local_cfg, dict):
        local_cfg = {}
    merged = _merge(cfg, local_cfg)
    merged["enabled"] = bool(local_cfg.get("enabled", True))
    merged["provider"] = str(local_cfg.get("provider", "ollama"))
    merged.pop("api", None)
    merged.pop("local", None)
    merged.pop("env", None)
    return merged


def build_llm_provider(cfg: Dict[str, Any] | None) -> LLMProvider | None:
    c = _normalize_config(cfg or {})
    if not bool(c.get("enabled", False)):
        return None
    provider = str(c.get("provider", "mock")).strip().lower()
    model = str(c.get("model", "mock-v1"))
    timeout_sec = int(c.get("timeout_sec", 20))

    if provider == "mock":
        return MockProvider(model_name=model, fixed_response=str(c.get("mock_response", "advisory: proceed deterministically")))
    if provider == "ollama":
        return OllamaProvider(base_url=str(c.get("base_url", "http://127.0.0.1:11434")), model_name=model, timeout_sec=timeout_sec)
    if provider in {"llamacpp", "cpp"}:
        return LlamaCppProvider(base_url=str(c.get("base_url", "http://127.0.0.1:8080")), model_name=model, timeout_sec=timeout_sec)
    if provider in {"openai", "openai_compatible"}:
        return OpenAICompatibleProvider(
            base_url=str(c.get("base_url", "https://api.openai.com")),
            model_name=model,
            api_key_env=str(c.get("api_key_env", "OPENAI_API_KEY")),
            timeout_sec=timeout_sec,
        )
    raise ValueError(f"Unsupported LLM provider: {provider}")
