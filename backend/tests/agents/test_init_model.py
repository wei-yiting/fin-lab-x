"""Tests for the provider-aware ``_init_model`` helper in ``base``.

The helper translates ``ModelConfig`` (provider-prefixed name + reasoning +
thinking_budget) into the right kwargs for ``langchain.chat_models.init_chat_model``
across Gemini / Anthropic / OpenAI Responses.
"""

from unittest.mock import patch

import pytest

from backend.agent_engine.agents.base import _init_model
from backend.agent_engine.agents.config_loader import ModelConfig


def _call(cfg: ModelConfig) -> tuple[tuple, dict]:
    """Run ``_init_model`` against a mocked ``init_chat_model`` and return
    the ``(args, kwargs)`` it was called with."""
    with patch("backend.agent_engine.agents.base.init_chat_model") as mock_init:
        _init_model(cfg)
        mock_init.assert_called_once()
        return mock_init.call_args.args, mock_init.call_args.kwargs


def _kwargs(cfg: ModelConfig) -> dict:
    """Convenience wrapper around ``_call`` for tests that only need kwargs."""
    return _call(cfg)[1]


class TestInitModelGemini:
    def test_gemini_reasoning_on_with_none_budget_passes_none(self):
        cfg = ModelConfig(
            name="google_genai:gemini-2.5-flash",
            temperature=0.0,
            reasoning="on",
            thinking_budget=None,
        )
        args, kwargs = _call(cfg)
        assert args[0] == "gemini-2.5-flash"
        assert kwargs["model_provider"] == "google_genai"
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
        kwargs = _kwargs(cfg)
        assert kwargs["thinking_budget"] == 4096
        assert kwargs["include_thoughts"] is True

    def test_gemini_reasoning_off_forces_thinking_budget_zero(self):
        cfg = ModelConfig(
            name="google_genai:gemini-2.5-flash",
            temperature=0.0,
            reasoning="off",
            thinking_budget=None,
        )
        kwargs = _kwargs(cfg)
        assert kwargs["thinking_budget"] == 0
        # reasoning-off must NOT set include_thoughts (would attempt to
        # surface reasoning blocks the model isn't generating).
        assert "include_thoughts" not in kwargs

    def test_gemini_reasoning_on_with_dynamic_budget_negative_one_passes(self):
        """-1 is Gemini's documented "dynamic thinking" sentinel and must be
        forwarded as-is, not rejected by the thinking_budget footgun check."""
        cfg = ModelConfig(
            name="google_genai:gemini-2.5-flash",
            temperature=0.0,
            reasoning="on",
            thinking_budget=-1,
        )
        kwargs = _kwargs(cfg)
        assert kwargs["thinking_budget"] == -1
        assert kwargs["include_thoughts"] is True

    def test_gemini_reasoning_on_with_thinking_budget_zero_raises(self):
        """thinking_budget=0 would silently disable thinking, contradicting
        reasoning="on" — must fail fast at construction, not silently no-op."""
        cfg = ModelConfig(
            name="google_genai:gemini-2.5-flash",
            temperature=0.0,
            reasoning="on",
            thinking_budget=0,
        )
        with pytest.raises(ValueError, match="thinking_budget"):
            _init_model(cfg)

    def test_gemini_reasoning_on_with_thinking_budget_below_negative_one_raises(self):
        """Values below -1 are invalid per Gemini's API contract."""
        cfg = ModelConfig(
            name="google_genai:gemini-2.5-flash",
            temperature=0.0,
            reasoning="on",
            thinking_budget=-2,
        )
        with pytest.raises(ValueError, match="thinking_budget"):
            _init_model(cfg)


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
        kwargs = _kwargs(cfg)
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
        kwargs = _kwargs(cfg)
        assert "thinking" not in kwargs


