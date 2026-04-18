from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class LLMRequest:
    prompt: str
    temperature: float = 0.0
    max_tokens: int = 256


@dataclass(frozen=True)
class LLMResponse:
    text: str
    provider: str
    model: str


class LLMProvider(Protocol):
    provider_name: str
    model_name: str

    def generate(self, request: LLMRequest) -> LLMResponse:
        ...

    def health(self) -> dict:
        ...
