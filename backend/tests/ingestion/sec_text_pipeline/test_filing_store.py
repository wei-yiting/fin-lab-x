import json

import pytest

from backend.common.sec_core import FilingType
from backend.ingestion.sec_text_pipeline.filing_models import FlatItem, ParsedFiling
from backend.tests.ingestion.sec_text_pipeline.conftest import (
    make_metadata,
    make_structured_item,
)


@pytest.fixture
def filing() -> ParsedFiling:
    return ParsedFiling(
        metadata=make_metadata(),
        items=[
            make_structured_item(),
            FlatItem(item="1b", title="Unresolved Staff Comments", text="None."),
        ],
    )


class TestRoundTrip:
    def test_save_then_get_returns_equal_filing(self, store, filing):
        store.save(filing)
        restored = store.get("AAPL", FilingType.TEN_K, 2024)
        assert restored == filing

    def test_saved_file_is_json_at_expected_path(self, store, filing, tmp_path):
        store.save(filing)
        path = tmp_path / "AAPL" / "10-K" / "2024.json"
        assert path.exists()
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["metadata"]["accession_number"] == "0000320193-24-000123"
        assert payload["items"][0]["kind"] == "structured"

    def test_ticker_is_normalized_on_save_and_get(self, store, filing):
        store.save(filing.model_copy(update={"metadata": make_metadata(ticker="aapl")}))
        assert store.get(" aapl ", FilingType.TEN_K, 2024) is not None

    def test_save_overwrites_existing_year(self, store, filing):
        store.save(filing)
        updated = filing.model_copy(update={"items": []})
        store.save(updated)
        assert store.get("AAPL", FilingType.TEN_K, 2024) == updated

    def test_no_tmp_files_left_behind(self, store, filing, tmp_path):
        store.save(filing)
        leftovers = [p for p in tmp_path.rglob("*") if p.suffix == ".tmp"]
        assert leftovers == []

    def test_get_missing_returns_none(self, store):
        assert store.get("MSFT", FilingType.TEN_K, 2024) is None


class TestValidation:
    @pytest.mark.parametrize("bad", ["", "  ", "A/PL", "../etc"])
    def test_invalid_ticker_rejected(self, store, bad):
        with pytest.raises(ValueError):
            store.get(bad, FilingType.TEN_K, 2024)

    def test_corrupt_json_raises_validation_error(self, store, filing, tmp_path):
        store.save(filing)
        path = tmp_path / "AAPL" / "10-K" / "2024.json"
        path.write_text('{"metadata": {}}', encoding="utf-8")
        with pytest.raises(Exception):
            store.get("AAPL", FilingType.TEN_K, 2024)
