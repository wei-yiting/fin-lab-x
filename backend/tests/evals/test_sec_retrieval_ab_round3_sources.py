"""Regression checks for Round 3 filing-store source reconciliation."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import tiktoken


REPO_ROOT = Path(__file__).parents[3]
RESULTS_DIR = REPO_ROOT / (
    "backend/evals/scenarios/sec_retrieval_ab/curation/round2_ticker_results"
)
PENDING_TABLE_REBUILDS: set[str] = set()
EXPECTED_T2_ACTIONS = {
    "CAT-2025-409946": "dropped_item_8_duplicate",
    "AXON-2025-355627": "dropped_item_8",
    "COIN-2025-515508": "dropped_item_8",
    "DDOG-2025-286123": "dropped_item_8",
    "DDOG-2025-323068": "dropped_item_8",
    "DECK-2026-238856": "dropped_item_8",
    "GOOGL-2025-284798": "dropped_item_8",
    "GOOGL-2025-281729": "dropped_item_8_duplicate",
    "LIN-2025-161275": "dropped_item_8",
    "LIN-2025-320932": "dropped_item_8",
    "NVDA-2026-337687": "relabelled_store_item",
    "PLD-2025-336753": "relabelled_store_item_and_reanchored",
    "PLD-2025-348730": "relabelled_store_item",
    "PODD-2025-255412": "dropped_item_8",
}


def _store_units(filing: dict[str, Any]) -> Iterator[dict[str, Any]]:
    for item in filing["items"]:
        item_key = str(item["item"]).lower()
        if item["kind"] == "structured":
            if prelude := item.get("prelude"):
                yield {
                    "item": item_key,
                    "unit_kind": "prelude",
                    "block_index": None,
                    "block_heading": None,
                    "text": prelude,
                }
            for block_index, block in enumerate(item.get("blocks", [])):
                yield {
                    "item": item_key,
                    "unit_kind": "structured_block",
                    "block_index": block_index,
                    "block_heading": block.get("heading"),
                    "text": block.get("text", ""),
                }
        else:
            yield {
                "item": item_key,
                "unit_kind": "flat_item",
                "block_index": None,
                "block_heading": None,
                "text": item.get("text", ""),
            }


def _item_hint(value: str) -> str:
    match = re.search(r"Item\s+(\d+[A-Za-z]?)", value, re.IGNORECASE)
    assert match is not None, value
    return match.group(1).lower()


def test_round3_sources_are_store_exact_and_exclude_item_8() -> None:
    encoding = tiktoken.get_encoding("cl100k_base")
    observed_pending_rebuilds: set[str] = set()

    for result_path in sorted(RESULTS_DIR.glob("*.json")):
        result = json.loads(result_path.read_text())
        store_path = (
            REPO_ROOT
            / "data/sec_text"
            / result["ticker"]
            / "10-K"
            / f"{result['fiscal_year']}.json"
        )
        units = list(_store_units(json.loads(store_path.read_text())))
        actual_occurrence_count = 0

        for candidate in result["candidate_results"]:
            occurrences = candidate.get("acceptable_occurrences", [])
            assert occurrences, candidate["candidate_id"]
            actual_occurrence_count += len(occurrences)

            for occurrence in occurrences:
                item = _item_hint(occurrence["item_hint"])
                assert item != "8", occurrence["occurrence_id"]
                assert 50 <= len(occurrence["answer_snippet"]) <= 200
                assert occurrence["answer_snippet"] in occurrence["answer_span"]
                assert len(encoding.encode(occurrence["answer_span"])) <= 300

                exact_units = [
                    unit
                    for unit in units
                    if unit["item"] == item
                    and occurrence["answer_span"].casefold() in unit["text"].casefold()
                    and occurrence["answer_snippet"].casefold()
                    in unit["text"].casefold()
                ]
                if occurrence["occurrence_id"] in PENDING_TABLE_REBUILDS:
                    observed_pending_rebuilds.add(occurrence["occurrence_id"])
                    assert not exact_units
                else:
                    assert exact_units, occurrence["occurrence_id"]

        assert (
            result["result_summary"]["acceptable_occurrence_count"]
            == actual_occurrence_count
        )

    assert observed_pending_rebuilds == PENDING_TABLE_REBUILDS


def test_round3_store_anchors_resolve_to_the_current_exact_strings() -> None:
    anchored_occurrence_count = 0

    for result_path in sorted(RESULTS_DIR.glob("*.json")):
        result = json.loads(result_path.read_text())
        store_path = (
            REPO_ROOT
            / "data/sec_text"
            / result["ticker"]
            / "10-K"
            / f"{result['fiscal_year']}.json"
        )
        units = list(_store_units(json.loads(store_path.read_text())))

        for candidate in result["candidate_results"]:
            for occurrence in candidate.get("acceptable_occurrences", []):
                if not (anchor := occurrence.get("store_anchor")):
                    continue
                anchored_occurrence_count += 1
                matching_units = [
                    unit
                    for unit in units
                    if unit["item"] == anchor["item"].lower()
                    and unit["unit_kind"] == anchor["unit_kind"]
                    and unit["block_index"] == anchor["block_index"]
                    and unit["block_heading"] == anchor["block_heading"]
                ]
                assert len(matching_units) == 1, occurrence["occurrence_id"]
                text = matching_units[0]["text"]
                span = text[anchor["span_start"] : anchor["span_end"]]
                snippet = text[anchor["snippet_start"] : anchor["snippet_end"]]
                assert span == occurrence["answer_span"]
                assert snippet == occurrence["answer_snippet"]
                assert (
                    hashlib.sha256(span.encode()).hexdigest() == anchor["span_sha256"]
                )
                assert (
                    hashlib.sha256(snippet.encode()).hexdigest()
                    == anchor["snippet_sha256"]
                )

    assert anchored_occurrence_count == 24


def test_jpm_n10_enumerates_store_exact_var_table_copies() -> None:
    result = json.loads((RESULTS_DIR / "T09_JPM.json").read_text())
    filing = json.loads((REPO_ROOT / "data/sec_text/JPM/10-K/2025.json").read_text())
    units = list(_store_units(filing))
    candidate = next(
        candidate
        for candidate in result["candidate_results"]
        if candidate["candidate_id"] == "n10"
    )
    occurrences = candidate["acceptable_occurrences"]

    assert len(occurrences) == 2
    assert {occurrence["item_hint"] for occurrence in occurrences} == {
        "Item 1",
        "Item 15",
    }
    assert len({occurrence["answer_snippet"] for occurrence in occurrences}) == 1

    snippet = occurrences[0]["answer_snippet"]
    assert len(snippet) == 151
    for risk_type in (
        "Fixed income",
        "Foreign exchange",
        "Equities",
        "Commodities and other",
    ):
        assert risk_type in snippet
    assert snippet.startswith("CIB trading VaR by risk type")
    assert sum(unit["text"].count(snippet) for unit in units) == 2

    reconciliation = candidate["round3_reconciliation"]["t3"]
    assert reconciliation == [
        {
            "action": "reanchored_table_and_enumerated_store_copies",
            "original_occurrence_id": "JPM-2025-504303",
            "canonical_item_hint": "Item 7A",
            "store_locations": [
                "Item 1 / Segment & Corporate Results – Managed Basis / "
                "chars 239167-239318",
                "Item 15 / Segment & Corporate Results – Managed Basis / "
                "chars 239167-239318",
            ],
            "reason": (
                "The canonical table linearization did not exact-match the filing "
                "store. The store has two non-Item-8 copies of the same source "
                "table, so both store-exact locations are enumerated; cross-arm "
                "header-path reconciliation remains outside this task."
            ),
        }
    ]


def test_lin_a16_has_independently_sufficient_store_exact_or_alternatives() -> None:
    result = json.loads((RESULTS_DIR / "T10_LIN.json").read_text())
    filing = json.loads((REPO_ROOT / "data/sec_text/LIN/10-K/2025.json").read_text())
    units = list(_store_units(filing))
    candidate = next(
        candidate
        for candidate in result["candidate_results"]
        if candidate["candidate_id"] == "a16"
    )
    occurrences = candidate["acceptable_occurrences"]

    assert candidate["proposal"]["question"] == (
        "How did currency translation affect Linde's APAC sales in 2025?"
    )
    assert len(occurrences) == 2
    assert {
        occurrence["store_anchor"]["block_heading"] for occurrence in occurrences
    } == {"APAC"}

    table, narrative = occurrences
    assert "Factors Contributing to Changes - Sales" in table["answer_snippet"]
    assert "Currency(1)%" in table["answer_snippet"]
    assert narrative["answer_snippet"].startswith(
        "Currency translation decreased sales by 1%"
    )
    for occurrence in occurrences:
        assert occurrence["exact_occurrences_in_store"] == 1
        assert (
            sum(unit["text"].count(occurrence["answer_snippet"]) for unit in units) == 1
        )

    assert [
        action["action"] for action in candidate["round3_reconciliation"]["t3"]
    ] == ["reanchored_store_table", "verified_store_exact"]


def test_pld_p48_item16_span_preserves_year_context() -> None:
    result = json.loads((RESULTS_DIR / "T14_PLD.json").read_text())
    candidate = next(
        candidate
        for candidate in result["candidate_results"]
        if candidate["candidate_id"] == "p48"
    )
    item16 = next(
        occurrence
        for occurrence in candidate["acceptable_occurrences"]
        if occurrence["item_hint"] == "Item 16"
    )

    assert "2025\n\n         2024\n\n         2023" in item16["answer_span"]
    assert "Preferred Stock – Series Q:" in item16["answer_span"]
    assert item16["span_cl100k_tokens"] == 247
    assert len(item16["answer_snippet"]) == 95


def test_every_non_item8_store_copy_is_enumerated_in_its_or_set() -> None:
    store_units: list[dict[str, Any]] = []
    listed_snippets: list[str] = []

    for result_path in sorted(RESULTS_DIR.glob("*.json")):
        result = json.loads(result_path.read_text())
        filing = json.loads(
            (
                REPO_ROOT
                / "data/sec_text"
                / result["ticker"]
                / "10-K"
                / f"{result['fiscal_year']}.json"
            ).read_text()
        )
        store_units.extend(unit for unit in _store_units(filing) if unit["item"] != "8")
        listed_snippets.extend(
            occurrence["answer_snippet"]
            for candidate in result["candidate_results"]
            for occurrence in candidate["acceptable_occurrences"]
        )

    for snippet in set(listed_snippets):
        folded = snippet.casefold()
        reachable_count = sum(
            unit["text"].casefold().count(folded) for unit in store_units
        )
        listed_count = sum(listed.casefold() == folded for listed in listed_snippets)
        assert reachable_count == listed_count, snippet


def test_round3_item_8_reconciliation_is_complete_and_provenanced() -> None:
    observed_actions: dict[str, str] = {}
    surviving_occurrence_ids: set[str] = set()

    for result_path in sorted(RESULTS_DIR.glob("*.json")):
        result = json.loads(result_path.read_text())
        for candidate in result["candidate_results"]:
            surviving_occurrence_ids.update(
                occurrence["occurrence_id"]
                for occurrence in candidate.get("acceptable_occurrences", [])
            )
            for record in candidate.get("round3_reconciliation", {}).get("t2", []):
                observed_actions[record["occurrence_id"]] = record["action"]
                assert record["label_escape_search"]
                assert record["reason"]

    assert observed_actions == EXPECTED_T2_ACTIONS
    for occurrence_id, action in EXPECTED_T2_ACTIONS.items():
        if action.startswith("dropped_item_8"):
            assert occurrence_id not in surviving_occurrence_ids
        else:
            assert occurrence_id in surviving_occurrence_ids
