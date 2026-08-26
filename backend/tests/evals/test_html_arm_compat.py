"""Unit tests for backend.evals.scenarios.sec_retrieval_ab.html_arm_compat.

Fixtures are real chunks recorded from the frozen HTML pipeline's Qdrant output
(backend/evals/regression/reference_measurements/sec_retrieval/2026-08-19_73faf5f.csv),
not invented strings — except the one test that exercises an item value never actually
observed in that data, which says so in its own docstring.
"""

from backend.evals.scenarios.sec_retrieval_ab.html_arm_compat import (
    normalize_chunk,
    normalize_chunks,
)


def test_normalize_chunk_passes_through_unchanged_when_item_is_unknown() -> None:
    """INTC/2025 chunk_index=134: the frozen pipeline's Part/Item anchor detection failed
    entirely for this chunk, so header_path is a bare 'TICKER / YEAR' with no Item segment.
    """
    chunk = {
        "ticker": "INTC",
        "year": 2025,
        "filing_date": "2026-01-23",
        "filing_type": "10-K",
        "accession_number": "0000050863-26-000011",
        "item": "_unknown",
        "header_path": "INTC / 2025",
        "chunk_index": 134,
        "text": "We are subject to numerous risks associated with the evolving market "
        "for products with AI capabilities.",
        "ingested_at": "2026-08-19T11:27:39.553783+00:00",
        "score": 0.5,
    }

    assert normalize_chunk(chunk) == chunk


def test_normalize_chunks_maps_normalize_chunk_over_a_list() -> None:
    """normalize_chunks is the list-shaped entry point that feeds
    output["retrieved_chunks"] directly to the unmodified sec_retrieval scorer functions.
    """
    unknown_chunk = {
        "ticker": "INTC",
        "year": 2025,
        "item": "_unknown",
        "header_path": "INTC / 2025",
        "chunk_index": 134,
        "text": "We are subject to numerous risks associated with the evolving market "
        "for products with AI capabilities.",
    }
    known_chunk = {
        "ticker": "NVDA",
        "year": 2026,
        "item": "Item 1",
        "header_path": "NVDA / 2026 / Part I / Item 1. Business",
        "chunk_index": 25,
        "text": "In addition to controls targeting D:1, D:4 and D:5 countries, the USG has "
        "also imposed worldwide export controls impacting our products, and may impose "
        "additional controls in the future.",
    }

    result = normalize_chunks([unknown_chunk, known_chunk])

    assert result == [
        unknown_chunk,
        {**known_chunk, "header_path": "NVDA / 2026 / Item 1. Business"},
    ]


def test_normalize_chunk_drops_part_segment_when_title_already_matches_canonical() -> (
    None
):
    """NVDA/2026 chunk_index=25: Item 1's live-extracted title happens to already match the
    canonical TENK_STANDARD_TITLES value, isolating the Part-removal behavior on its own.
    """
    chunk = {
        "ticker": "NVDA",
        "year": 2026,
        "filing_date": "2026-02-25",
        "filing_type": "10-K",
        "accession_number": "0001045810-26-000021",
        "item": "Item 1",
        "header_path": "NVDA / 2026 / Part I / Item 1. Business",
        "chunk_index": 25,
        "text": "In addition to controls targeting D:1, D:4 and D:5 countries, the USG has "
        "also imposed worldwide export controls impacting our products, and may impose "
        "additional controls in the future.",
        "ingested_at": "2026-08-19T11:27:39.553783+00:00",
        "score": 0.6,
    }

    normalized = normalize_chunk(chunk)

    assert normalized == {**chunk, "header_path": "NVDA / 2026 / Item 1. Business"}


def test_normalize_chunk_replaces_curly_apostrophe_title_with_canonical_straight_form() -> (
    None
):
    """AMD/2025 chunk_index=152: the pipeline's live-extracted title uses a curly apostrophe
    (U+2019) in "Management's"; TENK_STANDARD_TITLES uses a straight one (U+0027). A
    string-repair approach would need to special-case this per divergent chunk — rebuilding
    from the canonical title sidesteps it entirely.
    """
    chunk = {
        "ticker": "AMD",
        "year": 2025,
        "filing_date": "2026-02-04",
        "filing_type": "10-K",
        "accession_number": "0000002488-26-000018",
        "item": "Item 7",
        "header_path": (
            "AMD / 2025 / Part II / Item 7. Management’s Discussion and Analysis "
            "of Financial Condition and Results of Operations / Overview"
        ),
        "chunk_index": 152,
        "text": "### Overview\n\nIn 2025, we delivered strong annual revenue growth with net "
        "revenue increasing 34% to $34.6 billion, compared to $25.8 billion in 2024.",
        "ingested_at": "2026-08-19T11:27:39.553783+00:00",
        "score": 0.55,
    }

    normalized = normalize_chunk(chunk)

    assert normalized == {
        **chunk,
        "header_path": (
            "AMD / 2025 / Item 7. Management's Discussion and Analysis "
            "of Financial Condition and Results of Operations / Overview"
        ),
    }


