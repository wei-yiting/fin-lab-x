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

    def test_response_with_occasional_genuine_mistake_still_scores_one(self) -> None:
        """This scorer's job is to judge whether the response is written in
        the wrong language overall, not to guarantee zero wrong characters
        (a deliberate policy decision). A response that is mostly Traditional
        but has a couple of genuine Simplified characters slip in (2 of 28
        CJK characters here, a ~7% ratio, well under
        ``_MAX_SIMPLIFIED_RATIO``) is the kind of occasional mistake this
        scorer is designed to tolerate — this is intended tolerant-by-design
        behavior, not a dilution of a bug."""
        output = {
            "response": "特斯拉這波利空到底比較像短期衝击，還是已經傷到長期投资論點？"
        }
        expected = {"cjk_min": 0.20, "cjk_max": 1.0}

        score = response_no_simplified_chars(output, expected, input="any question")

        assert score is not None
        assert score.score == 1.0

    def test_absolute_floor_fails_despite_low_ratio(self) -> None:
        """Regression case for the absolute-count floor (``_MAX_GENUINE_CHANGES``):
        many common Chinese words are identical in Simplified and Traditional
        (股票, 成交量, 信心, ...), so a response can carry several genuine
        Simplified characters and still land under ``_MAX_SIMPLIFIED_RATIO``
        by ratio alone. This response has exactly 4 genuine (non-dual-status)
        Simplified characters — 说, 电, 现, 学 — scattered through an
        otherwise-long, correct Traditional response (4 of 57 CJK
        characters, a ~7% ratio, well under the 15% ratio threshold), so the
        ratio check alone would incorrectly pass it. The absolute floor (3)
        catches it independently of the ratio."""
        output = {
            "response": (
                "分析師針對特斯拉本季財報進行说明，並在电話會議中談到需求疲軟的现象，"
                "多數学者則持保留態度，但整體長期投資論點未受根本動搖。"
            )
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

    def test_taiwan_standard_response_with_tai_scores_one(self) -> None:
        """Regression case: 台 is legitimate standalone Taiwan-standard
        Traditional Chinese (台灣, 台積電 — a common company name in
        Traditional Chinese financial answers), but OpenCC's s2t table
        treats it as ambiguous and rewrites it to 臺 — the false positive
        this scorer must not reproduce."""
        output = {"response": "台積電目前的財務體質在台灣半導體產業中相對穩健。"}
        expected = {"cjk_min": 0.20, "cjk_max": 1.0}

        score = response_no_simplified_chars(output, expected, input="any question")

        assert score is not None
        assert score.score == 1.0

    def test_tai_allowance_does_not_mask_other_simplified_contamination(
        self,
    ) -> None:
        """The 台 dual-status allowance is narrowly scoped to that
        character: this response is wholesale Simplified (8 of 14 CJK
        characters changed, a ~57% ratio) and must still be caught, not
        accidentally excused by the legitimate 台 sitting alongside it."""
        output = {"response": "台积电目前的财务体质相对稳健。"}
        expected = {"cjk_min": 0.20, "cjk_max": 1.0}

        score = response_no_simplified_chars(output, expected, input="any question")

        assert score is not None
        assert score.score == 0.0

    @pytest.mark.parametrize(
        "response",
        [
            pytest.param("央行是否會干預匯市，市場高度關注。", id="gan-yu-intervene"),
            pytest.param("該公司公布財報後股價應聲上漲。", id="gongsi-gongbu-announce"),
            pytest.param(
                "市占率保持穩定，顯示競爭力未受影響。", id="shizhanlv-market-share"
            ),
            pytest.param("范先生針對此次併購案發表看法。", id="fan-xiansheng-surname"),
        ],
    )
    def test_other_dual_status_characters_score_one(self, response: str) -> None:
        """The systematically-derived dual-status exclusion set must cover
        more than just 台 — these are additional characters with the same
        ambiguity (干預, 公司公布財報, 市占率保持穩定, 范先生 all use a
        different dual-status character each). A naive single-character
        allowlist would miss all of these; deriving the full set from
        OpenCC's own dictionary catches them without hand-picking each one
        as it's discovered."""
        output = {"response": response}
        expected = {"cjk_min": 0.20, "cjk_max": 1.0}

        score = response_no_simplified_chars(output, expected, input="any question")

        assert score is not None
        assert score.score == 1.0
