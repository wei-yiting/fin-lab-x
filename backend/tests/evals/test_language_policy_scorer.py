"""Unit tests for language_policy programmatic scorers."""

from autoevals import Score  # pyright: ignore[reportMissingImports]

from backend.evals.scenarios.language_policy.scorer import expected_tool_called


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

    def test_undeclared_expect_tool_skips(self) -> None:
        """A row with no expect_tool makes no claim — no-score, not a free pass."""
        output = {"tool_outputs": [{"tool": "get_fundamentals", "args": {}}]}
        expected = {"cjk_min": 0.2}

        assert expected_tool_called(output, expected, input="any question") is None

    def test_empty_expect_tool_skips(self) -> None:
        """CSV rows with an empty expect_tool cell (e.g. LP-02) also skip."""
        output = {"tool_outputs": []}
        expected = {"tool": ""}

        assert expected_tool_called(output, expected, input="any question") is None

    def test_malformed_output_scores_zero_when_declared(self) -> None:
        output = {"response": "no tool_outputs key at all"}
        expected = {"tool": "tavily_financial_search"}

        score = expected_tool_called(output, expected, input="any question")

        assert score is not None
        assert score.score == 0.0
