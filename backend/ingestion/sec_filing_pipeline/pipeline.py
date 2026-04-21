from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal

from backend.ingestion.sec_filing_pipeline.filing_models import (
    FilingMetadata,
    FilingType,
    ParsedFiling,
    RawFiling,
    RetryCallback,
    SECPipelineError,
    TransientError,
    UnsupportedFilingTypeError,
)
from backend.ingestion.sec_filing_pipeline.filing_store import (
    FilingStore,
    LocalFilingStore,
)
from backend.ingestion.sec_filing_pipeline.html_preprocessor import HTMLPreprocessor
from backend.ingestion.sec_filing_pipeline.html_to_md_converter import (
    HTMLToMarkdownConverter,
    MarkdownifyAdapter,
    convert_with_fallback,
    create_converter,
)
from backend.ingestion.sec_filing_pipeline.markdown_cleaner import MarkdownCleaner
from backend.ingestion.sec_filing_pipeline.sec_downloader import SECDownloader

logger = logging.getLogger(__name__)

_MAX_BATCH_RETRIES = 3
_RETRY_BASE_DELAY = 1.0


@dataclass(frozen=True)
class BatchResult:
    status: Literal["success", "error"]
    filing: ParsedFiling | None
    error: SECPipelineError | None
    from_cache: bool