def test_normalize_chunk_replaces_wording_divergent_title_with_canonical_form() -> None:
    """NVDA/2026 chunk_index=308: the pipeline's live-extracted title for Item 15 reads
    "Exhibits and Financial Statement Schedules"; TENK_STANDARD_TITLES reads "Exhibits,
    Financial Statement Schedules" (comma, not "and"). A different divergence shape than
    the apostrophe-encoding case above — same rebuild handles both without special-casing.
    """
    chunk = {
        "ticker": "NVDA",
        "year": 2026,
        "filing_date": "2026-02-25",
        "filing_type": "10-K",
        "accession_number": "0001045810-26-000021",
        "item": "Item 15",
        "header_path": "NVDA / 2026 / Part IV / Item 15. Exhibits and Financial Statement Schedules",
        "chunk_index": 308,
        "text": "(2)In fiscal year 2026, we estimate 76% of Data Center revenue from "
        "Taiwan-headquartered customers was attributed to end customers based in the "
        "United States and Europe.",
        "ingested_at": "2026-08-19T11:27:20.472400+00:00",
        "score": 0.49,
    }

    normalized = normalize_chunk(chunk)

    assert normalized == {
        **chunk,
        "header_path": "NVDA / 2026 / Item 15. Exhibits, Financial Statement Schedules",
    }


def test_normalize_chunk_preserves_nested_block_heading_tail() -> None:
    """NVDA/2026 chunk_index=128: two levels of block heading below the Item segment
    (MarkdownNodeParser's unbounded nesting). The tail is kept as-is — it doesn't interfere
    with the scorer's header_path.startswith(expected) check and stays useful for debugging.
    """
    chunk = {
        "ticker": "NVDA",
        "year": 2026,
        "filing_date": "2026-02-25",
        "filing_type": "10-K",
        "accession_number": "0001045810-26-000021",
        "item": "Item 7",
        "header_path": (
            "NVDA / 2026 / Part II / Item 7. Management's Discussion and Analysis of "
            "Financial Condition and Results of Operations / Results of Operations / "
            "Operating Income by Reportable Segments"
        ),
        "chunk_index": 128,
        "text": "#### Operating Income by Reportable Segments\n\n"
        "|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |\n"
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- "
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        "ingested_at": "2026-08-19T11:27:20.472400+00:00",
        "score": 0.42,
    }

    normalized = normalize_chunk(chunk)

    assert normalized == {
        **chunk,
        "header_path": (
            "NVDA / 2026 / Item 7. Management's Discussion and Analysis of Financial "
            "Condition and Results of Operations / Results of Operations / "
            "Operating Income by Reportable Segments"
        ),
    }


def test_normalize_chunk_passes_through_unchanged_when_item_key_is_unrecognized() -> (
    None
):
    """Defensive path, not an observed real case: an item value that doesn't resolve to a
    known TENK_STANDARD_TITLES key is treated like "no item detected" rather than raising,
    since a single malformed chunk shouldn't crash a whole scoring run.
    """
    chunk = {
        "ticker": "ZZZZ",
        "year": 2025,
        "filing_date": "2025-01-01",
        "filing_type": "10-K",
        "accession_number": "0000000000-25-000000",
        "item": "Item 99",
        "header_path": "ZZZZ / 2025 / Part I / Item 99. Not A Real Item",
        "chunk_index": 0,
        "text": "placeholder",
        "ingested_at": "2025-01-01T00:00:00+00:00",
        "score": 0.1,
    }

    assert normalize_chunk(chunk) == chunk


def test_normalize_chunk_strips_temporary_suffix_before_canonical_title_lookup() -> (
    None
):
    """Clearly-synthetic fixture: no real 'Item 9A(T)' chunk exists in the reference CSV
    (checked via `grep -o "'item': '[^']*'"` over 2026-08-19_73faf5f.csv). "Item 9A(T)" is a
    real historical SEC form (~2008-2010, temporary internal-control-attestation exemption)
    that the frozen pipeline's own item-anchor regex
    (backend/ingestion/sec_dense_pipeline_html/vectorizer.py) recognizes and can emit, and
    that this module's own _ITEM_SEGMENT_RE anticipates matching. The canonical-title lookup
    must strip the trailing "(T)" so this resolves the same as a plain "Item 9A" instead of
    silently falling through to the "no canonical title found" passthrough.
    """
    chunk = {
        "ticker": "ZZZZ",
        "year": 2009,
        "filing_date": "2010-02-01",
        "filing_type": "10-K",
        "accession_number": "0000000000-10-000000",
        "item": "Item 9A(T)",
        "header_path": "ZZZZ / 2009 / Part II / Item 9A(T). Controls and Procedures (Temporary)",
        "chunk_index": 0,
        "text": "placeholder",
        "ingested_at": "2025-01-01T00:00:00+00:00",
        "score": 0.1,
    }

    normalized = normalize_chunk(chunk)

    assert normalized == {
        **chunk,
        "header_path": "ZZZZ / 2009 / Item 9A(T). Controls and Procedures",
    }
