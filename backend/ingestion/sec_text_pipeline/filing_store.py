"""JSON filing store — the fetch+parse stage cache.

Persists :class:`ParsedFiling` as schema-validated JSON under
``data/sec_text/{TICKER}/10-K/{YEAR}.json``. Machine-facing cache only:
the inspect view (:mod:`inspect_view` + the package CLI) derives the
human-facing markdown render from this store. Parallel to Qdrant (the
embedding-stage cache) — the two
invalidate under different conditions (a parser change invalidates this
store; an embedding-model change invalidates only Qdrant), hence both
exist.
"""

from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path
from typing import Protocol

from backend.common.data_paths import get_sec_text_dir
from backend.common.sec_core import FilingType
from backend.ingestion.sec_text_pipeline.filing_models import ParsedFiling

# First character must be alphanumeric so path-special values ("." , "..",
# ".AAPL", "-AAPL") can never become a directory component.
_TICKER_RE = re.compile(r"^[A-Z0-9][A-Z0-9.\-]*$")


class FilingStore(Protocol):
    """What parse_filing needs from a store — nothing more (envelope §0
    reachability). Downstream tickets widen this when they consume more.
    """

    def save(self, filing: ParsedFiling) -> None: ...

    def get(
        self, ticker: str, filing_type: FilingType, fiscal_year: int
    ) -> ParsedFiling | None: ...


class LocalFilingStore:
    def __init__(self, base_dir: str | Path | None = None) -> None:
        self._base_dir = Path(base_dir) if base_dir is not None else get_sec_text_dir()

    @staticmethod
    def _validate_ticker(ticker: str) -> str:
        normalized = ticker.strip().upper()
        if not normalized or not _TICKER_RE.match(normalized):
            raise ValueError(
                f"Invalid ticker {ticker!r}: must start with A-Z or 0-9 and "
                f"contain only A-Z, 0-9, '.', or '-'"
            )
        return normalized

    def _filing_dir(self, ticker: str, filing_type: FilingType) -> Path:
        return self._base_dir / self._validate_ticker(ticker) / str(filing_type)

    def _filing_path(
        self, ticker: str, filing_type: FilingType, fiscal_year: int
    ) -> Path:
        return self._filing_dir(ticker, filing_type) / f"{fiscal_year}.json"

    def save(self, filing: ParsedFiling) -> None:
        ticker = self._validate_ticker(filing.metadata.ticker)
        path = self._filing_path(
            ticker, filing.metadata.filing_type, filing.metadata.fiscal_year
        )
        os.makedirs(path.parent, exist_ok=True)

        # Normalize the ticker inside the stored payload so the file content
        # always matches its own path key.
        normalized = filing.model_copy(
            update={"metadata": filing.metadata.model_copy(update={"ticker": ticker})}
        )
        content = normalized.model_dump_json(indent=2)

        fd, tmp_path = tempfile.mkstemp(
            dir=path.parent, suffix=".tmp", prefix=".filing_"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(content)
            os.replace(tmp_path, path)
        except BaseException:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise

    def get(
        self, ticker: str, filing_type: FilingType, fiscal_year: int
    ) -> ParsedFiling | None:
        path = self._filing_path(ticker, filing_type, fiscal_year)
        if not path.exists():
            return None
        return ParsedFiling.model_validate_json(path.read_text(encoding="utf-8"))