class TestInitModelOpenAI:
    @pytest.mark.parametrize(
        "name",
        ["openai:gpt-5-mini", "gpt-5-mini", "openai:gpt-5-nano"],
        ids=["explicit-prefix", "bare-name", "explicit-prefix-nano"],
    )
    def test_reasoning_on_uses_responses_api(self, name):
        """Bare names and explicit ``openai:`` prefixes both route into the
        same reasoning="on" branch (responses API + unified reasoning dict).
        Guards against (a) a default-provider regression that would silently
        drop reasoning kwargs for prefix-less model names, and (b) the
        elif-provider-=='openai' branch split misrouting an explicit prefix
        into the unrecognized-provider path."""
        cfg = ModelConfig(name=name, temperature=0.0, reasoning="on")
        kwargs = _kwargs(cfg)
        # Unified reasoning dict (langchain-openai 0.3.24+) — both effort
        # and summary need to be set together; summary="auto" is what
        # actually surfaces reasoning content_blocks.
        assert kwargs["reasoning"] == {"effort": "medium", "summary": "auto"}
        assert kwargs["use_responses_api"] is True

    def test_openai_reasoning_off_sets_reasoning_effort_minimal(self):
        """Empirically verified against the real OpenAI API: omitting a
        reasoning kwarg entirely leaves gpt-5-tier models at the provider's
        own default effort, which still burns real, billed reasoning tokens
        (128/139 for gpt-5-nano, 64/74 for gpt-5-mini on a trivial prompt).
        "minimal" is the lowest tier that actually reaches
        reasoning_tokens=0; "none" is rejected by the API for these models."""
        cfg = ModelConfig(
            name="openai:gpt-5-nano",
            temperature=0.0,
            reasoning="off",
        )
        kwargs = _kwargs(cfg)
        assert kwargs["reasoning_effort"] == "minimal"

    def test_bare_name_defaults_to_openai_provider(self):
        """Names without a ``provider:`` prefix default to OpenAI semantics.

        Uses a reasoning-capable bare name (not e.g. gpt-4o-mini): on the
        openai provider, reasoning="off" assumes a reasoning-capable (gpt-5
        tier) model and sets reasoning_effort="minimal" — classic models
        are a documented-unsupported combination (see
        TestInitModelUnsupported)."""
        cfg = ModelConfig(
            name="gpt-5-nano",
            temperature=0.0,
            reasoning="off",
        )
        args, kwargs = _call(cfg)
        assert args[0] == "gpt-5-nano"
        assert kwargs["reasoning_effort"] == "minimal"
        assert "thinking_budget" not in kwargs
        assert "thinking" not in kwargs

    @pytest.mark.parametrize(
        ("name", "expected_provider", "expected_bare"),
        [
            ("openai:gpt-5-nano", "openai", "gpt-5-nano"),
            ("gpt-5-nano", "openai", "gpt-5-nano"),
            ("anthropic:claude-haiku-4-5", "anthropic", "claude-haiku-4-5"),
            (
                "google_genai:gemini-3.1-flash-lite",
                "google_genai",
                "gemini-3.1-flash-lite",
            ),
        ],
        ids=["openai-prefix", "openai-bare", "anthropic", "gemini"],
    )
    def test_mapped_providers_get_explicit_routing_and_bare_name(
        self, name, expected_provider, expected_bare
    ):
        """All three mapped providers must pass ``model_provider`` explicitly
        AND the bare positional model id, for two inverse failure modes:
        without explicit ``model_provider``, init_chat_model infers the
        provider from the name string on its own (a bare non-OpenAI-shaped
        name could silently route to the wrong integration); WITH it,
        init_chat_model's own prefix-stripping is skipped
        (langchain.chat_models.base._parse_model), so an unstripped
        ``provider:``-prefixed name would pass through as a literal, invalid
        model id. ``ModelConfig.provider``/``bare_name`` own the parsing;
        this test pins that _init_model consumes them for every mapped
        provider, not just openai (where both bugs were originally found)."""
        cfg = ModelConfig(name=name, temperature=0.0, reasoning="off")
        args, kwargs = _call(cfg)
        assert kwargs["model_provider"] == expected_provider
        assert args[0] == expected_bare


class TestInitModelUnrecognizedProvider:
    """Every unrecognized provider prefix used to fall into the OpenAI
    ``else`` branch silently. Now only ``google_genai``/``anthropic``/
    ``openai`` (incl. bare names) have a reasoning kwarg mapping; anything
    else with ``reasoning="on"`` must fail loudly instead of receiving
    OpenAI-specific kwargs that would break ``init_chat_model`` for that
    provider."""

    def test_unrecognized_provider_reasoning_on_raises(self):
        cfg = ModelConfig(
            name="mistral:mistral-large",
            temperature=0.0,
            reasoning="on",
        )
        with pytest.raises(ValueError, match="mistral"):
            _init_model(cfg)

    def test_unrecognized_provider_reasoning_off_is_noop(self):
        """No reasoning kwarg mapping is known for this provider, so we must
        not guess — only the base temperature kwarg should be passed."""
        cfg = ModelConfig(
            name="mistral:mistral-large",
            temperature=0.5,
            reasoning="off",
        )
        args, kwargs = _call(cfg)
        assert args[0] == "mistral:mistral-large"
        assert kwargs == {"temperature": 0.5}


