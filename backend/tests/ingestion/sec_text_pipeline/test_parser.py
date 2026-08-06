import pytest

from backend.common.sec_core import FilingType
from backend.ingestion.sec_text_pipeline import parser
from backend.ingestion.sec_text_pipeline.filing_models import FlatItem, ParsedFiling
from backend.tests.ingestion.sec_text_pipeline.conftest import FakeTenK


@pytest.fixture
def fetch_calls(monkeypatch, fake_tenk):
    """Patch the EDGAR fetch seam; record every call's arguments."""
    calls: list[tuple[str, FilingType, int | None]] = []

    def fake_fetch(
        ticker: str, filing_type: FilingType, fiscal_year: int | None = None
    ) -> FakeTenK:
        calls.append((ticker, filing_type, fiscal_year))
        return fake_tenk

    monkeypatch.setattr(parser, "fetch_filing_obj", fake_fetch)
    return calls


class TestParsedStructure:
    def test_all_emitted_items_are_flat(self, store, fetch_calls):
        result = parser.parse_filing("AAPL", fiscal_year=2025, store=store)
        assert isinstance(result, ParsedFiling)
        assert result.items  # non-empty
        assert all(isinstance(item, FlatItem) for item in result.items)

    def test_stub_items_are_dropped(self, store, fetch_calls):
        # Recorded AAPL FY2025 reality: 6 is [Reserved]; 10/12/13 are
        # incorporated-by-reference stubs. 11 contains real compensation
        # prose beyond its pointer sentence — the remaining-content
        # mechanism must keep it alive.
        result = parser.parse_filing("AAPL", fiscal_year=2025, store=store)
        emitted = {item.item for item in result.items}
        assert {"6", "10", "12", "13"}.isdisjoint(emitted)
        assert {"1", "1a", "7", "11"} <= emitted

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
        monkeypatch.setattr(parser, "fetch_filing_obj", lambda *a, **k: tenk)
        result = parser.parse_filing("AAPL", fiscal_year=2025, store=store)
        assert [item.item for item in result.items] == ["2"]

    def test_empty_text_item_skipped(self, store, monkeypatch):
        tenk = FakeTenK(
            sections_data={
                "part_i_item_1": {"item": "1", "text": "   \n  "},
                "part_i_item_2": {"item": "2", "text": "Item 2. Properties. " * 20},
            }
        )
        monkeypatch.setattr(parser, "fetch_filing_obj", lambda *a, **k: tenk)
        result = parser.parse_filing("AAPL", fiscal_year=2025, store=store)
        assert [item.item for item in result.items] == ["2"]


class TestMetadata:
    def test_metadata_from_filing_object(self, store, fetch_calls):
        meta = parser.parse_filing("AAPL", fiscal_year=2025, store=store).metadata
        assert meta.ticker == "AAPL"
        assert meta.cik == "320193"
        assert meta.company_name == "Apple Inc."
        assert meta.filing_type is FilingType.TEN_K
        assert meta.filing_date == "2025-10-31"
        assert meta.fiscal_year == 2025  # derived from period_of_report
        assert meta.accession_number == "0000320193-25-000079"
        assert meta.primary_document == "aapl-20250927.htm"
        assert meta.parsed_at  # timestamped

    def test_ticker_input_normalized(self, store, fetch_calls):
        meta = parser.parse_filing(" aapl ", fiscal_year=2025, store=store).metadata
        assert meta.ticker == "AAPL"
        assert fetch_calls[0][0] == "AAPL"

    def test_fiscal_year_derived_when_not_given(self, store, fetch_calls):
        meta = parser.parse_filing("AAPL", store=store).metadata
        assert meta.fiscal_year == 2025
        assert fetch_calls == [("AAPL", FilingType.TEN_K, None)]


class TestStoreInteraction:
    def test_result_is_persisted_and_round_trips(self, store, fetch_calls):
        result = parser.parse_filing("AAPL", fiscal_year=2025, store=store)
        assert store.get("AAPL", FilingType.TEN_K, 2025) == result

    def test_cache_hit_skips_fetch(self, store, fetch_calls):
        first = parser.parse_filing("AAPL", fiscal_year=2025, store=store)
        second = parser.parse_filing("AAPL", fiscal_year=2025, store=store)
        assert second == first
        assert len(fetch_calls) == 1

    def test_cache_hit_after_fetch_when_year_unknown(self, store, fetch_calls):
        first = parser.parse_filing("AAPL", fiscal_year=2025, store=store)
        # Without a year we must ask EDGAR what "latest" is, but the parse
        # result comes from the store once the derived year hits the cache.
        second = parser.parse_filing("AAPL", store=store)
        assert second == first
        assert len(fetch_calls) == 2

    def test_force_refetches_and_overwrites(self, store, fetch_calls):
        parser.parse_filing("AAPL", fiscal_year=2025, store=store)
        parser.parse_filing("AAPL", fiscal_year=2025, force=True, store=store)
        assert len(fetch_calls) == 2

    def test_default_store_is_local_sec_text(self, monkeypatch, tmp_path, fake_tenk):
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(parser, "fetch_filing_obj", lambda *a, **k: fake_tenk)
        parser.parse_filing("AAPL", fiscal_year=2025)
        assert (tmp_path / "data" / "sec_text" / "AAPL" / "10-K" / "2025.json").exists()
