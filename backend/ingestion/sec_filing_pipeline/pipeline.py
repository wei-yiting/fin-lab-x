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
    SECPipelineError,
    TransientError,
    UnsupportedFilingTypeError,
)
from backend.ingestion.sec_filing_pipeline.filing_store import FilingStore, LocalFilingStore
from backend.ingestion.sec_filing_pipeline.html_preprocessor import HTMLPreprocessor
from backend.ingestion.sec_filing_pipeline.html_to_md_converter import (
    HTMLToMarkdownConverter,
    HtmlToMarkdownAdapter,
    MarkdownifyAdapter,
    convert_with_fallback,
)
from backend.ingestion.sec_filing_pipeline.sec_downloader import SECDownloader

logger = logging.getLogger(__name__)

_MAX_BATCH_RETRIES = 3
_RETRY_BASE_DELAY = 1.0


@dataclass(frozen=True)
class BatchResult:
    status: Literal["success", "error"]
    filing: ParsedFiling | None
    error: str | None
    from_cache: bool


class SECFilingPipeline:
    def __init__(
        self,
        downloader: SECDownloader,
        preprocessor: HTMLPreprocessor,
        converter: HTMLToMarkdownConverter,
        fallback_converter: HTMLToMarkdownConverter,
        store: FilingStore,
    ) -> None:
        self._downloader = downloader
        self._preprocessor = preprocessor
        self._converter = converter
        self._fallback_converter = fallback_converter
        self._store = store

    @classmethod
    def create(cls) -> SECFilingPipeline:
        return cls(
            downloader=SECDownloader(),
            preprocessor=HTMLPreprocessor(),
            converter=HtmlToMarkdownAdapter(),
            fallback_converter=MarkdownifyAdapter(),
            store=LocalFilingStore(),
        )

    def process(
        self,
        ticker: str,
        filing_type: str,
        fiscal_year: int | None = None,
        force: bool = False,
    ) -> ParsedFiling:
        filing, _ = self._process_internal(ticker, filing_type, fiscal_year, force)
        return filing

    def _process_internal(
        self,
        ticker: str,
        filing_type: str,
        fiscal_year: int | None = None,
        force: bool = False,
    ) -> tuple[ParsedFiling, bool]:
        ticker = ticker.upper()
        self._validate_filing_type(filing_type)

        if fiscal_year is not None and not force:
            cached = self._store.get(ticker, FilingType(filing_type), fiscal_year)
            if cached is not None:
                return cached, True

        raw = self._downloader.download(ticker, filing_type, fiscal_year)

        if fiscal_year is None and not force:
            cached = self._store.get(ticker, FilingType(filing_type), raw.fiscal_year)
            if cached is not None:
                return cached, True

        cleaned_html = self._preprocessor.preprocess(raw.raw_html)
        markdown, converter_name = convert_with_fallback(
            cleaned_html, self._converter, self._fallback_converter
        )

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
        return filing, False

    def process_batch(
        self,
        tickers: list[str],
        filing_type: str,
    ) -> dict[str, BatchResult]:
        results: dict[str, BatchResult] = {}
        for ticker in tickers:
            normalized = ticker.upper()
            results[normalized] = self._process_with_retry(normalized, filing_type)
        return results

    def _process_with_retry(self, ticker: str, filing_type: str) -> BatchResult:
        last_error: Exception | None = None
        for attempt in range(_MAX_BATCH_RETRIES):
            try:
                filing, from_cache = self._process_internal(ticker, filing_type)
                return BatchResult(
                    status="success", filing=filing, error=None, from_cache=from_cache
                )
            except TransientError as exc:
                last_error = exc
                if attempt < _MAX_BATCH_RETRIES - 1:
                    delay = _RETRY_BASE_DELAY * (2**attempt)
                    logger.warning(
                        "Transient error for %s (attempt %d/%d), retrying in %.1fs: %s",
                        ticker, attempt + 1, _MAX_BATCH_RETRIES, delay, exc,
                    )
                    time.sleep(delay)
            except SECPipelineError as exc:
                return BatchResult(
                    status="error", filing=None, error=str(exc), from_cache=False
                )

        return BatchResult(
            status="error", filing=None, error=str(last_error), from_cache=False
        )

    @staticmethod
    def _validate_filing_type(filing_type: str) -> None:
        if filing_type not in FilingType.__members__.values():
            raise UnsupportedFilingTypeError(
                f"Unsupported filing type: {filing_type}"
            )
