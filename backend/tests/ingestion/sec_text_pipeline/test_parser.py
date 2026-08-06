import re

import pytest

from backend.common.sec_core import FetchedFiling, FilingType
from backend.ingestion.sec_text_pipeline import parser
from backend.ingestion.sec_text_pipeline.filing_models import FlatItem, ParsedFiling
from backend.tests.ingestion.sec_text_pipeline.conftest import FakeTenK, make_bundle


@pytest.fixture
def fetch_calls(monkeypatch, fake_bundle):
    """Patch the EDGAR fetch seam; record every call's arguments."""
    calls: list[tuple[str, FilingType, int | None]] = []

    def fake_fetch(
        ticker: str, filing_type: FilingType, fiscal_year: int | None = None
    ) -> FetchedFiling:
        calls.append((ticker, filing_type, fiscal_year))
        return fake_bundle

    monkeypatch.setattr(parser, "fetch_filing_bundle", fake_fetch)
    return calls


class TestParsedStructure:
    def test_all_emitted_items_are_flat(self, store, fetch_calls):
        result = parser.parse_filing("AAPL", fiscal_year=2025, store=store)
        assert isinstance(result, ParsedFiling)
        assert result.items  # non-empty
        assert all(isinstance(item, FlatItem) for item in result.items)

    def test_stub_items_are_dropped(self, store, fetch_calls):
        # Recorded AAPL FY2025 reality: 6 is [Reserved]; 10/11/12/13 are
        # incorporated-by-reference stubs. Item 11's raw section text bleeds
        # Items 12-15 onto its pure pointer stub — only after trimming to
        # its own boundary does it classify (and drop) correctly.
        result = parser.parse_filing("AAPL", fiscal_year=2025, store=store)
        emitted = {item.item for item in result.items}
        assert {"6", "10", "11", "12", "13"}.isdisjoint(emitted)
        assert {"1", "1a", "7"} <= emitted

    def test_emitted_text_contains_no_foreign_item_heading(self, store, fetch_calls):
        # Section bleed guard: edgartools returns Item 9C with "PART IIIItem
        # 10." (and onward) glued on, and Item 11 with Items 12-15 glued on.
        # After trimming, no emitted item's text may contain another item's
        # heading.
        heading_re = re.compile(r"(?<![a-z])(?i:item\s+(\d{1,2}[a-c]?)\s*\.(?!\d))")
        result = parser.parse_filing("AAPL", fiscal_year=2025, store=store)
        for item in result.items:
            foreign = {
                m.group(1).lower()
                for m in heading_re.finditer(item.text)
                if m.group(1).lower() != item.item
            }
            assert not foreign, f"item {item.item} text bleeds into {foreign}"
        nine_c = next(item for item in result.items if item.item == "9c")
        assert "Item 10." not in nine_c.text

    def test_item_keys_normalized_and_titled(self, store, fetch_calls):
        result = parser.parse_filing("AAPL", fiscal_year=2025, store=store)
        risk = next(item for item in result.items if item.item == "1a")
        assert risk.title == "Risk Factors"
        assert "Risk Factors" in risk.text

    def test_duplicate_item_keys_keep_first_occurrence(self, store, fetch_calls):
        # Recorded reality: edgartools reports item 8 twice for AAPL FY2025
        # (part_ii_item_8 and a part_iv misattribution of the Notes).
        result = parser.parse_filing("AAPL", fiscal_year=2025, store=store)
        eights = [item for item in result.items if item.item == "8"]
        assert len(eights) == 1
        assert eights[0].text.startswith("Item 8.")

    def test_non_item_entries_skipped(self, store, monkeypatch):
        # A section with item=None (e.g. signatures) must not crash nor emit.
        tenk = FakeTenK(
            sections_data={
                "part_iv_signatures": {"item": "", "text": "Signatures. " * 20},
                "part_i_item_2": {"item": "2", "text": "Item 2. Properties. " * 20},
            }
        )
        monkeypatch.setattr(
            parser, "fetch_filing_bundle", lambda *a, **k: make_bundle(tenk)
        )
        result = parser.parse_filing("AAPL", fiscal_year=2025, store=store)
        assert [item.item for item in result.items] == ["2"]

    def test_empty_text_item_skipped(self, store, monkeypatch):
        tenk = FakeTenK(
            sections_data={
                "part_i_item_1": {"item": "1", "text": "   \n  "},
                "part_i_item_2": {"item": "2", "text": "Item 2. Properties. " * 20},
            }
        )
        monkeypatch.setattr(
            parser, "fetch_filing_bundle", lambda *a, **k: make_bundle(tenk)
        )
        result = parser.parse_filing("AAPL", fiscal_year=2025, store=store)
        assert [item.item for item in result.items] == ["2"]

    def test_all_sections_empty_or_stub_raises_and_saves_nothing(
        self, store, monkeypatch
    ):
        # A filing where every section is empty or a stub must fail loudly:
        # caching/returning an empty ParsedFiling would look like a
        # successful ingestion to every downstream consumer.
        tenk = FakeTenK(
            sections_data={
                "part_i_item_1": {"item": "1", "text": "   \n  "},
                "part_ii_item_6": {"item": "6", "text": "Item 6. [Reserved]"},
                "part_iii_item_11": {
                    "item": "11",
                    "text": (
                        "Item 11. Executive Compensation. The information "
                        "required by this Item is incorporated herein by "
                        "reference from the Proxy Statement."
                    ),
                },
            }
        )
        monkeypatch.setattr(
            parser, "fetch_filing_bundle", lambda *a, **k: make_bundle(tenk)
        )
        with pytest.raises(parser.EmptyFilingError) as excinfo:
            parser.parse_filing("AAPL", fiscal_year=2025, store=store)
        # Actionable message: ticker, fiscal year, accession number.
        assert "AAPL" in str(excinfo.value)
        assert "2025" in str(excinfo.value)
        assert "0000320193-25-000079" in str(excinfo.value)
        assert store.get("AAPL", FilingType.TEN_K, 2025) is None


