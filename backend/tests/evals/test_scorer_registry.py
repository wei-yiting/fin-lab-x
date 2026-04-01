"""Tests for scorer registry resolution and language policy scorers."""

from typing import Any

import pytest

from backend.evals.eval_spec_schema import ScorerConfig


def test_resolve_scorers_resolves_programmatic_dotpath() -> None:
    from backend.evals.scorer_registry import resolve_scorers
    from backend.evals.scorers.language_policy_scorer import tool_arg_no_cjk

    scorers = resolve_scorers(
        [
            ScorerConfig(
                name="tool_arg_no_cjk",
                function="backend.evals.scorers.language_policy_scorer.tool_arg_no_cjk",
            )
        ]
    )

    assert len(scorers) == 1
    assert scorers[0] is tool_arg_no_cjk


def test_resolve_scorers_raises_import_error_for_missing_module() -> None:
    from backend.evals.scorer_registry import resolve_scorers

    scorer_config = ScorerConfig.model_construct(
        name="missing_module",
        function="backend.evals.scorers.missing_module.tool_arg_no_cjk",
    )

    with pytest.raises(ImportError, match="backend\\.evals\\.scorers\\.missing_module"):
        resolve_scorers([scorer_config])


def test_resolve_scorers_raises_import_error_for_missing_function() -> None:
    from backend.evals.scorer_registry import resolve_scorers

    scorer_config = ScorerConfig.model_construct(
        name="missing_function",
        function="backend.evals.scorers.language_policy_scorer.missing_function",
    )

    with pytest.raises(
        ImportError, match="missing_function"
    ):
        resolve_scorers([scorer_config])


def test_resolve_scorers_builds_llm_classifier(monkeypatch: pytest.MonkeyPatch) -> None:
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
        ) -> None:
            captured["name"] = name
            captured["prompt_template"] = prompt_template
            captured["choice_scores"] = choice_scores
            captured["use_cot"] = use_cot
            captured["model"] = model

    monkeypatch.setattr(scorer_registry, "LLMClassifier", FakeLLMClassifier)

    scorer_config = ScorerConfig(
        name="judge_score",
        type="llm_judge",
        rubric="Judge whether the answer follows the policy.",
        model="gpt-4.1",
        use_cot=True,
        choice_scores={"Y": 1.0, "N": 0.0},
    )

    scorers = scorer_registry.resolve_scorers([scorer_config])

    assert len(scorers) == 1
    assert callable(scorers[0])
    assert captured == {
        "name": "judge_score",
        "prompt_template": "Judge whether the answer follows the policy.",
        "choice_scores": {"Y": 1.0, "N": 0.0},
        "use_cot": True,
        "model": "gpt-4.1",
    }


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
    from backend.evals.scorers.language_policy_scorer import tool_arg_no_cjk

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


def test_tool_arg_no_cjk_fails_for_cjk_arguments() -> None:
    from backend.evals.scorers.language_policy_scorer import tool_arg_no_cjk

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
    from backend.evals.scorers.language_policy_scorer import tool_arg_no_cjk

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
    from backend.evals.scorers.language_policy_scorer import tool_arg_no_cjk

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
    from backend.evals.scorers.language_policy_scorer import tool_arg_no_cjk

    result = tool_arg_no_cjk(
        {
            "tool_outputs": [
                {
                    "tool": "yfinance_stock_quote",
                    "args": {"ticker": ticker},
                }
            ]
        },
        {"search_query_no_cjk": True, "tool": "yfinance_stock_quote"},
        input="What is the current price?",
    )

    assert result["score"] == expected_score


def test_tool_arg_no_cjk_skips_when_expected_flag_is_missing() -> None:
    from backend.evals.scorers.language_policy_scorer import tool_arg_no_cjk

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
    from backend.evals.scorers.language_policy_scorer import tool_arg_no_cjk

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
    from backend.evals.scorers.language_policy_scorer import response_language

    result = response_language(
        {"response": "微軟近期表現穩定，整體趨勢偏正向。"},
        {"cjk_min": 0.2, "cjk_max": 1.0},
        input="微軟最近有什麼新聞？",
    )

    assert result["name"] == "response_language"
    assert result["score"] == 1.0


def test_response_language_fails_when_cjk_ratio_below_min() -> None:
    from backend.evals.scorers.language_policy_scorer import response_language

    result = response_language(
        {"response": "Microsoft has been doing well lately."},
        {"cjk_min": 0.2, "cjk_max": 1.0},
        input="微軟最近有什麼新聞？",
    )

    assert result["score"] == 0.0
