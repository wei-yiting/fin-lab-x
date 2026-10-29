"""Regression checks for the second human-review surface."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from backend.evals.scenarios.sec_retrieval_ab.curation.round2_review_assembler import (
    REVIEW_COLUMNS,
    assemble_review_artifacts,
    build_review_rows,
)


REPO_ROOT = Path(__file__).parents[3]
CURATION_DIR = REPO_ROOT / "backend/evals/scenarios/sec_retrieval_ab/curation"


def test_review_rows_preserve_round1_context_and_leave_human_fields_blank() -> None:
    rows = build_review_rows(CURATION_DIR)

    assert len(rows) == 55
    assert [row["review_scope"] for row in rows].count("active") == 41
    assert [row["review_scope"] for row in rows].count("active_new") == 10
    assert [row["review_scope"] for row in rows].count("reference_only") == 4
    assert [row["round1_decision"] for row in rows[:13]] == ["o"] * 13
    assert [row["round1_decision"] for row in rows[13:41]] == ["?"] * 28
    assert [row["candidate_id"] for row in rows[41:51]] == [
        f"n{index:02d}" for index in range(1, 11)
    ]
    assert [row["round1_decision"] for row in rows[51:]] == ["!", "x", "x", "x"]
    assert all(row["round2_decision"] == "" for row in rows)
    assert all(row["round2_reviewer_comment"] == "" for row in rows)
    assert all(row["round2_query_type"] != "multi_passage" for row in rows[:51])
    assert all(row["answer_requirement"] for row in rows[:51])

    p17 = next(row for row in rows if row["candidate_id"] == "p17")
    assert p17["round1_reviewer_comment"]
    assert p17["round1_question"] != p17["round2_question"]
    assert p17["acceptable_occurrence_count"] == "3"

    n01 = next(row for row in rows if row["candidate_id"] == "n01")
    assert n01["round1_question"] == ""
    assert n01["round1_decision"] == ""


def test_every_multi_occurrence_candidate_has_a_completed_t6_audit() -> None:
    audited_candidates = 0
    audited_occurrences = 0

    for result_path in sorted((CURATION_DIR / "round2_ticker_results").glob("T*.json")):
        result = json.loads(result_path.read_text())
        for candidate in result["candidate_results"]:
            occurrences = candidate["acceptable_occurrences"]
            if len(occurrences) < 2:
                continue
            audited_candidates += 1
            audited_occurrences += len(occurrences)
            audit = candidate["round3_reconciliation"]["t6"]
            assert audit["status"] == "verified"
            assert audit["removed_occurrences"] == []
            assert audit["kept_occurrence_ids"] == [
                occurrence["occurrence_id"] for occurrence in occurrences
            ]

    assert audited_candidates == 17
    assert audited_occurrences == 41


def test_review_column_order_places_candidate_id_before_blank_review_fields() -> None:
    assert REVIEW_COLUMNS[-3:] == [
        "candidate_id",
        "round2_decision",
        "round2_reviewer_comment",
    ]


def test_assembler_emits_one_csv_row_per_candidate_and_expanded_markdown(
    tmp_path: Path,
) -> None:
    csv_path = tmp_path / "round2_review.csv"
    markdown_path = tmp_path / "round2_review.md"

    assemble_review_artifacts(CURATION_DIR, csv_path, markdown_path)

    with csv_path.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    markdown = markdown_path.read_text()

    assert list(rows[0]) == REVIEW_COLUMNS
    assert len(rows) == 55
    assert markdown.count("## Candidate ") == 55
    assert "51 active candidates" in markdown
    assert "OR alternative" in markdown
    assert "Round-1 reviewer comment" in markdown
    assert "`round2_decision`: _(blank)_" in markdown
    assert "`round2_reviewer_comment`: _(blank)_" in markdown