class TestMetadata:
    def test_metadata_from_filing_object(self, store, fetch_calls):
        meta = parser.parse_filing("AAPL", fiscal_year=2025, store=store).metadata
        assert meta.ticker == "AAPL"
        assert meta.cik == "320193"
        assert meta.company_name == "Apple Inc."
        assert meta.filing_type is FilingType.TEN_K
        assert meta.filing_date == "2025-10-31"
        assert meta.fiscal_year == 2025
        assert meta.accession_number == "0000320193-25-000079"
        assert meta.primary_document == "aapl-20250927.htm"
        assert meta.parsed_at  # timestamped

    def test_ticker_input_normalized(self, store, fetch_calls):
        meta = parser.parse_filing(" aapl ", fiscal_year=2025, store=store).metadata
        assert meta.ticker == "AAPL"
        assert fetch_calls[0][0] == "AAPL"


class TestStoreInteraction:
    def test_result_is_persisted_and_round_trips(self, store, fetch_calls):
        result = parser.parse_filing("AAPL", fiscal_year=2025, store=store)
        assert store.get("AAPL", FilingType.TEN_K, 2025) == result

    def test_cache_hit_skips_fetch(self, store, fetch_calls):
        first = parser.parse_filing("AAPL", fiscal_year=2025, store=store)
        second = parser.parse_filing("AAPL", fiscal_year=2025, store=store)
        assert second == first
        assert len(fetch_calls) == 1

    def test_force_refetches_and_overwrites(self, store, fetch_calls):
        parser.parse_filing("AAPL", fiscal_year=2025, store=store)
        parser.parse_filing("AAPL", fiscal_year=2025, force=True, store=store)
        assert len(fetch_calls) == 2

    def test_default_store_is_local_sec_text(self, monkeypatch, tmp_path, fake_bundle):
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(parser, "fetch_filing_bundle", lambda *a, **k: fake_bundle)
        parser.parse_filing("AAPL", fiscal_year=2025)
        assert (tmp_path / "data" / "sec_text" / "AAPL" / "10-K" / "2025.json").exists()
