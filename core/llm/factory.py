from __future__ import annotations

from typing import Any, Dict

from core.llm.base import LLMProvider
from core.llm.providers import LlamaCppProvider, MockProvider, OllamaProvider, OpenAICompatibleProvider


def build_llm_provider(cfg: Dict[str, Any] | None) -> LLMProvider | None:
    c = cfg or {}
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
