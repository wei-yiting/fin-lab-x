"""Unit tests for the HTML-vs-text parsing A/B analysis (DEV-138/183)."""

import json

import pytest

from backend.evals.experiments.parsing_ab.analyze import (
    bootstrap_mean_ci,
    breakdown,
    degraded_html_filings,
    expected_from_row,
    mcnemar_exact_p,
    paired_bootstrap_delta,
    row_buckets,
    row_id_for,
    score_arm,
    snippet_only_rank,
    snippet_recall_summary,
    summarize_arms,
)

ITEM_7 = (
    "NVDA / 2026 / Item 7. Management's Discussion and Analysis of "
    "Financial Condition and Results of Operations"
)
SNIPPET = "We invested $17.5 billion in private companies and infrastructure funds."


def _row(**overrides: str) -> dict[str, str]:
    row = {
        "question": "How much did NVIDIA invest in private companies?",
        "expected_header_paths": json.dumps([ITEM_7]),
        "answer_snippets": json.dumps([SNIPPET]),
        "expected_tickers": json.dumps(["NVDA"]),
        "query_type": "factoid",
        "detection_source": json.dumps(["markdown_h3"]),
        "fiscal_year": "2026",
    }
    row.update(overrides)
    return row


def _text_chunk(header_path: str, text: str) -> dict:
    return {"header_path": header_path, "text": text, "item": "7"}


def _html_chunk(header_path: str, text: str, item: str = "Item 7") -> dict:
    return {
        "ticker": "NVDA",
        "year": 2026,
        "item": item,
        "header_path": header_path,
        "text": text,
    }


class TestExpectedFromRow:
    def test_parses_index_aligned_json_lists(self) -> None:
        expected = expected_from_row(_row())
        assert expected == {"header_paths": [ITEM_7], "answer_snippets": [SNIPPET]}


class TestScoreArm:
    def test_text_arm_hit_at_rank_two(self) -> None:
        chunks = [
            _text_chunk(ITEM_7, "unrelated text"),
            _text_chunk(ITEM_7 + " / Overview", "Intro. " + SNIPPET + " More."),
        ]
        scores = score_arm("text", chunks, expected_from_row(_row()))
        assert scores == {
            "rank": 2,
            "recall_at_5": 1.0,
            "recall_at_10": 1.0,
            "mrr": 0.5,
        }

    def test_text_arm_miss(self) -> None:
        chunks = [_text_chunk(ITEM_7, "unrelated text")]
        scores = score_arm("text", chunks, expected_from_row(_row()))
        assert scores == {
            "rank": None,
            "recall_at_5": 0.0,
            "recall_at_10": 0.0,
            "mrr": 0.0,
        }

    def test_html_arm_goes_through_compat_wrapper(self) -> None:
        # Part segment + curly apostrophe: only a hit after normalize_chunks.
        raw_path = (
            "NVDA / 2026 / Part II / Item 7. Management’s Discussion and "
            "Analysis of Financial Condition and Results of Operations"
        )
        chunks = [_html_chunk(raw_path, SNIPPET)]
        scores = score_arm("html", chunks, expected_from_row(_row()))
        assert scores["rank"] == 1

    def test_rank_six_counts_for_recall_at_10_only(self) -> None:
        chunks = [_text_chunk(ITEM_7, "noise")] * 5 + [_text_chunk(ITEM_7, SNIPPET)]
        scores = score_arm("text", chunks, expected_from_row(_row()))
        assert scores["recall_at_5"] == 0.0
        assert scores["recall_at_10"] == 1.0
        assert scores["mrr"] == pytest.approx(1 / 6)

    def test_unknown_arm_rejected(self) -> None:
        with pytest.raises(ValueError):
            score_arm("pdf", [], expected_from_row(_row()))


class TestSnippetOnlyRank:
    def test_ignores_header_path(self) -> None:
        chunks = [
            _text_chunk("NVDA / 2026 / Item 1A. Risk Factors", "noise"),
            _text_chunk("NVDA / 2026 / Item 1A. Risk Factors", SNIPPET.upper()),
        ]
        assert snippet_only_rank(chunks, expected_from_row(_row())) == 2

    def test_none_when_no_chunk_contains_any_snippet(self) -> None:
        chunks = [_text_chunk(ITEM_7, "noise")]
        assert snippet_only_rank(chunks, expected_from_row(_row())) is None


class TestRowBuckets:
    def test_detection_path_is_the_set_of_listed_sources(self) -> None:
        row = _row(detection_source=json.dumps(["markdown_h4", "flat", "markdown_h4"]))
        assert row_buckets(row, "detection_source") == ["flat", "markdown_h4"]

    def test_scalar_column(self) -> None:
        assert row_buckets(_row(), "query_type") == ["factoid"]


