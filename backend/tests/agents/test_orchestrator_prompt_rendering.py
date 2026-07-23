"""Tests for Orchestrator prompt rendering + EDGAR_IDENTITY fast-fail."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
import yaml

from backend.agent_engine.agents.base import Orchestrator
from backend.agent_engine.agents.config_loader import ProfileConfigLoader
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


def test_render_prompt_preserves_literal_json_braces(monkeypatch):
    """Prompts containing literal `{...}` (e.g. a JSON example) must pass
    through rendering untouched while named placeholders still substitute.

    Without guarding the placeholder scan, a raw LangChain ``PromptTemplate``
    would treat ``{"role": "user"}`` as an undefined variable and raise at
    startup.
    """
    monkeypatch.setattr(
        model_context,
        "_REGISTRY",
        {"gpt-4o-mini": {"max_input_tokens": 128_000, "source": "litellm"}},
    )
    raw = (
        'Example tool call: {"role": "user", "content": "hi"}\n'
        "BUDGET: exceeds {section_soft_cap_chars} chars"
    )
    rendered = Orchestrator._render_prompt(raw, "gpt-4o-mini")
    assert '{"role": "user", "content": "hi"}' in rendered
    assert "exceeds 204800 chars" in rendered
    assert "{section_soft_cap_chars}" not in rendered


def test_validate_edgar_identity_fast_fail(monkeypatch):
    monkeypatch.delenv("EDGAR_IDENTITY", raising=False)
    config = SimpleNamespace(tools=["sec_filing_list_sections"])
    with pytest.raises(ConfigurationError, match="EDGAR_IDENTITY"):
        Orchestrator._validate_edgar_identity(config)


def test_validate_edgar_identity_skipped_when_no_sec_tool(monkeypatch):
    monkeypatch.delenv("EDGAR_IDENTITY", raising=False)
    config = SimpleNamespace(tools=["finnhub_stock_quote"])
    # Should NOT raise
    Orchestrator._validate_edgar_identity(config)


# ---------------------------------------------------------------------------
# Task 9: two-step SEC tool registration + baseline prompt strategy
# ---------------------------------------------------------------------------


BASELINE_PROMPT_PATH = (
    Path(__file__).resolve().parents[2]
    / "agent_engine"
    / "agents"
    / "profiles"
    / "baseline"
    / "system_prompt.md"
)

PROFILES_DIR = (
    Path(__file__).resolve().parents[2] / "agent_engine" / "agents" / "profiles"
)


_BASELINE_TOOLS = [
    "finnhub_stock_quote",
    "finnhub_company_basic_financials",
    "tavily_financial_search",
    "sec_filing_list_sections",
    "sec_filing_get_section",
]

EXPECTED_TOOLS_BY_PROFILE = {
    "baseline": _BASELINE_TOOLS,
    "reader": _BASELINE_TOOLS,
    "quant": _BASELINE_TOOLS + ["duckdb_query", "text_to_sql"],
    "graph": _BASELINE_TOOLS + ["neo4j_query", "text_to_cypher"],
    "analyst": _BASELINE_TOOLS
    + ["duckdb_query", "text_to_sql", "neo4j_query", "text_to_cypher"],
}


def test_baseline_system_prompt_advertises_sec_tools():
    """The baseline prompt must point the agent at the two-step SEC tools.

    The detailed strategy (10-K item table, fiscal_year-passing rules, stub
    semantics, soft-cap behavior) was moved into the sec_filing_list_sections
    tool's reading_guide output for progressive disclosure — the system
    prompt now only carries a high-level pointer.
    """
    text = BASELINE_PROMPT_PATH.read_text()
    assert "sec_filing_list_sections" in text
    assert "sec_filing_get_section" in text
    # Detailed strategy is no longer in the prompt — it lives in the tool output.
    assert "10-K STANDARD SECTION TITLES" not in text
    assert "{section_soft_cap_chars}" not in text


def test_baseline_system_prompt_has_no_yahoo_residue():
    """DECISION-001 regression guard: the baseline prompt must not reference
    Yahoo or the dropped yfinance tool. Quote/fundamentals claims are cited by
    data provider name (Finnhub) with no fabricated per-ticker URL.

    forwardPE is deliberately NOT asserted absent: live verification
    (2026-07-21, AAPL/MSFT/TSM) showed the free-tier /stock/metric map does
    include forwardPE, so it is part of the fundamentals catalog.
    """
    text = BASELINE_PROMPT_PATH.read_text().lower()
    assert "yahoo" not in text
    assert "yfinance" not in text


def test_orchestrator_baseline_renders_prompt_end_to_end(monkeypatch):
    """Building the real baseline Orchestrator must produce a non-empty
    rendered system prompt with no unsubstituted placeholders.

    The baseline prompt no longer references {section_soft_cap_chars}
    (it was moved to the SEC tool's reading_guide), so this test now only
    checks that rendering succeeds and the SEC tool pointer survives.

    We patch init_chat_model / create_agent so the test does not require an
    OpenAI API key — the assertion target is the rendered prompt string,
    not actual model wiring.
    """
    monkeypatch.setenv("EDGAR_IDENTITY", "test@example.com")
    config = ProfileConfigLoader("baseline").load()

    with (
        patch("backend.agent_engine.agents.base.init_chat_model") as mock_init,
        patch("backend.agent_engine.agents.base.create_agent") as mock_create,
        patch("backend.agent_engine.agents.base.RunBudgetMiddleware"),
        patch(
            "backend.agent_engine.agents.base.handle_tool_errors", new=MagicMock()
        ),
    ):
        mock_init.return_value = MagicMock()
        mock_create.return_value = MagicMock()
        orch = Orchestrator(config)

    assert orch.system_prompt
    assert "sec_filing_list_sections" in orch.system_prompt
    # No leaked template tokens.
    assert "{section_soft_cap_chars}" not in orch.system_prompt
    assert "{max_tool_calls_per_run}" not in orch.system_prompt


def test_setup_tools_registers_new_tools_and_drops_old(monkeypatch):
    """setup_tools() wires the new two-step tools and unregisters the old one.

    Resets the module-level idempotency flag and clears the registry so a
    fresh setup_tools() reflects the current source of truth. monkeypatch
    restores the flag at teardown to keep the rest of the suite isolated.
    """
    from backend.agent_engine import tools as tools_module
    from backend.agent_engine.tools.registry import (
        clear_registry,
        get_tool,
        get_tools_by_names,
    )

    monkeypatch.setattr(tools_module, "_tools_registered", False)
    clear_registry()

    tools_module.setup_tools()

    resolved = get_tools_by_names(
        ["sec_filing_list_sections", "sec_filing_get_section"]
    )
    assert len(resolved) == 2
    assert all(t is not None for t in resolved)

    assert get_tool("sec_official_docs_retriever") is None


@pytest.mark.parametrize("profile", sorted(EXPECTED_TOOLS_BY_PROFILE.keys()))
def test_all_profiles_use_new_tool_names(profile):
    """Every profile config must replace sec_official_docs_retriever with the
    two-step pair and preserve all other tools in their original order.
    """
    yaml_path = PROFILES_DIR / profile / "orchestrator_config.yaml"
    with yaml_path.open() as f:
        config_dict = yaml.safe_load(f)

    tools = config_dict.get("tools", [])
    assert "sec_official_docs_retriever" not in tools
    assert "sec_filing_list_sections" in tools
    assert "sec_filing_get_section" in tools
    assert tools == EXPECTED_TOOLS_BY_PROFILE[profile]
