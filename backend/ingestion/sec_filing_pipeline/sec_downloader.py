from __future__ import annotations

import os

from edgar import Company, CompanyNotFoundError, set_identity

from backend.ingestion.sec_filing_pipeline.filing_models import (
    ConfigurationError,
    FilingNotFoundError,
    FilingType,
    RawFiling,
    TickerNotFoundError,
    TransientError,
    UnsupportedFilingTypeError,
)


class SECDownloader:
    def __init__(self) -> None:
        identity = os.environ.get("EDGAR_IDENTITY")
        if not identity:
            raise ConfigurationError(
                "EDGAR_IDENTITY environment variable is required. "
                "Set it to 'Your Name your@email.com' per SEC EDGAR fair access policy."
            )
        set_identity(identity)

    def download(
        self,
        ticker: str,
        filing_type: str,
        fiscal_year: int | None = None,
    ) -> RawFiling:
        ticker = ticker.upper()

        if filing_type not in FilingType.__members__.values():
            raise UnsupportedFilingTypeError(f"Unsupported filing type: {filing_type}")

        try:
            try:
                company = Company(ticker)
            except CompanyNotFoundError as exc:
                raise TickerNotFoundError(f"Ticker not found: {ticker}") from exc

            filings = company.get_filings(form=filing_type)

            if fiscal_year is not None:
                filings = filings.filter(
                    date=f"{fiscal_year - 1}-01-01:{fiscal_year + 1}-01-01"
                )

            filing = filings.latest()

            if filing is None:
                raise FilingNotFoundError(
                    f"No {filing_type} filing found for {ticker}"
                    + (f" (fiscal year {fiscal_year})" if fiscal_year else "")
                )

            # Fiscal year derives from period_of_report, not filing_date,
            # because filing_date can fall in the next calendar year
            # (e.g., NVDA FY2026 ends 2026-01-25, filed 2026-02-28).
            derived_fy = int(str(filing.period_of_report)[:4])

            if fiscal_year is not None and derived_fy != fiscal_year:
                raise FilingNotFoundError(
                    f"No {filing_type} filing found for {ticker}"
                    f" matching fiscal year {fiscal_year}"
                    f" (closest match: {derived_fy})"
                )

            return RawFiling(
                raw_html=filing.html(),
                ticker=ticker,
                cik=str(company.cik),
                company_name=company.name,
                filing_date=str(filing.filing_date),
                fiscal_year=derived_fy,
                accession_number=filing.accession_number,
                source_url=filing.filing_url,
            )
        except (
            TickerNotFoundError,
            FilingNotFoundError,
            UnsupportedFilingTypeError,
        ):
            raise
        except (ConnectionError, TimeoutError, OSError) as exc:
            raise TransientError(str(exc)) from exc
