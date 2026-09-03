"""Unit tests for language_policy programmatic scorers."""

import pytest
from autoevals import Score  # pyright: ignore[reportMissingImports]

from backend.evals.scenarios.language_policy.scorer import (
    expected_tool_called,
    response_no_simplified_chars,
)


class TestExpectedToolCalled:
    def test_declared_tool_called_scores_one(self) -> None:
        output = {
            "response": "MSFT had news today.",
            "tool_outputs": [
                {"tool": "tavily_financial_search", "args": {"query": "MSFT news"}}
            ],
        }
        expected = {"tool": "tavily_financial_search"}

        score = expected_tool_called(output, expected, input="any question")

        assert isinstance(score, Score)
        assert score.score == 1.0

    def test_declared_tool_called_among_others_scores_one(self) -> None:
        output = {
            "tool_outputs": [
                {"tool": "get_fundamentals", "args": {"ticker": "MSFT"}},
                {"tool": "tavily_financial_search", "args": {"query": "MSFT news"}},
            ],
        }
        expected = {"tool": "tavily_financial_search"}

        score = expected_tool_called(output, expected, input="any question")

        assert score is not None
        assert score.score == 1.0

    def test_declared_tool_not_called_scores_zero(self) -> None:
        """The mis-pass hole: zero tool calls must fail, not vacuously pass."""
        output = {"response": "MSFT is a large company.", "tool_outputs": []}
        expected = {"tool": "tavily_financial_search"}

        score = expected_tool_called(output, expected, input="any question")

        assert score is not None
        assert score.score == 0.0

    def test_different_tool_called_scores_zero(self) -> None:
        output = {
            "tool_outputs": [{"tool": "get_fundamentals", "args": {"ticker": "MSFT"}}],
        }
        expected = {"tool": "tavily_financial_search"}

        score = expected_tool_called(output, expected, input="any question")

        assert score is not None
        assert score.score == 0.0

    @pytest.mark.parametrize(
        "expected",
        [
            pytest.param({"cjk_min": 0.2}, id="no-tool-key"),
            pytest.param({"tool": None}, id="tool-is-none"),
            pytest.param({"tool": ""}, id="tool-is-empty-string"),
        ],
    )
    def test_undeclared_expect_tool_skips(self, expected: dict[str, object]) -> None:
        """A row with no expect_tool makes no claim — no-score, not a free pass.

        The CSV loader turns an empty expect_tool cell (e.g. LP-02) into None,
        so the empty-string form only reaches this scorer from non-CSV callers.
        """
        output = {"tool_outputs": [{"tool": "get_fundamentals", "args": {}}]}

        assert expected_tool_called(output, expected, input="any question") is None

    def test_malformed_output_scores_zero_when_declared(self) -> None:
        output = {"response": "no tool_outputs key at all"}
        expected = {"tool": "tavily_financial_search"}

        score = expected_tool_called(output, expected, input="any question")

        assert score is not None
        assert score.score == 0.0


class TestResponseNoSimplifiedChars:
    def test_pure_traditional_response_scores_one(self) -> None:
        output = {
            "response": "特斯拉這波利空到底比較像短期衝擊，還是已經傷到長期投資論點？"
        }
        expected = {"cjk_min": 0.20, "cjk_max": 1.0}

        score = response_no_simplified_chars(output, expected, input="any question")

        assert score is not None
        assert score.score == 1.0

    def test_fully_simplified_response_scores_zero(self) -> None:
        output = {
            "response": "特斯拉这波利空到底比较像短期冲击，还是已经伤到长期投资论点？"
        }
        expected = {"cjk_min": 0.20, "cjk_max": 1.0}

        score = response_no_simplified_chars(output, expected, input="any question")

        assert score is not None
        assert score.score == 0.0

    def test_partially_contaminated_response_scores_zero(self) -> None:
        """A response that is mostly Traditional but has a few Simplified
        characters slip in (the observed real-world failure mode) must still
        be caught, not diluted by the surrounding correct text."""
        output = {
            "response": "特斯拉這波利空到底比較像短期衝击，還是已經傷到長期投资論點？"
        }
        expected = {"cjk_min": 0.20, "cjk_max": 1.0}

        score = response_no_simplified_chars(output, expected, input="any question")

        assert score is not None
        assert score.score == 0.0

    def test_english_expected_row_skips(self) -> None:
        """cjk_min == 0 declares an English-expected row — script purity is
        not a claim this row makes, matching expected_tool_called's
        no-claim convention."""
        output = {"response": "MSFT is trading at $420."}
        expected = {"cjk_min": 0.0, "cjk_max": 0.02}

        assert (
            response_no_simplified_chars(output, expected, input="any question") is None
        )

    def test_missing_cjk_min_raises(self) -> None:
        output = {"response": "some response"}
        expected = {"cjk_max": 1.0}

        with pytest.raises(ValueError, match="requires cjk_min"):
            response_no_simplified_chars(output, expected, input="any question")

    def test_empty_response_scores_one(self) -> None:
        """Vacuous purity: no characters means no Simplified characters —
        consistent with other scorers here treating absence as a separate,
        orthogonal claim (response_language would separately fail this on
        CJK ratio)."""
        output = {"response": ""}
        expected = {"cjk_min": 0.20, "cjk_max": 1.0}

        score = response_no_simplified_chars(output, expected, input="any question")

        assert score is not None
        assert score.score == 1.0
