"""EDGAR fetch with disk cache for the validation harness.

Wraps the existing SECDownloader so we don't duplicate edgartools
plumbing. Cached layout under `cache_dir`:

    {ticker}_{accession}.html
    {ticker}_{accession}.meta.json

The .meta.json sidecar lets subsequent runs skip both the network
call and the SECDownloader instantiation (which requires
EDGAR_IDENTITY).
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from pathlib import Path

from backend.ingestion.sec_filing_pipeline.filing_models import (
    FilingNotFoundError,
    SECPipelineError,
)
from backend.ingestion.sec_filing_pipeline.sec_downloader import SECDownloader

_TICKER_RE = re.compile(r"^[A-Z0-9.\-]+$")


class FetchError(Exception):
    """Raised when an EDGAR fetch cannot be completed."""


class FilingTypeRejected(FetchError):
    """Filing form is not 10-K (e.g. 10-K/A, NT 10-K, 20-F)."""


class PreCssEra(FetchError):
    """Filing year is before 2018 — outside CSS-era support."""


@dataclass(frozen=True)
class FilingFetchResult:
    ticker: str
    accession_number: str
    cik: str
    company_name: str
    filing_date: str
    fiscal_year: int
    form: str
    html_path: Path
    meta_path: Path
    from_cache: bool


def _validate_ticker(ticker: str) -> str:
    normalized = ticker.strip().upper()
    if not normalized or not _TICKER_RE.match(normalized):
        raise FetchError(f"Invalid ticker {ticker!r}")
    return normalized


def _meta_path_for(html_path: Path) -> Path:
    return html_path.with_suffix(".meta.json")


def find_cached(cache_dir: Path, ticker: str) -> Path | None:
    """Return the latest cached HTML path for ticker, or None.

    Ticker name is normalized; '.' in ticker (e.g. BRK.B) is replaced
    with '_' on disk so glob matches stay simple.
    """
    ticker = _validate_ticker(ticker)
    safe = ticker.replace(".", "_")
    if not cache_dir.exists():
        return None
    candidates = list(cache_dir.glob(f"{safe}_*.html"))
    if not candidates:
        return None
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0]


def load_meta(html_path: Path) -> dict:
    meta_path = _meta_path_for(html_path)
    if not meta_path.exists():
        return {}
    return json.loads(meta_path.read_text(encoding="utf-8"))


_DOWNLOADER: SECDownloader | None = None


def _get_downloader() -> SECDownloader:
    global _DOWNLOADER
    if _DOWNLOADER is None:
        _DOWNLOADER = SECDownloader()
    return _DOWNLOADER


def fetch_or_cache(
    ticker: str,
    cache_dir: Path,
    *,
    force: bool = False,
    rate_limit_seconds: float = 0.5,
) -> FilingFetchResult:
    """Fetch the latest 10-K for `ticker` and cache it under `cache_dir`.

    Returns the cached path; sets `from_cache=True` if no network call
    was needed. Pre-flight rejects pre-2018 filings.
    """
    ticker = _validate_ticker(ticker)
    cache_dir.mkdir(parents=True, exist_ok=True)
    safe = ticker.replace(".", "_")

    if not force:
        cached = find_cached(cache_dir, ticker)
        if cached is not None:
            meta = load_meta(cached)
            if meta:
                return FilingFetchResult(
                    ticker=ticker,
                    accession_number=meta["accession_number"],
                    cik=meta["cik"],
                    company_name=meta["company_name"],
                    filing_date=meta["filing_date"],
                    fiscal_year=meta["fiscal_year"],
                    form=meta["form"],
                    html_path=cached,
                    meta_path=_meta_path_for(cached),
                    from_cache=True,
                )

    time.sleep(rate_limit_seconds)  # Be polite to SEC.

    try:
        raw = _get_downloader().download(ticker, "10-K")
    except FilingNotFoundError as exc:
        raise FetchError(f"{ticker}: {exc}") from exc
    except SECPipelineError as exc:
        raise FetchError(f"{ticker}: {type(exc).__name__}: {exc}") from exc

    if raw.fiscal_year < 2018:
        raise PreCssEra(f"{ticker}: fiscal year {raw.fiscal_year} < 2018")

    accession_safe = raw.accession_number.replace("/", "_")
    html_path = cache_dir / f"{safe}_{accession_safe}.html"
    html_path.write_text(raw.raw_html, encoding="utf-8")

    meta = {
        "ticker": raw.ticker,
        "accession_number": raw.accession_number,
        "cik": raw.cik,
        "company_name": raw.company_name,
        "filing_date": raw.filing_date,
        "fiscal_year": raw.fiscal_year,
        "form": "10-K",
        "source_url": raw.source_url,
    }
    _meta_path_for(html_path).write_text(
        json.dumps(meta, indent=2), encoding="utf-8"
    )

    return FilingFetchResult(
        ticker=raw.ticker,
        accession_number=raw.accession_number,
        cik=raw.cik,
        company_name=raw.company_name,
        filing_date=raw.filing_date,
        fiscal_year=raw.fiscal_year,
        form="10-K",
        html_path=html_path,
        meta_path=_meta_path_for(html_path),
        from_cache=False,
    )