class TestInitModelUnsupported:
    """``reasoning='unsupported'`` short-circuits all reasoning kwargs.

    Some bound models physically can't accept the kwarg
    (``gemini-1.5-flash`` rejects ``thinking_budget`` entirely;
    ``gemini-2.5-pro`` rejects ``thinking_budget=0`` because thinking
    can't be disabled) and classic non-reasoning OpenAI models (e.g.
    ``gpt-4o``) reject ``reasoning_effort`` outright. Collapsing
    ``unsupported`` into ``off`` would break all of these, so the helper
    must skip every reasoning kwarg regardless of provider.
    """

    @pytest.mark.parametrize(
        "name",
        [
            "google_genai:gemini-1.5-flash",
            "anthropic:claude-3-haiku",
            "openai:gpt-4o",
        ],
        ids=["gemini", "anthropic", "openai"],
    )
    def test_unsupported_skips_all_reasoning_kwargs(self, name):
        cfg = ModelConfig(name=name, temperature=0.0, reasoning="unsupported")
        kwargs = _kwargs(cfg)
        assert "thinking_budget" not in kwargs
        assert "thinking" not in kwargs
        assert "reasoning" not in kwargs
        assert "reasoning_effort" not in kwargs
        assert "use_responses_api" not in kwargs
        assert kwargs["temperature"] == 0.0

    @pytest.mark.parametrize(
        ("name", "expected_provider", "expected_bare"),
        [
            ("openai:gpt-4o", "openai", "gpt-4o"),
            ("gpt-4o", "openai", "gpt-4o"),
            ("anthropic:claude-3-haiku", "anthropic", "claude-3-haiku"),
            ("google_genai:gemini-1.5-flash", "google_genai", "gemini-1.5-flash"),
        ],
        ids=["openai-prefix", "openai-bare", "anthropic", "gemini"],
    )
    def test_unsupported_still_normalizes_mapped_provider_routing(
        self, name, expected_provider, expected_bare
    ):
        """The reasoning="unsupported" short-circuit returns before the
        reasoning-kwarg branches — it must not also skip the routing
        normalization (explicit model_provider + bare positional name), or
        an unsupported-reasoning model would fall through to
        init_chat_model's own inference/stripping with different results.
        Routing correctness is orthogonal to the reasoning state, so the
        guarantee must hold for every mapped provider."""
        cfg = ModelConfig(name=name, temperature=0.0, reasoning="unsupported")
        args, kwargs = _call(cfg)
        assert kwargs["model_provider"] == expected_provider
        assert args[0] == expected_bare


class TestInitModelDefaults:
    def test_bare_default_model_config_is_valid(self):
        """``ModelConfig()`` with no arguments (pure class defaults) must not
        raise and must produce kwargs a real ``init_chat_model`` call would
        accept. Regression guard for the default combination: the class
        default used to be name="gpt-4o-mini" + reasoning="off", which is a
        classic non-reasoning model paired with the openai reasoning="off"
        path — verified against the real API to fail with "Unrecognized
        request argument supplied: reasoning_effort". The default is now
        openai:gpt-5-nano, a reasoning-capable model compatible with the
        reasoning="off" default. args[0] is the bare "gpt-5-nano", not the
        "openai:"-prefixed config name — ModelConfig.bare_name owns the
        prefix parsing and _init_model consumes it (see
        test_mapped_providers_get_explicit_routing_and_bare_name)."""
        cfg = ModelConfig()
        args, kwargs = _call(cfg)
        assert args[0] == "gpt-5-nano"
        assert kwargs["reasoning_effort"] == "minimal"


