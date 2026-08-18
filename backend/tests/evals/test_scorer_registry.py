"""Tests for scorer registry resolution and language policy scorers."""

from typing import Any

import pytest

from backend.evals.eval_spec_schema import ScorerConfig


def test_resolve_scorers_resolves_programmatic_dotpath() -> None:
    from backend.evals.scorer_registry import resolve_scorers
    from backend.evals.scenarios.language_policy.scorer import tool_arg_no_cjk

    scorers = resolve_scorers(
        [
            ScorerConfig(
                name="tool_arg_no_cjk",
                function="backend.evals.scenarios.language_policy.scorer.tool_arg_no_cjk",
            )
        ]
    )

    assert len(scorers) == 1
    assert scorers[0] is tool_arg_no_cjk


def test_resolve_scorers_raises_import_error_for_missing_module() -> None:
    from backend.evals.scorer_registry import resolve_scorers

    scorer_config = ScorerConfig.model_construct(
        name="missing_module",
        function="backend.evals.scenarios.missing_scenario.scorer.tool_arg_no_cjk",
    )

    with pytest.raises(
        ImportError, match="backend\\.evals\\.scenarios\\.missing_scenario\\.scorer"
    ):
        resolve_scorers([scorer_config])


def test_resolve_scorers_raises_import_error_for_missing_function() -> None:
    from backend.evals.scorer_registry import resolve_scorers

    scorer_config = ScorerConfig.model_construct(
        name="missing_function",
        function="backend.evals.scenarios.language_policy.scorer.missing_function",
    )

    with pytest.raises(ImportError, match="missing_function"):
        resolve_scorers([scorer_config])


def test_resolve_scorers_resolves_diagnostic_execution_health() -> None:
    from backend.evals.diagnostic.execution_scorer import execution_health
    from backend.evals.scorer_registry import resolve_scorers

    scorers = resolve_scorers(
        [
            ScorerConfig(
                name="diagnostic_execution_health",
                function="backend.evals.diagnostic.execution_scorer.execution_health",
            )
        ]
    )

    assert scorers == [execution_health]


def _capture_llm_classifier(
    monkeypatch: pytest.MonkeyPatch,
) -> dict[str, Any]:
    """Monkeypatch scorer_registry.LLMClassifier and capture its kwargs."""
    from backend.evals import scorer_registry

    captured: dict[str, Any] = {}

    class FakeLLMClassifier:
        def __init__(
            self,
            *,
            name: str,
            prompt_template: str,
            choice_scores: dict[str, float],
            use_cot: bool,
            model: str | None = None,
            temperature: float,
            client: Any,
        ) -> None:
            captured["name"] = name
            captured["prompt_template"] = prompt_template
            captured["choice_scores"] = choice_scores
            captured["use_cot"] = use_cot
            captured["model"] = model
            captured["temperature"] = temperature
            captured["client"] = client

    monkeypatch.setattr(scorer_registry, "LLMClassifier", FakeLLMClassifier)
    return captured


_GEMINI_JUDGE_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"


def _judge_config() -> ScorerConfig:
    return ScorerConfig(
        name="judge_score",
        type="llm_judge",
        rubric="Judge whether the answer follows the policy.",
        model="gemini-3.6-flash",
        use_cot=True,
        choice_scores={"Y": 1.0, "N": 0.0},
    )


def test_resolve_scorers_builds_llm_classifier(monkeypatch: pytest.MonkeyPatch) -> None:
    from backend.evals import scorer_registry

    monkeypatch.setenv("GEMINI_API_KEY", "sk-test-gemini")
    captured = _capture_llm_classifier(monkeypatch)

    scorers = scorer_registry.resolve_scorers([_judge_config()])

    assert len(scorers) == 1
    assert callable(scorers[0])
    client = captured.pop("client")
    assert client.api_key == "sk-test-gemini"
    assert str(client.base_url) == _GEMINI_JUDGE_BASE_URL
    assert captured == {
        "name": "judge_score",
        "prompt_template": "Judge whether the answer follows the policy.",
        "choice_scores": {"Y": 1.0, "N": 0.0},
        "use_cot": True,
        "model": "gemini-3.6-flash",
        "temperature": 0.0,
    }


