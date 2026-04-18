from __future__ import annotations

import json
import os
from typing import Any, Dict
from urllib.error import URLError
from urllib.request import Request, urlopen

from core.llm.base import LLMRequest, LLMResponse


class MockProvider:
    provider_name = "mock"

    def __init__(self, model_name: str = "mock-v1", fixed_response: str = "advisory: proceed deterministically") -> None:
        self.model_name = model_name
        self.fixed_response = fixed_response

    def generate(self, request: LLMRequest) -> LLMResponse:
        _ = request
        return LLMResponse(text=self.fixed_response, provider=self.provider_name, model=self.model_name)

    def health(self) -> dict:
        return {"ok": True, "provider": self.provider_name, "model": self.model_name}


class OllamaProvider:
    provider_name = "ollama"

    def __init__(self, base_url: str, model_name: str, timeout_sec: int = 20) -> None:
        self.base_url = base_url.rstrip("/")
        self.model_name = model_name
        self.timeout_sec = timeout_sec

    def _post_json(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        req = Request(
            url=f"{self.base_url}{path}",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(req, timeout=self.timeout_sec) as resp:
            body = resp.read().decode("utf-8")
        return json.loads(body)

    def generate(self, request: LLMRequest) -> LLMResponse:
        out = self._post_json(
            "/api/generate",
            {
                "model": self.model_name,
                "prompt": request.prompt,
                "stream": False,
                "options": {
                    "temperature": request.temperature,
                    "num_predict": request.max_tokens,
                },
            },
        )
        text = str(out.get("response", ""))
        return LLMResponse(text=text, provider=self.provider_name, model=self.model_name)

    def health(self) -> dict:
        try:
            req = Request(url=f"{self.base_url}/api/tags", method="GET")
            with urlopen(req, timeout=self.timeout_sec) as resp:
                body = resp.read().decode("utf-8")
            data = json.loads(body)
            return {"ok": True, "provider": self.provider_name, "model": self.model_name, "models": data.get("models", [])}
        except Exception as exc:
            return {"ok": False, "provider": self.provider_name, "model": self.model_name, "error": str(exc)}


class LlamaCppProvider:
    provider_name = "llamacpp"

    def __init__(self, base_url: str, model_name: str, timeout_sec: int = 20) -> None:
        self.base_url = base_url.rstrip("/")
        self.model_name = model_name
        self.timeout_sec = timeout_sec

    def _post_json(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        req = Request(
            url=f"{self.base_url}{path}",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(req, timeout=self.timeout_sec) as resp:
            body = resp.read().decode("utf-8")
        return json.loads(body)

    def generate(self, request: LLMRequest) -> LLMResponse:
        out = self._post_json(
            "/completion",
            {
                "prompt": request.prompt,
                "temperature": request.temperature,
                "n_predict": request.max_tokens,
            },
        )
        text = str(out.get("content", ""))
        return LLMResponse(text=text, provider=self.provider_name, model=self.model_name)

    def health(self) -> dict:
        try:
            req = Request(url=f"{self.base_url}/health", method="GET")
            with urlopen(req, timeout=self.timeout_sec) as resp:
                _ = resp.read().decode("utf-8")
            return {"ok": True, "provider": self.provider_name, "model": self.model_name}
        except Exception as exc:
            return {"ok": False, "provider": self.provider_name, "model": self.model_name, "error": str(exc)}


class OpenAICompatibleProvider:
    provider_name = "openai_compatible"

    def __init__(self, base_url: str, model_name: str, api_key_env: str, timeout_sec: int = 20) -> None:
        self.base_url = base_url.rstrip("/")
        self.model_name = model_name
        self.api_key_env = api_key_env
        self.timeout_sec = timeout_sec

    def _api_key(self) -> str:
        key = os.environ.get(self.api_key_env, "")
        if not key:
            raise PermissionError(f"Missing API key in env var: {self.api_key_env}")
        return key

    def generate(self, request: LLMRequest) -> LLMResponse:
        req = Request(
            url=f"{self.base_url}/v1/chat/completions",
            data=json.dumps(
                {
                    "model": self.model_name,
                    "messages": [{"role": "user", "content": request.prompt}],
                    "temperature": request.temperature,
                    "max_tokens": request.max_tokens,
                }
            ).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._api_key()}",
            },
            method="POST",
        )
        with urlopen(req, timeout=self.timeout_sec) as resp:
            body = resp.read().decode("utf-8")
        out = json.loads(body)
        choices = out.get("choices", [])
        text = ""
        if choices:
            text = str(((choices[0] or {}).get("message") or {}).get("content", ""))
        return LLMResponse(text=text, provider=self.provider_name, model=self.model_name)

    def health(self) -> dict:
        try:
            req = Request(
                url=f"{self.base_url}/v1/models",
                headers={"Authorization": f"Bearer {self._api_key()}"},
                method="GET",
            )
            with urlopen(req, timeout=self.timeout_sec) as resp:
                _ = resp.read().decode("utf-8")
            return {"ok": True, "provider": self.provider_name, "model": self.model_name}
        except Exception as exc:
            return {"ok": False, "provider": self.provider_name, "model": self.model_name, "error": str(exc)}