class TestInitModelReasoningEffort:
    """``ModelConfig.reasoning_effort`` — the strength override used to pin
    benchmark configs (e.g. Luna reasoning.effort none vs medium, Gemini
    thinking_level minimal vs medium) on top of the existing on/off/
    unsupported three-state."""

    def test_openai_reasoning_effort_overrides_medium_default(self):
        cfg = ModelConfig(
            name="openai:gpt-5.6-luna",
            temperature=0.0,
            reasoning="on",
            reasoning_effort="none",
        )
        kwargs = _kwargs(cfg)
        assert kwargs["reasoning"] == {"effort": "none", "summary": "auto"}
        assert kwargs["use_responses_api"] is True

    def test_openai_reasoning_on_without_effort_keeps_medium_default(self):
        """Backward compatibility: the 5 shipped profiles never set
        reasoning_effort, so omitting it must reproduce the exact prior
        hardcoded behavior."""
        cfg = ModelConfig(name="openai:gpt-5.6-luna", temperature=0.0, reasoning="on")
        kwargs = _kwargs(cfg)
        assert kwargs["reasoning"] == {"effort": "medium", "summary": "auto"}

    def test_gemini_reasoning_effort_sets_thinking_level(self):
        cfg = ModelConfig(
            name="google_genai:gemini-3.6-flash",
            temperature=0.0,
            reasoning="on",
            reasoning_effort="minimal",
        )
        kwargs = _kwargs(cfg)
        assert kwargs["thinking_level"] == "minimal"
        # thinking_budget stays the existing pass-through (None here, since
        # the config didn't set one) — the two knobs are independent.
        assert kwargs["thinking_budget"] is None

    def test_gemini_reasoning_on_without_effort_omits_thinking_level(self):
        """Backward compatibility: profiles that never set reasoning_effort
        must not gain a new kwarg."""
        cfg = ModelConfig(
            name="google_genai:gemini-2.5-flash",
            temperature=0.0,
            reasoning="on",
            thinking_budget=None,
        )
        kwargs = _kwargs(cfg)
        assert "thinking_level" not in kwargs

    def test_reasoning_effort_without_reasoning_on_raises(self):
        cfg = ModelConfig(
            name="openai:gpt-5.6-luna",
            temperature=0.0,
            reasoning="off",
            reasoning_effort="none",
        )
        with pytest.raises(
            ValueError, match="reasoning_effort requires reasoning='on'"
        ):
            _init_model(cfg)

    def test_reasoning_effort_with_unsupported_raises(self):
        cfg = ModelConfig(
            name="openai:gpt-4o",
            temperature=0.0,
            reasoning="unsupported",
            reasoning_effort="medium",
        )
        with pytest.raises(
            ValueError, match="reasoning_effort requires reasoning='on'"
        ):
            _init_model(cfg)

    def test_anthropic_reasoning_effort_raises_no_effort_tier_concept(self):
        cfg = ModelConfig(
            name="anthropic:claude-sonnet-4-5",
            temperature=1.0,
            reasoning="on",
            thinking_budget=2048,
            reasoning_effort="medium",
        )
        with pytest.raises(ValueError, match="not supported for provider 'anthropic'"):
            _init_model(cfg)

    @pytest.mark.parametrize(
        "reasoning_effort",
        [
            pytest.param("", id="empty-string"),
            pytest.param("   ", id="whitespace-only"),
        ],
    )
    def test_empty_or_blank_reasoning_effort_raises(self, reasoning_effort):
        """An empty/blank reasoning_effort passes ModelConfig's plain
        ``str | None`` Pydantic validation but must fail loudly here rather
        than silently falling back to "medium" via truthiness (``or``)."""
        cfg = ModelConfig(
            name="openai:gpt-5.6-luna",
            temperature=0.0,
            reasoning="on",
            reasoning_effort=reasoning_effort,
        )
        with pytest.raises(
            ValueError, match="reasoning_effort must be a non-empty string"
        ):
            _init_model(cfg)


class TestInitModelTemperature:
    @pytest.mark.parametrize(
        "name",
        [
            "google_genai:gemini-3.1-flash-lite",
            "anthropic:claude-haiku-4-5",
            "openai:gpt-5-nano",
            "gpt-5-nano",
        ],
    )
    def test_temperature_passed_for_all_providers(self, name):
        """Uses reasoning-capable model names for every provider: pairing
        classic OpenAI models (gpt-4o-mini) with reasoning="off" is a
        documented-unsupported combination (see TestInitModelUnsupported) —
        it only "worked" here because init_chat_model is mocked."""
        cfg = ModelConfig(name=name, temperature=0.7, reasoning="off")
        kwargs = _kwargs(cfg)
        assert kwargs["temperature"] == 0.7
