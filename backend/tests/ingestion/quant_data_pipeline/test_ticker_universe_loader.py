import pytest
import yaml

from backend.ingestion.quant_data_pipeline.quant_pipeline_errors import ConfigurationError
from backend.ingestion.quant_data_pipeline.ticker_universe_loader import load_ticker_universe

EXPECTED_TICKERS = ["MSFT", "NVDA", "CRM", "WMT", "JPM", "BRK.B", "JNJ", "KO", "XOM", "CAT"]


def test_load_default_universe():
    result = load_ticker_universe()
    assert result == EXPECTED_TICKERS


def test_custom_path_uppercase_normalization(tmp_path):
    f = tmp_path / "universe.yaml"
    f.write_text("tickers:\n  - aapl\n  - googl\n")
    result = load_ticker_universe(f)
    assert result == ["AAPL", "GOOGL"]


def test_missing_tickers_key(tmp_path):
    f = tmp_path / "universe.yaml"
    f.write_text("foo: bar\n")
    with pytest.raises(ConfigurationError, match="missing 'tickers'"):
        load_ticker_universe(f)


def test_parse_error(tmp_path):
    f = tmp_path / "universe.yaml"
    f.write_text("{unclosed: [bracket")
    with pytest.raises(ConfigurationError, match="Failed to parse") as excinfo:
        load_ticker_universe(f)
    assert isinstance(excinfo.value.__cause__, yaml.YAMLError)


def test_file_not_found(tmp_path):
    with pytest.raises(ConfigurationError, match="not found"):
        load_ticker_universe(tmp_path / "nonexistent.yaml")


def test_loader_rejects_scalar_string(tmp_path):
    p = tmp_path / "u.yaml"
    p.write_text('tickers: "MSFT"\n')
    with pytest.raises(ConfigurationError, match="must be a list"):
        load_ticker_universe(p)


def test_loader_rejects_dict(tmp_path):
    p = tmp_path / "u.yaml"
    p.write_text('tickers:\n  MSFT: 1\n')
    with pytest.raises(ConfigurationError, match="must be a list"):
        load_ticker_universe(p)


def test_loader_rejects_empty_string_in_list(tmp_path):
    p = tmp_path / "u.yaml"
    p.write_text('tickers:\n  - MSFT\n  - ""\n')
    with pytest.raises(ConfigurationError, match="non-empty string"):
        load_ticker_universe(p)


def test_loader_rejects_null_in_list(tmp_path):
    p = tmp_path / "u.yaml"
    p.write_text('tickers:\n  - MSFT\n  - null\n')
    with pytest.raises(ConfigurationError, match="non-empty string"):
        load_ticker_universe(p)
