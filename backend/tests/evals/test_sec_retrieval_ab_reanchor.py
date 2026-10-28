"""Unit tests for re-anchoring sec_retrieval_ab ground truth to a new filing store."""

from backend.common.sec_core import FilingType
from backend.evals.scenarios.sec_retrieval_ab.curation.reanchor_to_store import (
    exact_slice,
    reanchor_row,
)
from backend.ingestion.sec_text_pipeline.filing_models import (
    Block,
    FilingMetadata,
    FlatItem,
    ParsedFiling,
    StructuredItem,
)

SPAN = "Price – Lower realizations decreased earnings by $6.1 billion. More text."
SNIPPET = "Price – Lower realizations decreased earnings by $6.1 billion."


def _filing(item7_text: str, item8_text: str = "notes") -> ParsedFiling:
    return ParsedFiling(
        metadata=FilingMetadata(
            ticker="XOM",
            cik="0000034088",
            company_name="EXXON MOBIL CORP",
            filing_type=FilingType.TEN_K,
            filing_date="2026-02-18",
            fiscal_year=2025,
            accession_number="0000034088-26-000045",
            primary_document="xom-20251231.htm",
            parsed_at="2026-10-28T00:00:00+00:00",
        ),
        items=[
            StructuredItem(
                item="7",
                title="Management's Discussion and Analysis",
                prelude="",
                blocks=[Block(heading="Upstream", text="Intro. " + item7_text)],
                detection_source="markdown_h4",
            ),
            FlatItem(item="8", title="Financial Statements", text=item8_text),
            FlatItem(item="16", title="Form 10-K Summary", text="None."),
        ],
    )


def _row(paths: list[str], spans: list[str], snippets: list[str]) -> dict[str, list]:
    return {
        "expected_header_paths": paths,
        "answer_spans": spans,
        "answer_snippets": snippets,
        "block_heading": ["old"] * len(paths),
        "detection_source": ["flat"] * len(paths),
    }


ITEM_16 = "XOM / 2025 / Item 16. Form 10-K Summary"
ITEM_7 = "XOM / 2025 / Item 7. Management's Discussion and Analysis"


class TestExactSlice:
    def test_returns_store_text_for_whitespace_variant(self) -> None:
        haystack = "Fixed income $35\xa0 $27\n\nForeign exchange 9"
        assert exact_slice(haystack, "fixed income$35 $27 Foreign") == (
            "Fixed income $35\xa0 $27\n\nForeign"
        )

    def test_none_when_absent(self) -> None:
        assert exact_slice("abc def", "xyz") is None


class TestReanchorRow:
    def test_unchanged_alternative_keeps_path_and_refreshes_block_metadata(
        self,
    ) -> None:
        row = _row([ITEM_7], [SPAN], [SNIPPET])
        new, notes = reanchor_row(row, _filing(SPAN))
        assert new["expected_header_paths"] == [ITEM_7]
        assert new["answer_spans"] == [SPAN]
        assert new["block_heading"] == ["Upstream"]
        assert new["detection_source"] == ["markdown_h4"]
        assert notes == []

    def test_label_escape_moves_to_the_item_holding_the_text(self) -> None:
        row = _row([ITEM_16], [SPAN], [SNIPPET])
        new, notes = reanchor_row(row, _filing(SPAN))
        assert new["expected_header_paths"] == [ITEM_7]
        assert any("Item 16 -> Item 7" in n for n in notes)

    def test_whitespace_drift_is_reextracted_from_store(self) -> None:
        drifted = SPAN.replace(" Lower", "\xa0 Lower")
        row = _row([ITEM_7], [SPAN], [SNIPPET])
        new, notes = reanchor_row(row, _filing(drifted))
        assert new["answer_spans"] == [drifted]
        assert new["answer_snippets"] == [SNIPPET.replace(" Lower", "\xa0 Lower")]
        assert any("whitespace" in n for n in notes)

    def test_alternatives_collapsing_to_one_location_are_deduplicated(self) -> None:
        row = _row([ITEM_7, ITEM_16], [SPAN, SPAN], [SNIPPET, SNIPPET])
        new, notes = reanchor_row(row, _filing(SPAN))
        assert new["expected_header_paths"] == [ITEM_7]
        assert any("merged" in n for n in notes)

    def test_item_8_copies_are_never_anchors(self) -> None:
        row = _row([ITEM_16], [SPAN], [SNIPPET])
        new, notes = reanchor_row(row, _filing("unrelated", item8_text=SPAN))
        assert new["expected_header_paths"] == []
        assert any("not found" in n for n in notes)
