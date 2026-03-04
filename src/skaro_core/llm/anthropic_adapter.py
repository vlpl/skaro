"""Anthropic Claude LLM adapter."""

from __future__ import annotations

from typing import AsyncIterator

import anthropic

from skaro_core.config import LLMConfig
from skaro_core.llm.base import BaseLLMAdapter, LLMError, LLMMessage, LLMResponse


class AnthropicAdapter(BaseLLMAdapter):
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self._validate_api_key()
        self.client = anthropic.AsyncAnthropic(api_key=config.api_key)

    def _wrap_error(self, exc: Exception) -> LLMError:
        if isinstance(exc, anthropic.RateLimitError):
            return LLMError(f"Anthropic rate limit exceeded. {exc}", provider="anthropic", retriable=True)
        if isinstance(exc, anthropic.AuthenticationError):
            return LLMError(
                "Anthropic authentication failed (401). Check your API key in Settings.",
                provider="anthropic", status_code=401,
            )
        if isinstance(exc, anthropic.PermissionDeniedError):
            return LLMError(
                "Anthropic permission denied (403). Your API key may lack required permissions.",
                provider="anthropic", status_code=403,
            )
        if isinstance(exc, anthropic.APIError):
            return LLMError(f"Anthropic API error: {exc}", provider="anthropic")
        return LLMError(f"Anthropic request failed: {exc}", provider="anthropic")

    def _prepare_messages(self, messages: list[LLMMessage]) -> tuple[str, list[dict]]:
        """Split system messages out (Anthropic uses a separate parameter)."""
        system_msg = ""
        chat_messages = []
        for msg in messages:
            if msg.role == "system":
                system_msg += msg.content + "\n"
            else:
                chat_messages.append({"role": msg.role, "content": msg.content})
        return system_msg.strip(), chat_messages

    async def complete(self, messages: list[LLMMessage]) -> LLMResponse:
        system_msg, chat_messages = self._prepare_messages(messages)

        try:
            response = await self.client.messages.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                system=system_msg if system_msg else anthropic.NOT_GIVEN,
                messages=chat_messages,
            )
        except LLMError:
            raise
        except Exception as e:
            raise self._wrap_error(e) from e

        content = ""
        for block in response.content:
            if block.type == "text":
                content += block.text

        return LLMResponse(
            content=content,
            model=response.model,
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
        )

    async def stream(self, messages: list[LLMMessage]) -> AsyncIterator[str]:
        system_msg, chat_messages = self._prepare_messages(messages)

        try:
            async with self.client.messages.stream(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                system=system_msg if system_msg else anthropic.NOT_GIVEN,
                messages=chat_messages,
            ) as stream:
                async for text in stream.text_stream:
                    yield text
                # Capture usage after stream completes
                final = await stream.get_final_message()
                if final and final.usage:
                    self.last_usage = {
                        "input_tokens": final.usage.input_tokens,
                        "output_tokens": final.usage.output_tokens,
                    }
        except LLMError:
            raise
        except Exception as e:
            raise self._wrap_error(e) from e