def test_llm_judge_uses_gemini_key_when_openai_and_braintrust_keys_are_present(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ADR-0007's original bug was an env-inferred key picking the wrong
    provider; guard the same failure mode for the Gemini client — an
    OPENAI_API_KEY sitting in .env for the agent must never leak into the
    judge."""
    from backend.evals import scorer_registry

    monkeypatch.setenv("GEMINI_API_KEY", "sk-test-gemini")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-openai")
    monkeypatch.setenv("BRAINTRUST_API_KEY", "sk-test-braintrust")
    captured = _capture_llm_classifier(monkeypatch)

    scorer_registry.resolve_scorers([_judge_config()])

    client = captured["client"]
    assert client.api_key == "sk-test-gemini"
    assert str(client.base_url) == _GEMINI_JUDGE_BASE_URL


def test_llm_judge_ignores_openai_base_url_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from backend.evals import scorer_registry

    monkeypatch.setenv("GEMINI_API_KEY", "sk-test-gemini")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://api.braintrust.dev/v1/proxy")
    captured = _capture_llm_classifier(monkeypatch)

    scorer_registry.resolve_scorers([_judge_config()])

    assert str(captured["client"].base_url) == _GEMINI_JUDGE_BASE_URL


def test_llm_judge_fails_fast_without_gemini_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from backend.evals import scorer_registry

    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    _capture_llm_classifier(monkeypatch)

    with pytest.raises(ValueError, match="GEMINI_API_KEY") as exc_info:
        scorer_registry.resolve_scorers([_judge_config()])

    assert "judge" in str(exc_info.value)
    assert _GEMINI_JUDGE_BASE_URL in str(exc_info.value)


def test_scorer_config_rejects_temperature_on_programmatic_scorer() -> None:
    with pytest.raises(ValueError, match="temperature"):
        ScorerConfig(
            name="tool_arg_no_cjk",
            function="backend.evals.scenarios.language_policy.scorer.tool_arg_no_cjk",
            temperature=0.5,
        )


def test_scorer_config_rejects_explicit_zero_temperature_on_programmatic_scorer() -> (
    None
):
    with pytest.raises(ValueError, match="temperature"):
        ScorerConfig(
            name="tool_arg_no_cjk",
            function="backend.evals.scenarios.language_policy.scorer.tool_arg_no_cjk",
            temperature=0.0,
        )


def test_scorer_config_rejects_out_of_range_temperature_on_llm_judge() -> None:
    with pytest.raises(ValueError, match="less than or equal to 2"):
        ScorerConfig(
            name="judge_score",
            type="llm_judge",
            rubric="Rate the answer.",
            temperature=2.5,
        )


def test_scorer_config_allows_programmatic_scorer_without_temperature() -> None:
    scorer_config = ScorerConfig(
        name="tool_arg_no_cjk",
        function="backend.evals.scenarios.language_policy.scorer.tool_arg_no_cjk",
    )

    assert scorer_config.temperature == 0.0


def test_resolve_scorers_rejects_llm_judge_without_rubric() -> None:
    from backend.evals.scorer_registry import resolve_scorers

    scorer_config = ScorerConfig.model_construct(
        name="judge_score",
        type="llm_judge",
        rubric=None,
        model="gpt-4.1",
        choice_scores={"Y": 1.0, "N": 0.0},
        use_cot=False,
    )

    with pytest.raises(ValueError, match="rubric"):
        resolve_scorers([scorer_config])


def test_tool_arg_no_cjk_passes_for_english_arguments() -> None:
    from backend.evals.scenarios.language_policy.scorer import tool_arg_no_cjk

    result = tool_arg_no_cjk(
        {
            "tool_outputs": [
                {
                    "tool": "tavily_financial_search",
                    "args": {"query": "latest news about MSFT"},
                }
            ]
        },
        {"search_query_no_cjk": True, "tool": "tavily_financial_search"},
        input="What is the latest news about MSFT?",
    )

    assert result["name"] == "tool_arg_no_cjk"
    assert result["score"] == 1.0


def test_execution_health_passes_when_execution_completes_and_tools_succeed() -> None:
    from backend.evals.diagnostic.execution_scorer import execution_health

    result = execution_health(
        {
            "response": "done",
            "finished_normally": True,
            "tool_outputs": [
                {"tool": "search_news", "result": "ok"},
                {"tool": "fetch_quote", "result": {"price": 123}},
            ],
        },
        {
            "draft_pass_signals": ["do not read me"],
            "expected_best_source": "ignore me",
        },
        input={"question": "What changed?"},
    )

    assert result["name"] == "diagnostic_execution_health"
    assert result["score"] == 1.0
    assert result["metadata"] == {
        "execution_complete": True,
        "tool_call_all_successful": True,
        "tool_call_count": 2,
        "tool_error_names": [],
    }


def test_execution_health_records_zero_tool_calls() -> None:
    """An agent answering from model memory still scores 1.0 — tool_call_count
    is the only thing separating it from a clean tool-backed run. Whether a
    question warranted a tool at all is a human-review judgement."""
    from backend.evals.diagnostic.execution_scorer import execution_health

    result = execution_health(
        {"response": "Answered without tools", "finished_normally": True},
        {},
        input="Any question",
    )

    assert result["score"] == 1.0
    assert result["metadata"]["tool_call_all_successful"] is True
    assert result["metadata"]["tool_call_count"] == 0


def test_execution_health_fails_when_finished_normally_absent() -> None:
    """Response text alone is not a completion signal — the flag decides."""
    from backend.evals.diagnostic.execution_scorer import execution_health

    result = execution_health(
        {"response": "Partial answer text", "tool_outputs": []},
        {"draft_pass_signals": ["still ignored"]},
        input="Any question",
    )

    assert result["score"] == 0.0
    assert result["metadata"] == {
        "execution_complete": False,
        "tool_call_all_successful": True,
        "tool_call_count": 0,
        "tool_error_names": [],
    }


def test_execution_health_fails_when_finished_normally_false() -> None:
    from backend.evals.diagnostic.execution_scorer import execution_health

    result = execution_health(
        {"response": "text", "finished_normally": False, "tool_outputs": []},
        {},
        input="Any question",
    )

    assert result["score"] == 0.0
    assert result["metadata"]["execution_complete"] is False


def test_execution_health_passes_for_empty_response_when_finished_normally() -> None:
    """A legitimately empty (or whitespace-only) response can still complete."""
    from backend.evals.diagnostic.execution_scorer import execution_health

    for response in ("", "   \n"):
        result = execution_health(
            {"response": response, "finished_normally": True, "tool_outputs": []},
            {},
            input="Any question",
        )

        assert result["score"] == 1.0
        assert result["metadata"]["execution_complete"] is True


def test_execution_health_fails_and_emits_tool_error_names() -> None:
    from backend.evals.diagnostic.execution_scorer import execution_health

    result = execution_health(
        {
            "response": "Partial answer",
            "finished_normally": True,
            "tool_outputs": [
                {"tool": "search_news", "result": "ok"},
                {"tool": "fetch_quote", "error": "timeout"},
                {"tool": "tool_without_name", "error": None},
            ],
        },
        {},
        input="Question",
    )

    assert result["score"] == 0.0
    assert result["metadata"] == {
        "execution_complete": True,
        "tool_call_all_successful": False,
        "tool_call_count": 3,
        "tool_error_names": ["fetch_quote"],
    }


def test_tool_arg_no_cjk_fails_for_cjk_arguments() -> None:
    from backend.evals.scenarios.language_policy.scorer import tool_arg_no_cjk

    result = tool_arg_no_cjk(
        {
            "tool_outputs": [
                {
                    "tool": "tavily_financial_search",
                    "args": {"query": "微軟最新新聞"},
                }
            ]
        },
        {"search_query_no_cjk": True, "tool": "tavily_financial_search"},
        input="微軟最近有什麼新聞？",
    )

    assert result["name"] == "tool_arg_no_cjk"
    assert result["score"] == 0.0


def test_tool_arg_no_cjk_ignores_non_matching_tool_outputs() -> None:
    from backend.evals.scenarios.language_policy.scorer import tool_arg_no_cjk

    result = tool_arg_no_cjk(
        {
            "tool_outputs": [
                {
                    "tool": "other_tool",
                    "args": {"query": "微軟最新新聞"},
                }
            ]
        },
        {"search_query_no_cjk": True, "tool": "tavily_financial_search"},
        input="What is the latest news about MSFT?",
    )

    assert result["score"] == 1.0


def test_tool_arg_no_cjk_passes_when_expected_tool_is_missing() -> None:
    from backend.evals.scenarios.language_policy.scorer import tool_arg_no_cjk

    result = tool_arg_no_cjk(
        {
            "tool_outputs": [
                {
                    "tool": "other_tool",
                    "args": {"query": "latest news about MSFT"},
                }
            ]
        },
        {"search_query_no_cjk": True, "tool": "tavily_financial_search"},
        input="What is the latest news about MSFT?",
    )

    assert result["score"] == 1.0


@pytest.mark.parametrize(
    ("ticker", "expected_score"),
    [
        ("AAPL", 1.0),
        ("aapl", 0.0),
    ],
)
def test_tool_arg_no_cjk_validates_ticker_by_regex(
    ticker: str,
    expected_score: float,
) -> None:
    from backend.evals.scenarios.language_policy.scorer import tool_arg_no_cjk

    result = tool_arg_no_cjk(
        {
            "tool_outputs": [
                {
                    "tool": "finnhub_stock_quote",
                    "args": {"ticker": ticker},
                }
            ]
        },
        {"search_query_no_cjk": True, "tool": "finnhub_stock_quote"},
        input="What is the current price?",
    )

    assert result["score"] == expected_score


def test_tool_arg_no_cjk_skips_when_expected_flag_is_missing() -> None:
    from backend.evals.scenarios.language_policy.scorer import tool_arg_no_cjk

    result = tool_arg_no_cjk(
        {
            "tool_outputs": [
                {
                    "tool": "tavily_financial_search",
                    "args": {"query": "微軟最新新聞"},
                }
            ]
        },
        {"search_query_no_cjk": None, "tool": "tavily_financial_search"},
        input="微軟最近有什麼新聞？",
    )

    assert result["score"] == 1.0


def test_tool_arg_no_cjk_skips_when_expected_flag_is_false() -> None:
    from backend.evals.scenarios.language_policy.scorer import tool_arg_no_cjk

    result = tool_arg_no_cjk(
        {
            "tool_outputs": [
                {
                    "tool": "tavily_financial_search",
                    "args": {"query": "微軟最新新聞"},
                }
            ]
        },
        {"search_query_no_cjk": False, "tool": "tavily_financial_search"},
        input="微軟最近有什麼新聞？",
    )

    assert result["score"] == 1.0


def test_response_language_passes_when_cjk_ratio_in_range() -> None:
    from backend.evals.scenarios.language_policy.scorer import response_language

    result = response_language(
        {"response": "微軟近期表現穩定，整體趨勢偏正向。"},
        {"cjk_min": 0.2, "cjk_max": 1.0},
        input="微軟最近有什麼新聞？",
    )

    assert result["name"] == "response_language"
    assert result["score"] == 1.0


def test_response_language_fails_when_cjk_ratio_below_min() -> None:
    from backend.evals.scenarios.language_policy.scorer import response_language

    result = response_language(
        {"response": "Microsoft has been doing well lately."},
        {"cjk_min": 0.2, "cjk_max": 1.0},
        input="微軟最近有什麼新聞？",
    )

    assert result["score"] == 0.0
