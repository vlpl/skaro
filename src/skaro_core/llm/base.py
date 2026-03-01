"""Base LLM adapter interface and factory."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncIterator

from skaro_core.config import LLMConfig


class LLMError(Exception):
    """Raised when LLM API call fails."""

    def __init__(self, message: str, provider: str = "", retriable: bool = False):
        self.provider = provider
        self.retriable = retriable
        super().__init__(message)


@dataclass
class LLMMessage:
    role: str  # "system" | "user" | "assistant"
    content: str


@dataclass
class LLMResponse:
    content: str
    model: str
    usage: dict[str, int] | None = None


class BaseLLMAdapter(ABC):
    """Abstract interface for LLM providers."""

    def __init__(self, config: LLMConfig):
        self.config = config
        self.last_usage: dict[str, int] | None = None

    @abstractmethod
    async def complete(self, messages: list[LLMMessage]) -> LLMResponse:
        ...

    @abstractmethod
    async def stream(self, messages: list[LLMMessage]) -> AsyncIterator[str]:
        ...

    def _validate_api_key(self) -> None:
        if not self.config.api_key:
            from skaro_core.llm.base import PROVIDER_PRESETS
            preset = PROVIDER_PRESETS.get(self.config.provider)
            env_hint = f" or set env variable: {preset[1]}" if preset and preset[1] else ""
            raise ValueError(
                f"API key not found for {self.config.provider}. "
                f"Enter it in Settings{env_hint}"
            )


# (default_model, default_api_key_env, needs_key)
PROVIDER_PRESETS: dict[str, tuple[str, str, bool]] = {
    "anthropic": ("claude-sonnet-4-6", "ANTHROPIC_API_KEY", True),
    "openai": ("gpt-5.2", "OPENAI_API_KEY", True),
    "groq": ("llama-3.3-70b-versatile", "GROQ_API_KEY", True),
    "ollama": ("llama3.1", "", False),
}


def create_llm_adapter(config: LLMConfig) -> BaseLLMAdapter:
    """Factory: create adapter based on provider name."""
    provider = config.provider.lower()

    if provider == "anthropic":
        from skaro_core.llm.anthropic_adapter import AnthropicAdapter
        return AnthropicAdapter(config)
    elif provider == "openai":
        from skaro_core.llm.openai_adapter import OpenAIAdapter
        return OpenAIAdapter(config)
    elif provider == "groq":
        from skaro_core.llm.groq_adapter import GroqAdapter
        return GroqAdapter(config)
    elif provider == "ollama":
        from skaro_core.llm.ollama_adapter import OllamaAdapter
        return OllamaAdapter(config)
    else:
        raise ValueError(
            f"Unknown LLM provider: {provider}. "
            f"Supported: {', '.join(PROVIDER_PRESETS.keys())}"
        )
