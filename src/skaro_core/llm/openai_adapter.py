"""OpenAI LLM adapter (compatible with OpenAI API and OpenAI-compatible endpoints)."""

from __future__ import annotations

from typing import AsyncIterator

import openai

from skaro_core.config import LLMConfig
from skaro_core.llm.base import BaseLLMAdapter, LLMError, LLMMessage, LLMResponse


class OpenAIAdapter(BaseLLMAdapter):
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self._validate_api_key()
        kwargs: dict = {"api_key": config.api_key}
        if config.base_url:
            kwargs["base_url"] = config.base_url
        self.client = openai.AsyncOpenAI(**kwargs)

    async def complete(self, messages: list[LLMMessage]) -> LLMResponse:
        oai_messages = [{"role": m.role, "content": m.content} for m in messages]
        try:
            response = await self.client.chat.completions.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                messages=oai_messages,
            )
        except openai.RateLimitError as e:
            raise LLMError(f"OpenAI rate limit exceeded. {e}", provider="openai", retriable=True) from e
        except openai.APIError as e:
            raise LLMError(f"OpenAI API error: {e}", provider="openai") from e
        except Exception as e:
            raise LLMError(f"OpenAI request failed: {e}", provider="openai") from e

        content = response.choices[0].message.content or ""
        usage = None
        if response.usage:
            usage = {
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
            }

        return LLMResponse(content=content, model=response.model or self.config.model, usage=usage)

    async def stream(self, messages: list[LLMMessage]) -> AsyncIterator[str]:
        oai_messages = [{"role": m.role, "content": m.content} for m in messages]
        try:
            stream = await self.client.chat.completions.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                messages=oai_messages,
                stream=True,
                stream_options={"include_usage": True},
            )
        except openai.RateLimitError as e:
            raise LLMError(f"OpenAI rate limit exceeded. {e}", provider="openai", retriable=True) from e
        except openai.APIError as e:
            raise LLMError(f"OpenAI API error: {e}", provider="openai") from e
        except Exception as e:
            raise LLMError(f"OpenAI request failed: {e}", provider="openai") from e

        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
            if chunk.usage:
                self.last_usage = {
                    "input_tokens": chunk.usage.prompt_tokens,
                    "output_tokens": chunk.usage.completion_tokens,
                }
