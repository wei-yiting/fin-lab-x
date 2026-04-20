"""Tests for Orchestrator prompt rendering + EDGAR_IDENTITY fast-fail."""

from types import SimpleNamespace

import pytest

from backend.agent_engine.agents.base import Orchestrator
from backend.agent_engine.utils import model_context
from backend.common.sec_core import ConfigurationError


@pytest.fixture(autouse=True)
def _reset_warned_models():
    model_context._WARNED_MODELS.clear()
    yield
    model_context._WARNED_MODELS.clear()


@pytest.mark.parametrize(
    "model_name,ctx_tokens,expected_cap",
    [
        ("gpt-4o-mini", 128_000, 204_800),
        ("claude-opus-4-20250514", 200_000, 320_000),
        ("future-model-131072", 131_072, 209_715),
    ],
)
def test_render_prompt_registered_model(
    monkeypatch, model_name, ctx_tokens, expected_cap
):
    monkeypatch.setattr(
        model_context,
        "_REGISTRY",
        {model_name: {"max_input_tokens": ctx_tokens, "source": "litellm"}},
    )
    raw = "BUDGET: exceeds {section_soft_cap_chars} chars"
    rendered = Orchestrator._render_prompt(raw, model_name)
    assert f"exceeds {expected_cap} chars" in rendered


def test_render_prompt_unknown_model_fallback_and_warn_once(monkeypatch, caplog):
    monkeypatch.setattr(model_context, "_REGISTRY", {})
    model_context._WARNED_MODELS.clear()

    raw = "BUDGET: exceeds {section_soft_cap_chars} chars"
    with caplog.at_level("WARNING", logger=model_context.logger.name):
        r1 = Orchestrator._render_prompt(raw, "made-up-model-9000")
        r2 = Orchestrator._render_prompt(raw, "made-up-model-9000")
        r3 = Orchestrator._render_prompt(raw, "made-up-model-9000")

    # 128_000 * 0.4 * 4 = 204_800 (DEFAULT_CONTEXT_WINDOW fallback)
    for rendered in (r1, r2, r3):
        assert "exceeds 204800 chars" in rendered

    warnings = [
        rec for rec in caplog.records if "made-up-model-9000" in rec.getMessage()
    ]
    assert len(warnings) == 1


def test_render_prompt_missing_var_raises():
    raw = "Prompt with {nonexistent_var} placeholder."
    with pytest.raises(
        ValueError, match=r"Prompt references undefined variables.*nonexistent_var"
    ):
        Orchestrator._render_prompt(raw, "gpt-4o-mini")


def test_render_prompt_no_placeholder_verbatim():
    raw = "Pure prompt"
    assert Orchestrator._render_prompt(raw, "gpt-4o-mini") == "Pure prompt"


def test_validate_edgar_identity_fast_fail(monkeypatch):
    monkeypatch.delenv("EDGAR_IDENTITY", raising=False)
    config = SimpleNamespace(tools=["sec_filing_list_sections"])
    with pytest.raises(ConfigurationError, match="EDGAR_IDENTITY"):
        Orchestrator._validate_edgar_identity(config)


def test_validate_edgar_identity_skipped_when_no_sec_tool(monkeypatch):
    monkeypatch.delenv("EDGAR_IDENTITY", raising=False)
    config = SimpleNamespace(tools=["yfinance_stock_quote"])
    # Should NOT raise
    Orchestrator._validate_edgar_identity(config)