class TestBootstrap:
    def test_mean_ci_is_deterministic_and_brackets_point(self) -> None:
        values = [1.0, 0.0, 1.0, 1.0, 0.0, 1.0, 1.0, 0.0, 1.0, 1.0]
        first = bootstrap_mean_ci(values)
        second = bootstrap_mean_ci(values)
        assert first == second
        point, lo, hi = first
        assert point == pytest.approx(0.7)
        assert lo <= point <= hi
        assert 0.0 <= lo < hi <= 1.0

    def test_constant_values_have_zero_width_ci(self) -> None:
        assert bootstrap_mean_ci([1.0] * 8) == (1.0, 1.0, 1.0)

    def test_paired_delta_resamples_rows_jointly(self) -> None:
        # Identical arms: every resample's delta is exactly zero.
        html = [1.0, 0.0, 0.5, 1.0]
        assert paired_bootstrap_delta(html, list(html)) == (0.0, 0.0, 0.0)

    def test_paired_delta_sign_is_text_minus_html(self) -> None:
        html = [0.0] * 10
        text = [1.0] * 10
        assert paired_bootstrap_delta(html, text) == (1.0, 1.0, 1.0)

    def test_paired_delta_requires_equal_length(self) -> None:
        with pytest.raises(ValueError):
            paired_bootstrap_delta([1.0], [1.0, 0.0])


class TestMcNemar:
    def test_no_discordant_pairs_is_p_one(self) -> None:
        assert mcnemar_exact_p(0, 0) == 1.0

    def test_symmetric_split_is_p_one(self) -> None:
        assert mcnemar_exact_p(3, 3) == 1.0

    def test_lopsided_split(self) -> None:
        # Two-sided exact binomial, n=6, k=0: 2 * 0.5**6.
        assert mcnemar_exact_p(0, 6) == pytest.approx(2 * 0.5**6)


class TestSummaries:
    def _records(self) -> list[dict]:
        return [
            {
                "row_id": "r1",
                "query_type": ["factoid"],
                "detection_source": ["markdown_h3"],
                "html": {"recall_at_5": 1.0, "recall_at_10": 1.0, "mrr": 1.0},
                "text": {"recall_at_5": 1.0, "recall_at_10": 1.0, "mrr": 0.5},
            },
            {
                "row_id": "r2",
                "query_type": ["passage"],
                "detection_source": ["markdown_h3", "flat"],
                "html": {"recall_at_5": 0.0, "recall_at_10": 0.0, "mrr": 0.0},
                "text": {"recall_at_5": 1.0, "recall_at_10": 1.0, "mrr": 1.0},
            },
        ]

    def test_summarize_arms_reports_means_and_paired_delta(self) -> None:
        summary = summarize_arms(self._records())
        r5 = summary["recall_at_5"]
        assert r5["n"] == 2
        assert r5["html"][0] == pytest.approx(0.5)
        assert r5["text"][0] == pytest.approx(1.0)
        assert r5["delta"][0] == pytest.approx(0.5)
        assert r5["text_only_hits"] == 1
        assert r5["html_only_hits"] == 0
        assert r5["mcnemar_p"] == pytest.approx(1.0)
        assert summary["mrr"]["delta"][0] == pytest.approx(0.25)

    def test_breakdown_counts_a_row_in_every_bucket_it_touches(self) -> None:
        table = breakdown(self._records(), "detection_source", "recall_at_5")
        by_bucket = {entry["bucket"]: entry for entry in table}
        assert by_bucket["markdown_h3"]["n"] == 2
        assert by_bucket["flat"]["n"] == 1
        assert by_bucket["flat"]["html"] == 0.0
        assert by_bucket["flat"]["text"] == 1.0


class TestRowId:
    def test_prefers_candidate_id_from_the_curated_dataset(self) -> None:
        assert row_id_for(_row(candidate_id="n10"), 3) == "n10"

    def test_falls_back_to_position(self) -> None:
        assert row_id_for(_row(), 3) == "row03"


class TestDegradedHtmlFilings:
    def test_flags_tickers_whose_html_chunks_are_mostly_unlabelled(self) -> None:
        manifest = {
            "filings": {
                "COST/2025": {"html": {"chunks": 10, "items": {"_unknown": 10}}},
                "NVDA/2026": {"html": {"chunks": 10, "items": {"_unknown": 1}}},
                "JPM/2025": {"html": {"chunks": 10, "items": {"_unknown": 5}}},
            }
        }
        assert degraded_html_filings(manifest) == ["COST", "JPM"]


class TestSnippetRecallSummary:
    def test_counts_snippet_rank_within_ten_regardless_of_label(self) -> None:
        records = [
            {"html": {"snippet_rank": 3}, "text": {"snippet_rank": 1}},
            {"html": {"snippet_rank": None}, "text": {"snippet_rank": 11}},
        ]
        summary = snippet_recall_summary(records)
        assert summary["html"][0] == pytest.approx(0.5)
        assert summary["text"][0] == pytest.approx(0.5)
        assert summary["delta"][0] == pytest.approx(0.0)