class SECFilingPipeline:
    """Orchestrates download → preprocess → convert → store for a single SEC filing.

    Wires together the four pipeline stages and exposes two entry points:

    - :meth:`process` — single-filing JIT path used by the agent tool and CLI
      (one ticker, one filing, raises on failure).
    - :meth:`process_batch` — multi-ticker path used by the batch CLI command
      (returns a per-ticker ``BatchResult`` instead of raising, so one bad
      ticker does not abort the run).

    Both paths share :meth:`_execute_with_retry` for transient-error retry,
    and :meth:`_process_internal` for the actual stage execution.
    """

    def __init__(
        self,
        downloader: SECDownloader,
        preprocessor: HTMLPreprocessor,
        converter: HTMLToMarkdownConverter,
        fallback_converter: HTMLToMarkdownConverter,
        markdown_cleaner: MarkdownCleaner,
        store: FilingStore,
    ) -> None:
        self._downloader = downloader
        self._preprocessor = preprocessor
        self._converter = converter
        self._fallback_converter = fallback_converter
        self._markdown_cleaner = markdown_cleaner
        self._store = store

    @classmethod
    def create(cls) -> SECFilingPipeline:
        """Build a pipeline wired with the default production collaborators.

        Use this for CLI / agent-tool entry points where you want the standard
        ``html-to-markdown`` primary converter, ``markdownify`` fallback,
        :class:`MarkdownCleaner` for boilerplate stripping, and the on-disk
        :class:`LocalFilingStore`.  Tests should construct
        ``SECFilingPipeline`` directly with fakes/mocks instead.
        """
        return cls(
            downloader=SECDownloader(),
            preprocessor=HTMLPreprocessor(),
            converter=create_converter(),
            fallback_converter=MarkdownifyAdapter(),
            markdown_cleaner=MarkdownCleaner(),
            store=LocalFilingStore(),
        )

    def process(
        self,
        ticker: str,
        filing_type: str,
        fiscal_year: int | None = None,
        force: bool = False,
        on_retry: RetryCallback | None = None,
    ) -> ParsedFiling:
        """Process a single filing and return the parsed result.

        Single-filing entry point used by the agent tool and the default CLI
        invocation.  Honors the cache (skip download if hit) unless ``force``
        is set, retries transient errors up to ``_MAX_BATCH_RETRIES`` times,
        and raises any :class:`SECPipelineError` on failure — so callers see
        the original exception type and can branch on it.

        Use :meth:`process_batch` instead when you have many tickers and want
        per-ticker error isolation.
        """
        filing, _ = self._execute_with_retry(
            ticker, filing_type, fiscal_year, force, on_retry
        )
        return filing

    def resolve_latest_year(self, ticker: str, filing_type: str) -> int:
        """Return EDGAR's latest fiscal year for a ticker without downloading content.

        Cheap metadata-only call. Use this when you need to know the truly latest
        year before deciding whether a cache hit (e.g., embedding sentinel) is
        actually current.
        """
        self._validate_filing_type(filing_type)
        return self._downloader.get_latest_fiscal_year(ticker, filing_type)

    def download_raw(
        self,
        ticker: str,
        filing_type: str,
        fiscal_year: int | None = None,
    ) -> RawFiling:
        """Download raw filing HTML from EDGAR.

        Public entry point for callers that want the EDGAR fetch step alone —
        e.g., the JIT path in :mod:`sec_dense_pipeline.retriever`, which wraps
        each step with its own Langfuse span. Bypasses cache and retry; use
        :meth:`process` for the cached + retried convenience path.
        """
        self._validate_filing_type(filing_type)
        return self._downloader.download(ticker.strip().upper(), filing_type, fiscal_year)

    def parse_raw(self, raw: RawFiling, filing_type: str) -> ParsedFiling:
        """Convert raw filing HTML to cleaned Markdown and persist to the store.

        Public entry point for callers that already have a :class:`RawFiling`
        (e.g., from :meth:`download_raw`). Wraps preprocessor → converter →
        cleaner → :class:`ParsedFiling` → store.save.
        """
        self._validate_filing_type(filing_type)
        cleaned_html = self._preprocessor.preprocess(raw.raw_html)
        markdown, converter_name = convert_with_fallback(
            cleaned_html, self._converter, self._fallback_converter
        )
        markdown = self._markdown_cleaner.clean(markdown)

        metadata = FilingMetadata(
            ticker=raw.ticker,
            cik=raw.cik,
            company_name=raw.company_name,
            filing_type=FilingType(filing_type),
            filing_date=raw.filing_date,
            fiscal_year=raw.fiscal_year,
            accession_number=raw.accession_number,
            source_url=raw.source_url,
            parsed_at=datetime.now(UTC).isoformat(),
            converter=converter_name,
        )
        filing = ParsedFiling(metadata=metadata, markdown_content=markdown)
        self._store.save(filing)
        return filing

    def _execute_with_retry(
        self,
        ticker: str,
        filing_type: str,
        fiscal_year: int | None = None,
        force: bool = False,
        on_retry: RetryCallback | None = None,
    ) -> tuple[ParsedFiling, bool]:
        """Run :meth:`_process_internal` with exponential-backoff retry.

        Shared retry helper for both :meth:`process` and
        :meth:`_process_with_retry`.  Retries only on :class:`TransientError`
        (network blips, SEC 5xx); non-transient errors propagate immediately
        so the caller can decide what to do with them.  Returns
        ``(filing, from_cache)`` so the batch path can report cache hits.
        """
        last_error: Exception | None = None
        for attempt in range(_MAX_BATCH_RETRIES):
            try:
                return self._process_internal(ticker, filing_type, fiscal_year, force)
            except TransientError as exc:
                last_error = exc
                if attempt < _MAX_BATCH_RETRIES - 1:
                    if on_retry is not None:
                        on_retry(attempt + 1, _MAX_BATCH_RETRIES, exc)
                    delay = _RETRY_BASE_DELAY * (2**attempt)
                    logger.warning(
                        "Transient error for %s (attempt %d/%d), retrying in %.1fs: %s",
                        ticker,
                        attempt + 1,
                        _MAX_BATCH_RETRIES,
                        delay,
                        exc,
                    )
                    time.sleep(delay)
        raise last_error  # type: ignore[misc]

    def _process_internal(
        self,
        ticker: str,
        filing_type: str,
        fiscal_year: int | None = None,
        force: bool = False,
    ) -> tuple[ParsedFiling, bool]:
        """Execute one full pipeline pass: download → preprocess → convert → store.

        Two-phase cache check is intentional:

        1. If ``fiscal_year`` is supplied we can look up the cache directly
           without contacting SEC at all.
        2. If ``fiscal_year`` is ``None`` we have to download the filing index
           first to learn the latest year, then re-check the cache against
           that resolved year before doing the (expensive) full download.

        Always wraps the converter result in a :class:`ParsedFiling` and
        persists it via the configured ``FilingStore``.  Returns
        ``(filing, from_cache)``.
        """
        ticker = ticker.upper()
        self._validate_filing_type(filing_type)

        if fiscal_year is not None and not force:
            cached = self._store.get(ticker, FilingType(filing_type), fiscal_year)
            if cached is not None:
                return cached, True

        raw = self.download_raw(ticker, filing_type, fiscal_year)

        if not force:
            cached = self._store.get(ticker, FilingType(filing_type), raw.fiscal_year)
            if cached is not None:
                return cached, True

        filing = self.parse_raw(raw, filing_type)
        return filing, False

    def process_batch(
        self,
        tickers: list[str],
        filing_type: str,
    ) -> dict[str, BatchResult]:
        """Process multiple tickers, isolating failures per ticker.

        Multi-ticker entry point used by the ``batch`` CLI command.  Always
        downloads the latest fiscal year (``fiscal_year=None``) and never
        forces re-download (``force=False``) — batch mode is meant for
        bulk-warming the local cache.

        Unlike :meth:`process`, this method never raises: per-ticker errors
        are captured into the corresponding :class:`BatchResult` so a single
        bad ticker does not abort the rest of the run.  Returns a dict keyed
        by upper-cased ticker.
        """
        results: dict[str, BatchResult] = {}
        for ticker in tickers:
            normalized = ticker.upper()
            results[normalized] = self._process_with_retry(normalized, filing_type)
        return results

    def _process_with_retry(self, ticker: str, filing_type: str) -> BatchResult:
        """Per-ticker wrapper for the batch path: catch and box errors.

        Calls :meth:`_execute_with_retry` (which already does transient-error
        retry) and converts both success and any :class:`SECPipelineError`
        into a :class:`BatchResult`.  Used only by :meth:`process_batch` —
        the single-filing path lets exceptions propagate to the caller.
        """
        try:
            filing, from_cache = self._execute_with_retry(ticker, filing_type)
            return BatchResult(
                status="success", filing=filing, error=None, from_cache=from_cache
            )
        except SECPipelineError as exc:
            return BatchResult(
                status="error", filing=None, error=exc, from_cache=False
            )

    @staticmethod
    def _validate_filing_type(filing_type: str) -> None:
        """Reject unsupported filing types early with a domain-specific error.

        Currently only ``"10-K"`` is supported (see :class:`FilingType`).
        Called at the top of :meth:`_process_internal` so we fail fast before
        spending a network round-trip on an invalid request.
        """
        if filing_type not in FilingType.__members__.values():
            raise UnsupportedFilingTypeError(f"Unsupported filing type: {filing_type}")
