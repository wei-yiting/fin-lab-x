"""Behavioral tests for the sec_text_pipeline CLI entry point.

Envelope §5 scope: one happy path per CLI mode plus one legible-failure
case. `parse_filing` is patched with a toy ParsedFiling — render
correctness itself is covered by test_inspect_view.py, so these tests
assert dispatch, forwarding, and output routing only.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from backend.ingestion.sec_text_pipeline.__main__ import main
from backend.ingestion.sec_text_pipeline.filing_models import FlatItem, ParsedFiling
from backend.tests.ingestion.sec_text_pipeline.conftest import (
    make_metadata,
    make_structured_item,
)

FLAT_BODY = "Flat risk factors body."


@pytest.fixture()
def toy_filing():
    return ParsedFiling(
        metadata=make_metadata(),
        items=[
            make_structured_item(),
            FlatItem(item="1a", title="Risk Factors", text=FLAT_BODY),
        ],
    )


def test_default_prints_summary(toy_filing, capsys):
    with patch(
        "backend.ingestion.sec_text_pipeline.__main__.parse_filing",
        return_value=toy_filing,
    ) as parse:
        main(["--ticker", "AAPL", "--fiscal-year", "2024"])

    out = capsys.readouterr().out
    assert "2 items (structured 1 / flat 1)" in out
    assert FLAT_BODY not in out
    parse.assert_called_once_with("AAPL", 2024, False)


def test_section_prints_plain_text(toy_filing, capsys):
    with patch(
        "backend.ingestion.sec_text_pipeline.__main__.parse_filing",
        return_value=toy_filing,
    ):
        main(["--ticker", "AAPL", "--fiscal-year", "2024", "--section", "1A"])

    assert capsys.readouterr().out == f"{FLAT_BODY}\n"


def test_inspect_writes_file_and_prints_path(toy_filing, capsys, monkeypatch, tmp_path):
    monkeypatch.setenv("SEC_TEXT_INSPECT_DIR", str(tmp_path))
    with patch(
        "backend.ingestion.sec_text_pipeline.__main__.parse_filing",
        return_value=toy_filing,
    ) as parse:
        main(["inspect", "--ticker", "AAPL", "--fiscal-year", "2024", "--force"])

    expected = tmp_path / "AAPL" / "10-K" / "2024.md"
    assert capsys.readouterr().out.strip() == str(expected)
    assert "# AAPL 10-K FY2024" in expected.read_text(encoding="utf-8")
    parse.assert_called_once_with("AAPL", 2024, True)


def test_unknown_section_key_fails_legibly(toy_filing, capsys):
    with patch(
        "backend.ingestion.sec_text_pipeline.__main__.parse_filing",
        return_value=toy_filing,
    ):
        with pytest.raises(SystemExit) as excinfo:
            main(["--ticker", "AAPL", "--fiscal-year", "2024", "--section", "9b"])

    assert excinfo.value.code == 1
    err = capsys.readouterr().err
    assert "available: 7, 1a" in err
    assert "Traceback" not in err


def test_malformed_ticker_fails_legibly(capsys):
    # No patch: the ticker is rejected by the filing store's validation
    # before any network access can happen.
    with pytest.raises(SystemExit) as excinfo:
        main(["--ticker", "../BAD", "--fiscal-year", "2024"])

    assert excinfo.value.code == 1
    err = capsys.readouterr().err
    assert "Invalid ticker" in err
    assert "Traceback" not in err
