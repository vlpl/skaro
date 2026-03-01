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

    async def complete(self, messages: list[LLMMessage]) -> LLMResponse:
        system_msg = ""
        chat_messages = []
        for msg in messages:
            if msg.role == "system":
                system_msg += msg.content + "\n"
            else:
                chat_messages.append({"role": msg.role, "content": msg.content})

        try:
            response = await self.client.messages.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                system=system_msg.strip() if system_msg else anthropic.NOT_GIVEN,
                messages=chat_messages,
            )
        except anthropic.RateLimitError as e:
            raise LLMError(f"Anthropic rate limit exceeded. {e}", provider="anthropic", retriable=True) from e
        except anthropic.APIError as e:
            raise LLMError(f"Anthropic API error: {e}", provider="anthropic") from e
        except Exception as e:
            raise LLMError(f"Anthropic request failed: {e}", provider="anthropic") from e

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
        system_msg = ""
        chat_messages = []
        for msg in messages:
            if msg.role == "system":
                system_msg += msg.content + "\n"
            else:
                chat_messages.append({"role": msg.role, "content": msg.content})

        try:
            async with self.client.messages.stream(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                system=system_msg.strip() if system_msg else anthropic.NOT_GIVEN,
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
        except anthropic.RateLimitError as e:
            raise LLMError(f"Anthropic rate limit exceeded. {e}", provider="anthropic", retriable=True) from e
        except anthropic.APIError as e:
            raise LLMError(f"Anthropic API error: {e}", provider="anthropic") from e
        except Exception as e:
            raise LLMError(f"Anthropic request failed: {e}", provider="anthropic") from e
