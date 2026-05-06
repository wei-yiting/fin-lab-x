"""Tests for the provider-aware ``_init_model`` helper in ``base``.

The helper translates ``ModelConfig`` (provider-prefixed name + reasoning +
thinking_budget) into the right kwargs for ``langchain.chat_models.init_chat_model``
across Gemini / Anthropic / OpenAI Responses.
"""

from unittest.mock import patch

import pytest

from backend.agent_engine.agents.base import _init_model
from backend.agent_engine.agents.config_loader import ModelConfig


class TestInitModelGemini:
    def test_gemini_reasoning_on_with_none_budget_passes_none(self):
        cfg = ModelConfig(
            name="google_genai:gemini-2.5-flash",
            temperature=0.0,
            reasoning="on",
            thinking_budget=None,
        )
        with patch("backend.agent_engine.agents.base.init_chat_model") as mock_init:
            _init_model(cfg)
            mock_init.assert_called_once()
            args, kwargs = mock_init.call_args
            assert args[0] == "google_genai:gemini-2.5-flash"
            assert kwargs["temperature"] == 0.0
            assert kwargs["thinking_budget"] is None
            # Gemini reasoning-on requires include_thoughts=True for the
            # response to actually carry reasoning content_blocks.
            assert kwargs["include_thoughts"] is True
            # Gemini path must not leak Anthropic / OpenAI kwargs
            assert "thinking" not in kwargs
            assert "reasoning" not in kwargs
            assert "reasoning_effort" not in kwargs
            assert "use_responses_api" not in kwargs

    def test_gemini_reasoning_on_with_explicit_budget(self):
        cfg = ModelConfig(
            name="google_genai:gemini-2.5-flash",
            temperature=0.0,
            reasoning="on",
            thinking_budget=4096,
        )
        with patch("backend.agent_engine.agents.base.init_chat_model") as mock_init:
            _init_model(cfg)
            kwargs = mock_init.call_args.kwargs
            assert kwargs["thinking_budget"] == 4096
            assert kwargs["include_thoughts"] is True

    def test_gemini_reasoning_off_forces_thinking_budget_zero(self):
        cfg = ModelConfig(
            name="google_genai:gemini-2.5-flash",
            temperature=0.0,
            reasoning="off",
            thinking_budget=None,
        )
        with patch("backend.agent_engine.agents.base.init_chat_model") as mock_init:
            _init_model(cfg)
            kwargs = mock_init.call_args.kwargs
            assert kwargs["thinking_budget"] == 0
            # reasoning-off must NOT set include_thoughts (would attempt to
            # surface reasoning blocks the model isn't generating).
            assert "include_thoughts" not in kwargs


class TestInitModelAnthropic:
    def test_anthropic_reasoning_on_without_budget_raises(self):
        cfg = ModelConfig(
            name="anthropic:claude-sonnet-4-5",
            temperature=0.0,
            reasoning="on",
            thinking_budget=None,
        )
        # Match "thinking_budget" so a future refactor that drops the
        # actionable hint trips the test, not a generic provider name.
        with pytest.raises(ValueError, match="thinking_budget"):
            _init_model(cfg)

    def test_anthropic_reasoning_on_with_low_budget_raises(self):
        """Anthropic API rejects budget_tokens < 1024 — fail fast at agent
        construction rather than letting it bubble as a mid-request 400."""
        cfg = ModelConfig(
            name="anthropic:claude-3-5-sonnet",
            temperature=0.0,
            reasoning="on",
            thinking_budget=512,
        )
        with pytest.raises(ValueError, match="thinking_budget >= 1024"):
            _init_model(cfg)

    def test_anthropic_reasoning_on_with_budget_passes_thinking_block(self):
        cfg = ModelConfig(
            name="anthropic:claude-sonnet-4-5",
            temperature=1.0,
            reasoning="on",
            thinking_budget=2048,
        )
        with patch("backend.agent_engine.agents.base.init_chat_model") as mock_init:
            _init_model(cfg)
            kwargs = mock_init.call_args.kwargs
            assert kwargs["thinking"] == {
                "type": "enabled",
                "budget_tokens": 2048,
            }

    def test_anthropic_reasoning_on_with_non_unity_temperature_raises(self):
        """Anthropic extended thinking rejects any temperature != 1.0 with
        HTTP 400. Catch at startup rather than mid-request."""
        cfg = ModelConfig(
            name="anthropic:claude-sonnet-4-5",
            temperature=0.0,
            reasoning="on",
            thinking_budget=2048,
        )
        with pytest.raises(ValueError, match="temperature=1.0"):
            _init_model(cfg)

    def test_anthropic_reasoning_off_omits_thinking_block(self):
        cfg = ModelConfig(
            name="anthropic:claude-sonnet-4-5",
            temperature=0.0,
            reasoning="off",
        )
        with patch("backend.agent_engine.agents.base.init_chat_model") as mock_init:
            _init_model(cfg)
            kwargs = mock_init.call_args.kwargs
            assert "thinking" not in kwargs


