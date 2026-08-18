"""Seam-2 unit tests: ParsedFiling → chunk payloads (pure, no Qdrant)."""

import pytest
import tiktoken

from backend.ingestion.sec_dense_pipeline.chunking import (
    ChunkPayload,
    build_chunk_payloads,
    chunk_point_id,
)
from backend.ingestion.sec_text_pipeline.filing_models import (
    Block,
    FlatItem,
    ParsedFiling,
    StructuredItem,
)
from backend.tests.ingestion.sec_dense_pipeline.conftest import (
    PRELUDE_TEXT,
    make_metadata,
    make_toy_filing,
    numbered_text,
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
def payloads() -> list[ChunkPayload]:
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


def test_prelude_attached_whole_to_every_block_chunk_of_its_item(payloads) -> None:
    item7_blocks = [
        p for p in payloads if p["item"] == "7" and p["block_heading"] is not None
    ]
    assert item7_blocks
    assert all(p["prelude"] == PRELUDE_TEXT for p in item7_blocks)


def test_valid_prelude_produces_its_own_searchable_leading_chunk(payloads) -> None:
    """The prelude enters the chunk flow itself — same path as FlatItem /
    reclassified leading blocks — so its content is searchable, not only
    payload metadata. Its own chunk carries prelude=None (it IS the prelude)."""
    item7 = [p for p in payloads if p["item"] == "7"]
    leading = _of_block(payloads, "7", None)
    assert leading, "valid prelude did not produce a leading chunk"
    assert " ".join(p["text"] for p in leading) == PRELUDE_TEXT
    assert all(p["prelude"] is None for p in leading)
    # Leading chunks come first within the item.
    max_leading_index = max(p["chunk_index"] for p in leading)
    min_block_index = min(
        p["chunk_index"] for p in item7 if p["block_heading"] is not None
    )
    assert max_leading_index < min_block_index


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
        ("7", None): filing.items[0].prelude,
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
    prelude_chunk = _of_block(payloads, "7", None)[0]
    assert prelude_chunk["header_path"] == (
        "AAPL / 2024 / Item 7. Management's Discussion and Analysis of "
        "Financial Condition and Results of Operations"
    )
    for p in payloads:
        assert "Part" not in p["header_path"]


@pytest.mark.parametrize("raw_item", ["7A", " 7a ", " 7A "])
def test_item_is_normalized_at_the_contract_boundary(raw_item: str) -> None:
    """Schema-valid item variants normalize to the lowercase stripped key.

    The payload `item` is an index/filter field, so mixed case or stray
    whitespace in the schema's unconstrained str must never leak into it;
    the display-layer header_path keeps the uppercase form.
    """
    filing = ParsedFiling(
        metadata=make_metadata(),
        items=[
            FlatItem(
                item=raw_item,
                title="Quantitative and Qualitative Disclosures About Market Risk",
                text=numbered_text("foxtrot", 50),
            )
        ],
    )
    result = build_chunk_payloads(filing)
    assert result
    assert all(p["item"] == "7a" for p in result)
    assert all(p["header_path"].startswith("AAPL / 2024 / Item 7A. ") for p in result)


def test_ticker_is_canonicalized_into_payload_and_path(payloads) -> None:
    lowercase = build_chunk_payloads(make_toy_filing(ticker=" aapl "))
    assert lowercase[0]["ticker"] == "AAPL"
    assert lowercase[0]["header_path"].startswith("AAPL / 2024 / ")


@pytest.mark.parametrize("empty_text", ["", "   ", "\n\n  \n"])
def test_empty_block_text_does_not_interrupt_chunk_flow(empty_text: str) -> None:
    """Schema allows Block(text="") — an empty block must yield zero chunks
    while its sibling blocks chunk normally with gapless filing-wide
    indices. The dangerous regression shape is the block loop stopping at
    the empty block: later content would silently vanish from the index
    while the commit marker still flips to complete (a false cache-hit no
    rerun would ever heal)."""
    filing = ParsedFiling(
        metadata=make_metadata(),
        items=[
            StructuredItem(
                item="7",
                title="Management's Discussion and Analysis",
                prelude="",
                blocks=[
                    Block(heading="Section A", text=numbered_text("golf", 200)),
                    Block(heading="Section B", text=empty_text),
                    Block(
                        heading="Section C",
                        text="UNIQUE_MARKER_C " + numbered_text("hotel", 100),
                    ),
                ],
                detection_source="markdown_h3",
            )
        ],
    )
    payloads = build_chunk_payloads(filing)

    assert any("UNIQUE_MARKER_C" in p["text"] for p in payloads), (
        "content after the empty block was dropped"
    )
    assert all(p["text"].strip() for p in payloads), (
        "an empty block must not produce empty chunk points"
    )
    assert [p["chunk_index"] for p in payloads] == list(range(len(payloads)))
    headings = {p["block_heading"] for p in payloads}
    assert "Section A" in headings and "Section C" in headings
    assert "Section B" not in headings


def test_block_at_exact_token_limit_yields_single_chunk() -> None:
    """Guards the token-based splitter configuration: a block of exactly
    512 cl100k_base tokens (far more than 512 characters) must stay one
    chunk. A character-based misconfiguration would shred it into several
    fragments — this boundary case is the only assertion that separates
    the two modes; every looser count-based test passes under both."""
    enc = tiktoken.get_encoding("cl100k_base")
    long_text = " ".join(
        f"financial results improved during fiscal year {i}" for i in range(200)
    )
    text = enc.decode(enc.encode(long_text)[:512])
    assert len(enc.encode(text)) == 512, "fixture must be exactly 512 tokens"
    assert len(text) > 512, "fixture must exceed 512 characters"

    filing = ParsedFiling(
        metadata=make_metadata(),
        items=[
            StructuredItem(
                item="7",
                title="Management's Discussion and Analysis",
                prelude="",
                blocks=[Block(heading="Only Block", text=text)],
                detection_source="markdown_h3",
            )
        ],
    )
    payloads = build_chunk_payloads(filing)

    assert len(payloads) == 1, (
        f"expected exactly 1 chunk for a 512-token block, got {len(payloads)} — "
        "splitter is likely counting characters instead of tokens"
    )
    assert payloads[0]["text"] == text


def test_chunk_point_id_is_deterministic_and_index_scoped() -> None:
    assert chunk_point_id("AAPL", 2024, 0) == chunk_point_id("AAPL", 2024, 0)
    assert chunk_point_id("AAPL", 2024, 0) != chunk_point_id("AAPL", 2024, 1)
    assert chunk_point_id("AAPL", 2024, 0) != chunk_point_id("AAPL", 2023, 0)
