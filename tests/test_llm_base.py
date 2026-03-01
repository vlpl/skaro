"""Tests for LLM base module: factory, error class, dataclasses, validation."""

from __future__ import annotations

import pytest

from skaro_core.config import LLMConfig
from skaro_core.llm.base import (
    BaseLLMAdapter,
    LLMError,
    LLMMessage,
    LLMResponse,
    PROVIDER_PRESETS,
    create_llm_adapter,
)


# ═══════════════════════════════════════════════════
# Dataclasses
# ═══════════════════════════════════════════════════


class TestLLMMessage:
    def test_create(self):
        msg = LLMMessage(role="user", content="hello")
        assert msg.role == "user"
        assert msg.content == "hello"

    def test_system_message(self):
        msg = LLMMessage(role="system", content="You are helpful")
        assert msg.role == "system"


class TestLLMResponse:
    def test_create_with_usage(self):
        resp = LLMResponse(
            content="Hi there",
            model="gpt-4",
            usage={"input_tokens": 10, "output_tokens": 5},
        )
        assert resp.content == "Hi there"
        assert resp.model == "gpt-4"
        assert resp.usage["input_tokens"] == 10

    def test_create_without_usage(self):
        resp = LLMResponse(content="text", model="m")
        assert resp.usage is None


# ═══════════════════════════════════════════════════
# LLMError
# ═══════════════════════════════════════════════════


class TestLLMError:
    def test_basic(self):
        err = LLMError("API timeout")
        assert str(err) == "API timeout"
        assert err.provider == ""
        assert err.retriable is False

    def test_with_provider(self):
        err = LLMError("Rate limited", provider="anthropic", retriable=True)
        assert err.provider == "anthropic"
        assert err.retriable is True

    def test_is_exception(self):
        with pytest.raises(LLMError):
            raise LLMError("fail")


# ═══════════════════════════════════════════════════
# PROVIDER_PRESETS
# ═══════════════════════════════════════════════════


class TestProviderPresets:
    def test_all_providers_present(self):
        for provider in ("anthropic", "openai", "groq", "ollama"):
            assert provider in PROVIDER_PRESETS

    def test_preset_structure(self):
        for name, preset in PROVIDER_PRESETS.items():
            assert len(preset) == 3  # (model, env_var, needs_key)
            model, env_var, needs_key = preset
            assert isinstance(model, str) and model
            assert isinstance(needs_key, bool)
            if needs_key:
                assert isinstance(env_var, str) and env_var

    def test_ollama_no_key(self):
        _, env_var, needs_key = PROVIDER_PRESETS["ollama"]
        assert needs_key is False
        assert env_var == ""


# ═══════════════════════════════════════════════════
# create_llm_adapter factory
# ═══════════════════════════════════════════════════


class TestCreateLLMAdapter:
    """Adapters validate API key in __init__, so we provide a fake one."""

    def test_anthropic(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-fake")
        config = LLMConfig(provider="anthropic", api_key_env="ANTHROPIC_API_KEY")
        adapter = create_llm_adapter(config)
        assert isinstance(adapter, BaseLLMAdapter)
        assert adapter.config.provider == "anthropic"

    def test_openai(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-fake")
        config = LLMConfig(provider="openai", api_key_env="OPENAI_API_KEY")
        adapter = create_llm_adapter(config)
        assert isinstance(adapter, BaseLLMAdapter)

    def test_groq(self, monkeypatch):
        monkeypatch.setenv("GROQ_API_KEY", "sk-fake")
        config = LLMConfig(provider="groq", api_key_env="GROQ_API_KEY")
        adapter = create_llm_adapter(config)
        assert isinstance(adapter, BaseLLMAdapter)

    def test_ollama(self):
        config = LLMConfig(provider="ollama")
        adapter = create_llm_adapter(config)
        assert isinstance(adapter, BaseLLMAdapter)

    def test_unknown_provider_raises(self):
        config = LLMConfig(provider="nonexistent")
        with pytest.raises(ValueError, match="Unknown LLM provider"):
            create_llm_adapter(config)

    def test_case_insensitive(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-fake")
        config = LLMConfig(provider="Anthropic", api_key_env="ANTHROPIC_API_KEY")
        adapter = create_llm_adapter(config)
        assert isinstance(adapter, BaseLLMAdapter)


# ═══════════════════════════════════════════════════
# _validate_api_key
# ═══════════════════════════════════════════════════


class TestValidateApiKey:
    def test_raises_without_key(self):
        """Adapter __init__ calls _validate_api_key, so creation itself raises."""
        config = LLMConfig(provider="anthropic", api_key_env="NONEXISTENT_KEY_12345")
        with pytest.raises(ValueError, match="API key not found"):
            create_llm_adapter(config)

    def test_passes_with_env_key(self, monkeypatch):
        monkeypatch.setenv("TEST_LLM_KEY", "sk-test-123")
        config = LLMConfig(provider="anthropic", api_key_env="TEST_LLM_KEY")
        adapter = create_llm_adapter(config)
        # Should not raise — key was found
        assert adapter is not None

    def test_ollama_no_key_needed(self):
        config = LLMConfig(provider="ollama")
        adapter = create_llm_adapter(config)
        assert adapter is not None