class TestInitModelOpenAI:
    def test_openai_reasoning_on_uses_responses_api(self):
        cfg = ModelConfig(
            name="openai:gpt-5-mini",
            temperature=0.0,
            reasoning="on",
        )
        with patch("backend.agent_engine.agents.base.init_chat_model") as mock_init:
            _init_model(cfg)
            kwargs = mock_init.call_args.kwargs
            # Unified reasoning dict (langchain-openai 0.3.24+) — both effort
            # and summary need to be set together; summary="auto" is what
            # actually surfaces reasoning content_blocks.
            assert kwargs["reasoning"] == {"effort": "medium", "summary": "auto"}
            assert kwargs["use_responses_api"] is True

    def test_openai_reasoning_off_omits_reasoning_kwargs(self):
        cfg = ModelConfig(
            name="openai:gpt-4o-mini",
            temperature=0.0,
            reasoning="off",
        )
        with patch("backend.agent_engine.agents.base.init_chat_model") as mock_init:
            _init_model(cfg)
            kwargs = mock_init.call_args.kwargs
            assert "reasoning" not in kwargs
            assert "use_responses_api" not in kwargs

    def test_bare_name_defaults_to_openai_provider(self):
        """Names without a ``provider:`` prefix default to OpenAI semantics."""
        cfg = ModelConfig(
            name="gpt-4o-mini",
            temperature=0.0,
            reasoning="off",
        )
        with patch("backend.agent_engine.agents.base.init_chat_model") as mock_init:
            _init_model(cfg)
            args, kwargs = mock_init.call_args
            assert args[0] == "gpt-4o-mini"
            assert "thinking_budget" not in kwargs
            assert "thinking" not in kwargs


class TestInitModelUnsupported:
    """``reasoning='unsupported'`` short-circuits all reasoning kwargs.

    Some bound models physically can't accept the kwarg
    (``gemini-1.5-flash`` rejects ``thinking_budget`` entirely;
    ``gemini-2.5-pro`` rejects ``thinking_budget=0`` because thinking
    can't be disabled). Collapsing ``unsupported`` into ``off`` would
    break both, so the helper must skip every reasoning kwarg regardless
    of provider.
    """

    def test_unsupported_skips_all_reasoning_kwargs_for_gemini(self):
        cfg = ModelConfig(
            name="google_genai:gemini-1.5-flash",
            temperature=0.0,
            reasoning="unsupported",
            thinking_budget=None,
        )
        with patch("backend.agent_engine.agents.base.init_chat_model") as mock_init:
            _init_model(cfg)
            kwargs = mock_init.call_args.kwargs
            assert "thinking_budget" not in kwargs
            assert "thinking" not in kwargs
            assert "reasoning" not in kwargs
            assert "use_responses_api" not in kwargs
            assert kwargs["temperature"] == 0.0

    def test_unsupported_skips_reasoning_kwargs_for_anthropic(self):
        cfg = ModelConfig(
            name="anthropic:claude-3-haiku",
            temperature=0.0,
            reasoning="unsupported",
        )
        with patch("backend.agent_engine.agents.base.init_chat_model") as mock_init:
            _init_model(cfg)
            kwargs = mock_init.call_args.kwargs
            assert "thinking" not in kwargs
            assert kwargs["temperature"] == 0.0

    def test_unsupported_skips_reasoning_kwargs_for_openai(self):
        cfg = ModelConfig(
            name="openai:gpt-4o",
            temperature=0.0,
            reasoning="unsupported",
        )
        with patch("backend.agent_engine.agents.base.init_chat_model") as mock_init:
            _init_model(cfg)
            kwargs = mock_init.call_args.kwargs
            assert "reasoning" not in kwargs
            assert "use_responses_api" not in kwargs
            assert kwargs["temperature"] == 0.0


class TestInitModelTemperature:
    @pytest.mark.parametrize(
        "name",
        [
            "google_genai:gemini-2.5-flash",
            "anthropic:claude-sonnet-4-5",
            "openai:gpt-4o-mini",
            "gpt-4o-mini",
        ],
    )
    def test_temperature_passed_for_all_providers(self, name):
        cfg = ModelConfig(name=name, temperature=0.7, reasoning="off")
        with patch("backend.agent_engine.agents.base.init_chat_model") as mock_init:
            _init_model(cfg)
            kwargs = mock_init.call_args.kwargs
            assert kwargs["temperature"] == 0.7
