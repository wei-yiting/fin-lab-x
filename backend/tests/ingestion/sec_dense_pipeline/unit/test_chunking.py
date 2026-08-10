"""Seam-2 unit tests: ParsedFiling → chunk payloads (pure, no Qdrant)."""

from typing import Any

import pytest

from backend.ingestion.sec_dense_pipeline.chunking import (
    build_chunk_payloads,
    chunk_point_id,
)
from backend.tests.ingestion.sec_dense_pipeline.conftest import (
    PRELUDE_TEXT,
    make_toy_filing,
)

EXPECTED_PAYLOAD_KEYS = {
    "ticker",
    "fiscal_year",
    "filing_date",
    "filing_type",
    "accession_number",
    "cik",
    "primary_document",
    "item",
    "block_heading",
    "prelude",
    "header_path",
    "chunk_index",
    "text",
}


@pytest.fixture(scope="module")
def payloads() -> list[dict[str, Any]]:
    return build_chunk_payloads(make_toy_filing())


def _of_block(payloads, item, heading):
    return [p for p in payloads if p["item"] == item and p["block_heading"] == heading]


def test_every_payload_has_full_field_set_including_citation(payloads) -> None:
    assert payloads, "toy filing produced no chunks"
    for p in payloads:
        assert set(p.keys()) == EXPECTED_PAYLOAD_KEYS
        assert p["ticker"] == "AAPL"
        assert p["fiscal_year"] == 2024
        assert p["filing_type"] == "10-K"
        assert p["accession_number"] == "0000320193-24-000123"
        assert p["cik"] == "320193"
        assert p["primary_document"] == "aapl-20240928.htm"


def test_prelude_attached_whole_to_every_chunk_of_its_item(payloads) -> None:
    item7 = [p for p in payloads if p["item"] == "7"]
    assert item7
    assert all(p["prelude"] == PRELUDE_TEXT for p in item7)


def test_prelude_is_none_for_flat_and_reclassified_items(payloads) -> None:
    for item_key in ("1a", "8"):
        chunks = [p for p in payloads if p["item"] == item_key]
        assert chunks
        assert all(p["prelude"] is None for p in chunks), (
            f"item {item_key}: schema has no valid prelude, payload must be None"
        )


def test_block_heading_is_none_for_flat_and_reclassified_leading_block(
    payloads,
) -> None:
    flat = [p for p in payloads if p["item"] == "8"]
    assert flat and all(p["block_heading"] is None for p in flat)

    # Reclassified leading block: schema heading "" → payload None; its text
    # is in the chunk flow.
    leading = _of_block(payloads, "1a", None)
    assert leading and all("charlie" in p["text"] for p in leading)
    headed = _of_block(payloads, "1a", "Competition")
    assert headed and all("delta" in p["text"] for p in headed)


def test_chunk_boundaries_never_cross_blocks(payloads) -> None:
    filing = make_toy_filing()
    block_texts = {
        ("7", "Results of Operations"): filing.items[0].blocks[0].text,
        ("7", "Liquidity and Capital Resources"): filing.items[0].blocks[1].text,
        ("1a", None): filing.items[1].blocks[0].text,
        ("1a", "Competition"): filing.items[1].blocks[1].text,
        ("8", None): filing.items[2].text,
    }
    for p in payloads:
        source = block_texts[(p["item"], p["block_heading"])]
        assert p["text"] in source, (
            f"chunk {p['chunk_index']} is not a contiguous span of its own "
            f"block ({p['item']} / {p['block_heading']})"
        )


def test_adjacent_chunks_within_a_block_overlap(payloads) -> None:
    block = _of_block(payloads, "7", "Results of Operations")
    assert len(block) >= 2, "block too small to exercise overlap"
    for prev, nxt in zip(block, block[1:]):
        prev_words = set(prev["text"].split())
        nxt_head = nxt["text"].split()[:3]
        # Tokens are unique across the block, so shared words prove overlap.
        assert prev_words.issuperset(nxt_head), (
            "adjacent chunks of the same block do not overlap"
        )


def test_chunk_index_is_filing_wide_and_gapless(payloads) -> None:
    assert [p["chunk_index"] for p in payloads] == list(range(len(payloads)))
    # Crosses item boundaries: the first chunk of item 1a continues the
    # numbering where item 7 stopped.
    item7_max = max(p["chunk_index"] for p in payloads if p["item"] == "7")
    item1a_min = min(p["chunk_index"] for p in payloads if p["item"] == "1a")
    assert item1a_min == item7_max + 1


def test_header_path_format_without_part_level(payloads) -> None:
    headed = _of_block(payloads, "7", "Results of Operations")[0]
    assert headed["header_path"] == (
        "AAPL / 2024 / Item 7. Management's Discussion and Analysis of "
        "Financial Condition and Results of Operations / Results of Operations"
    )
    flat = [p for p in payloads if p["item"] == "8"][0]
    assert flat["header_path"] == (
        "AAPL / 2024 / Item 8. Financial Statements and Supplementary Data"
    )
    leading = _of_block(payloads, "1a", None)[0]
    assert leading["header_path"] == "AAPL / 2024 / Item 1A. Risk Factors"
    for p in payloads:
        assert "Part" not in p["header_path"]


def test_ticker_is_canonicalized_into_payload_and_path(payloads) -> None:
    lowercase = build_chunk_payloads(make_toy_filing(ticker=" aapl "))
    assert lowercase[0]["ticker"] == "AAPL"
    assert lowercase[0]["header_path"].startswith("AAPL / 2024 / ")


def test_chunk_point_id_is_deterministic_and_index_scoped() -> None:
    assert chunk_point_id("AAPL", 2024, 0) == chunk_point_id("AAPL", 2024, 0)
    assert chunk_point_id("AAPL", 2024, 0) != chunk_point_id("AAPL", 2024, 1)
    assert chunk_point_id("AAPL", 2024, 0) != chunk_point_id("AAPL", 2023, 0)
