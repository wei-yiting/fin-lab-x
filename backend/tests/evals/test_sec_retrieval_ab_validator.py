"""Unit tests for the sec_retrieval_ab dataset validator.

The validator is the single programmatic gate for the DEV-162 dataset
contract: ground truth is validated against fixture filing-store JSON only
(ADR-0016) — no Qdrant, no network, no LLM. Each contract rule gets at
least one passing and one failing case.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from backend.common.sec_core import FilingType
from backend.evals.scenarios.sec_retrieval_ab.curation.validate_dataset import (
    Issue,
    Row,
    load_filings,
    validate_rows,
)
from backend.ingestion.sec_text_pipeline.filing_models import (
    Block,
    FilingMetadata,
    FlatItem,
    ParsedFiling,
    StructuredItem,
)
from backend.ingestion.sec_text_pipeline.filing_store import LocalFilingStore

# --- fixture sentences (>=50 chars each so they are legal snippets) ---

EXPORT_SENT = (
    "The October 2023 export restrictions affected shipments of our "
    "A100 and H100 data center products to certain regions."
)
CONCENTRATION_SENT = (
    "A small number of hyperscale customers accounted for a substantial "
    "portion of our data center revenue in fiscal 2025."
)
REVENUE_SENT = (
    "Total revenue increased 42 percent year over year, driven primarily "
    "by demand for accelerated computing platforms."
)
DUP_SENT = (
    "We are subject to extensive regulation across the jurisdictions in "
    "which we operate our business segments."
)
FLAT_FIRST_SENT = (
    "Our exposure to interest rate fluctuations relates primarily to our "
    "fixed income investment portfolio holdings."
)
FLAT_NEAR_SENT = (
    "A hypothetical 100 basis point move in market interest rates would "
    "not materially change the portfolio fair value."
)
FLAT_FAR_SENT = (
    "Foreign currency forward contracts are used to hedge a portion of "
    "our anticipated non-dollar operating expenses."
)
SAME_TICKER_DUP_SENT = (
    "Our supplier concentration in advanced packaging remains a structural "
    "constraint on near-term capacity expansion."
)


def _filler(n_words: int, tag: str) -> str:
    """Deterministic filler prose that cannot collide with any snippet."""
    return " ".join(f"{tag}{i} operations continue" for i in range(n_words))


def _metadata(ticker: str, fiscal_year: int) -> FilingMetadata:
    return FilingMetadata(
        ticker=ticker,
        cik="0000000000",
        company_name=f"{ticker} Test Corp",
        filing_type=FilingType("10-K"),
        filing_date=f"{fiscal_year}-02-01",
        fiscal_year=fiscal_year,
        accession_number="0000000000-00-000000",
        primary_document="test.htm",
        parsed_at="2026-08-20T00:00:00Z",
    )


LONG_BLOCK_SPAN = _filler(260, "liquidity")  # > 300 cl100k tokens


@pytest.fixture()
def store_dir(tmp_path: Path) -> Path:
    store = LocalFilingStore(base_dir=tmp_path)

    filing_a = ParsedFiling(
        metadata=_metadata("AAA", 2025),
        items=[
            StructuredItem(
                item="1a",
                title="Risk Factors",
                prelude="The following prelude summarizes principal risks.",
                detection_source="markdown_h3",
                blocks=[
                    Block(
                        heading="Export Controls",
                        text=(
                            "Government agencies tightened trade rules during "
                            f"the year. {EXPORT_SENT} We continue to seek "
                            "licenses where they are available to us."
                        ),
                    ),
                    Block(
                        heading="Customer Concentration",
                        text=(
                            f"{CONCENTRATION_SENT} The loss of any such "
                            f"customer could harm results. {DUP_SENT} "
                            f"{SAME_TICKER_DUP_SENT}"
                        ),
                    ),
                ],
            ),
            StructuredItem(
                item="7",
                title=(
                    "Management's Discussion and Analysis of Financial "
                    "Condition and Results of Operations"
                ),
                prelude="",
                detection_source="markdown_h4",
                blocks=[
                    Block(
                        heading="Results of Operations",
                        text=(
                            f"Fiscal 2025 was a record year. {REVENUE_SENT} "
                            f"Gross margin expanded on product mix. "
                            f"{SAME_TICKER_DUP_SENT}"
                        ),
                    ),
                    Block(heading="Liquidity", text=LONG_BLOCK_SPAN),
                ],
            ),
            # Item 8 copy of EXPORT_SENT: outside the retrieval scope, so it
            # must not count against snippet uniqueness (round-3 decision 4).
            StructuredItem(
                item="8",
                title="Financial Statements and Supplementary Data",
                prelude="",
                detection_source="markdown_h3",
                blocks=[
                    Block(
                        heading="Note 1",
                        text=f"Basis of presentation. {EXPORT_SENT}",
                    )
                ],
            ),
            FlatItem(
                item="7a",
                title=("Quantitative and Qualitative Disclosures About Market Risk"),
                text=(
                    f"{FLAT_FIRST_SENT} {FLAT_NEAR_SENT} "
                    f"{_filler(500, 'ratebook')} {FLAT_FAR_SENT}"
                ),
            ),
        ],
    )
    filing_b = ParsedFiling(
        metadata=_metadata("BBB", 2024),
        items=[
            StructuredItem(
                item="1a",
                title="Risk Factors",
                prelude="",
                detection_source="text_fallback",
                blocks=[
                    Block(
                        heading="Regulatory Risk",
                        text=f"{DUP_SENT} Compliance costs may increase.",
                    )
                ],
            ),
        ],
    )
    store.save(filing_a)
    store.save(filing_b)
    return tmp_path


def _row(**overrides: object) -> Row:
    base: dict[str, object] = dict(
        row_id="r1",
        question="export restriction impact on data center products",
        header_paths=["AAA / 2025 / Item 1A. Risk Factors"],
        tickers=["AAA"],
        spans=[EXPORT_SENT],
        snippets=[EXPORT_SENT],
        query_type="factoid",
    )
    base.update(overrides)
    return Row(**base)  # type: ignore[arg-type]


def _issues(store_dir: Path, *rows: Row) -> list[Issue]:
    return validate_rows(list(rows), load_filings(store_dir))


def _rules(issues: list[Issue]) -> set[str]:
    return {issue.rule for issue in issues}


# --- passing cases ---


def test_valid_factoid_and_passage_rows_pass(store_dir: Path) -> None:
    factoid = _row()
    passage = _row(
        row_id="r2",
        question="drivers of annual revenue growth",
        header_paths=[
            "AAA / 2025 / Item 7. Management's Discussion and Analysis of "
            "Financial Condition and Results of Operations"
        ],
        spans=[
            f"Fiscal 2025 was a record year. {REVENUE_SENT} "
            "Gross margin expanded on product mix."
        ],
        snippets=[REVENUE_SENT],
        query_type="passage",
    )
    assert _issues(store_dir, factoid, passage) == []


def test_or_set_alternatives_pass(store_dir: Path) -> None:
    """Entries are OR alternatives: several distinct locations, one row."""
    flat_path = (
        "AAA / 2025 / Item 7A. Quantitative and Qualitative Disclosures "
        "About Market Risk"
    )
    row = _row(
        header_paths=[flat_path, flat_path],
        spans=[FLAT_FIRST_SENT, FLAT_FAR_SENT],
        snippets=[FLAT_FIRST_SENT, FLAT_FAR_SENT],
        query_type="passage",
    )
    assert _issues(store_dir, row) == []


def test_enumerated_same_text_duplicate_passes(store_dir: Path) -> None:
    """A snippet occurring twice passes when both locations are listed."""
    row = _row(
        header_paths=[
            "AAA / 2025 / Item 1A. Risk Factors",
            "AAA / 2025 / Item 7. Management's Discussion and Analysis of "
            "Financial Condition and Results of Operations",
        ],
        spans=[SAME_TICKER_DUP_SENT, SAME_TICKER_DUP_SENT],
        snippets=[SAME_TICKER_DUP_SENT, SAME_TICKER_DUP_SENT],
        query_type="passage",
    )
    assert _issues(store_dir, row) == []


def test_item8_copy_does_not_break_uniqueness(store_dir: Path) -> None:
    """EXPORT_SENT also lives in the fixture's Item 8; that copy is outside
    the retrieval scope and must not count against uniqueness."""
    assert "snippet_not_unique" not in _rules(_issues(store_dir, _row()))


def test_span_in_prelude_passes(store_dir: Path) -> None:
    row = _row(
        spans=["The following prelude summarizes principal risks."],
        snippets=["The following prelude summarizes principal risks."],
    )
    issues = _issues(store_dir, row)
    # Prelude text is a legal single-unit home for a span; only the
    # snippet-length rule may fire here (49 < 50 chars is deliberate).
    assert "span_not_in_block" not in _rules(issues)


# --- rule (a): exact substring ---


def test_span_absent_from_item_fails(store_dir: Path) -> None:
    row = _row(spans=["This sentence is nowhere in the filing store text."])
    assert "span_not_in_block" in _rules(_issues(store_dir, row))


def test_snippet_not_inside_span_fails(store_dir: Path) -> None:
    row = _row(snippets=[CONCENTRATION_SENT])
    assert "snippet_not_in_span" in _rules(_issues(store_dir, row))


def test_span_crossing_two_blocks_fails(store_dir: Path) -> None:
    crossing = (
        "We continue to seek licenses where they are available to us. "
        f"{CONCENTRATION_SENT}"
    )
    row = _row(spans=[crossing], snippets=[CONCENTRATION_SENT])
    assert "span_not_in_block" in _rules(_issues(store_dir, row))


# --- rule (b): span length ---


def test_span_over_token_budget_fails(store_dir: Path) -> None:
    md_and_a = (
        "AAA / 2025 / Item 7. Management's Discussion and Analysis of "
        "Financial Condition and Results of Operations"
    )
    snippet = "liquidity0 operations continue liquidity1 operations continue"
    row = _row(
        header_paths=[md_and_a],
        spans=[LONG_BLOCK_SPAN],
        snippets=[snippet],
    )
    assert "span_too_long" in _rules(_issues(store_dir, row))


# --- rule (c): snippet length and corpus uniqueness ---


def test_snippet_too_short_fails(store_dir: Path) -> None:
    short = "The following prelude summarizes principal risks."
    assert len(short) < 50
    row = _row(spans=[short], snippets=[short])
    assert "snippet_length" in _rules(_issues(store_dir, row))


def test_snippet_duplicated_across_corpus_fails(store_dir: Path) -> None:
    row = _row(
        spans=[
            f"{CONCENTRATION_SENT} The loss of any such customer could "
            f"harm results. {DUP_SENT}"
        ],
        snippets=[DUP_SENT],
    )
    assert "snippet_not_unique" in _rules(_issues(store_dir, row))


# --- rule (d): retired query types and excluded items ---


def test_multi_passage_query_type_rejected(store_dir: Path) -> None:
    row = _row(
        header_paths=[
            "AAA / 2025 / Item 1A. Risk Factors",
            "AAA / 2025 / Item 1A. Risk Factors",
        ],
        spans=[EXPORT_SENT, CONCENTRATION_SENT],
        snippets=[EXPORT_SENT, CONCENTRATION_SENT],
        query_type="multi_passage",
    )
    assert "entry_count" in _rules(_issues(store_dir, row))


def test_item_8_header_path_rejected(store_dir: Path) -> None:
    row = _row(
        header_paths=[
            "AAA / 2025 / Item 8. Financial Statements and Supplementary Data"
        ],
    )
    assert "item_8_excluded" in _rules(_issues(store_dir, row))


# --- rule (e): header_path contract ---


def test_header_path_with_part_segment_fails(store_dir: Path) -> None:
    row = _row(header_paths=["AAA / 2025 / Part I / Item 1A. Risk Factors"])
    assert "header_path_format" in _rules(_issues(store_dir, row))


def test_header_path_title_mismatch_fails(store_dir: Path) -> None:
    row = _row(header_paths=["AAA / 2025 / Item 1A. Risks"])
    assert "header_path_format" in _rules(_issues(store_dir, row))


def test_header_path_item_missing_from_filing_fails(store_dir: Path) -> None:
    row = _row(header_paths=["AAA / 2025 / Item 3. Legal Proceedings"])
    assert "item_missing" in _rules(_issues(store_dir, row))


def test_filing_missing_from_store_fails(store_dir: Path) -> None:
    row = _row(header_paths=["ZZZ / 2025 / Item 1A. Risk Factors"], tickers=["ZZZ"])
    assert "filing_missing" in _rules(_issues(store_dir, row))


# --- structural rules ---


def test_misaligned_list_lengths_fail(store_dir: Path) -> None:
    row = _row(
        header_paths=[
            "AAA / 2025 / Item 1A. Risk Factors",
            "AAA / 2025 / Item 1A. Risk Factors",
        ],
    )  # spans/snippets still length 1
    assert "list_alignment" in _rules(_issues(store_dir, row))


def test_zero_entries_fail(store_dir: Path) -> None:
    row = _row(header_paths=[], spans=[], snippets=[])
    assert "entry_count" in _rules(_issues(store_dir, row))


def test_ticker_mismatch_with_header_path_fails(store_dir: Path) -> None:
    row = _row(tickers=["BBB"])
    assert "ticker_mismatch" in _rules(_issues(store_dir, row))


# --- generation helper: sentence splitter abbreviation guard ---


def test_sentence_ranges_do_not_break_after_abbreviations() -> None:
    from backend.evals.scenarios.sec_retrieval_ab.curation.generate_candidates import (
        sentence_ranges,
    )

    text = (
        "We operated 285 warehouses outside of the U.S. (31% of all "
        "locations), and we plan to expand. A second sentence follows here."
    )
    ranges = sentence_ranges(text)
    sentences = [text[a:b] for a, b in ranges]
    assert len(sentences) == 2
    assert "(31%" in sentences[0]  # not split at the "U.S." abbreviation
    assert sentences[1] == "A second sentence follows here."
