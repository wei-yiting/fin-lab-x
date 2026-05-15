"""yfinance ingestion entrypoint.

`refresh_yfinance_ticker` is the only public function: one call ingests
``info`` + quarterly + annual statements for a single ticker, upserts the
four owned tables, and writes one ``ingestion_runs`` audit row (success or
error).

Inline retry decorator lives here (not in foundation ``quant_retry``) because
it is closure-bound to the per-call ``RunReport`` — it bumps ``retry_count``
and emits per-attempt OTel events scoped to the enclosing ``traced_span``.
"""

import functools
import time
from collections.abc import Callable
from datetime import date
from typing import TypeVar

from duckdb import DuckDBPyConnection
from opentelemetry import trace as otel_trace

from backend.ingestion.quant_data_pipeline.duck_db.upsert import upsert_rows
from backend.ingestion.quant_data_pipeline.ingestion_run_tracker import (
    RunReport,
    track_ingestion_run,
)
from backend.ingestion.quant_data_pipeline.quant_pipeline_errors import (
    TransientError,
)
from backend.utils.span_tracing import traced_span

from . import constants, dto_builder, yfinance_client

_T = TypeVar("_T")

# ``companies.sector`` / ``companies.industry`` are the only nullable columns
# we want to coalesce — a transient None from Yahoo must not blank out a
# previously-stored value.
COMPANIES_COALESCE_COLS: tuple[str, ...] = ("sector", "industry")

# ``market_valuations`` coalesces every non-PK column: each is independently
# nullable in yfinance, and intraday NaN flashes are common.
MARKET_VALUATIONS_COALESCE_COLS: tuple[str, ...] = (
    "market_cap_usd",
    "enterprise_value_usd",
    "trailing_price_to_earnings",
    "forward_price_to_earnings",
    "price_to_book_ratio",
    "price_to_sales_trailing_12m",
    "ev_to_ebitda_ratio",
    "trailing_peg_ratio",
    "dividend_yield_pct",
    "beta",
    "held_pct_institutions",
)


def _retry_with_counter(
    report: RunReport,
    max_attempts: int | None = None,
    base_delay: float | None = None,
) -> Callable[[Callable[..., _T]], Callable[..., _T]]:
    """Build a retry decorator that mutates ``report.metadata['retry_count']``.

    ``retry_count`` increments only for retries that actually happen; the
    terminal-raise attempt does NOT bump the counter. Per-attempt OTel events
    are added to the enclosing ``traced_span`` when one is active, otherwise
    skipped (no untraced batch run shows up on Langfuse).

    ``max_attempts`` / ``base_delay`` default to the module-level
    ``constants`` values read at call time (not import time) so tests can
    ``monkeypatch.setattr(constants, ...)`` without having to thread the
    override through every call site.
    """
    if max_attempts is None:
        max_attempts = constants.RETRY_MAX_ATTEMPTS
    if base_delay is None:
        base_delay = constants.RETRY_BASE_DELAY_SECONDS

    def decorator(fn: Callable[..., _T]) -> Callable[..., _T]:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs) -> _T:
            for attempt in range(max_attempts):
                current_span = otel_trace.get_current_span()
                span_active = current_span.get_span_context().is_valid
                try:
                    result = fn(*args, **kwargs)
                    if span_active:
                        current_span.add_event(
                            "fetch_attempt",
                            attributes={"attempt": attempt, "status": "success"},
                        )
                    return result
                except TransientError as exc:
                    if span_active:
                        current_span.add_event(
                            "fetch_attempt",
                            attributes={
                                "attempt": attempt,
                                "status": "error",
                                "error_class": type(exc).__name__,
                            },
                        )
                    if attempt + 1 >= max_attempts:
                        raise
                    report.metadata["retry_count"] = (
                        report.metadata.get("retry_count", 0) + 1
                    )
                    time.sleep(base_delay * (2**attempt))
            # Unreachable: the loop either returns or re-raises before exit.
            raise RuntimeError("unreachable: retry loop exited without return/raise")

        return wrapper

    return decorator


def refresh_yfinance_ticker(
    conn: DuckDBPyConnection, ticker: str,
) -> RunReport:
    """Idempotent yfinance fetch + upsert for one ticker.

    One audit row + up to four upserts per call. On a stage failure the
    audit row still records the partial ``rows_per_table`` plus pacing,
    ``retry_count``, and the failed stage name in ``error_stage``.
    """
    ticker = ticker.strip().upper()
    today = date.today()

    with track_ingestion_run(conn, "yfinance", ticker) as report:
        report.metadata = {
            "periods_covered": {},
            "rows_per_table": {},
            "missing_fields": [],
            "pacing": {},
            "retry_count": 0,
            "error_stage": None,
        }
        retry = _retry_with_counter(report)
        calls_before, sleep_before = yfinance_client.get_pacing_stats()

        try:
            # ---- Stage 1: info → companies + market_valuations ----
            report.metadata["error_stage"] = "info"
            with traced_span("yf_fetch_info", input={"ticker": ticker}):
                info = retry(yfinance_client.fetch_info)(ticker)

            report.metadata["error_stage"] = "normalize"
            company, missing_co = dto_builder.build_company_row(info, ticker)
            upsert_rows(
                conn,
                "companies",
                ["ticker"],
                [company],
                coalesce_columns=COMPANIES_COALESCE_COLS,
            )
            report.rows_written_total += 1
            report.metadata["rows_per_table"]["companies"] = 1

            mv, missing_mv = dto_builder.build_market_valuation_row(
                info, ticker, today,
            )
            upsert_rows(
                conn,
                "market_valuations",
                ["ticker", "as_of_date"],
                [mv],
                coalesce_columns=MARKET_VALUATIONS_COALESCE_COLS,
            )
            report.rows_written_total += 1
            report.metadata["rows_per_table"]["market_valuations"] = 1

            # ---- Stage 2: quarterly ----
            report.metadata["error_stage"] = "quarterly"
            with traced_span("yf_fetch_quarterly_statements"):
                df_q = retry(yfinance_client.fetch_quarterly_statements)(ticker)
            rows_q, missing_q = dto_builder.build_quarterly_rows(df_q, company)
            upsert_rows(
                conn,
                "quarterly_financials",
                ["ticker", "fiscal_year", "fiscal_quarter"],
                rows_q,
            )
            report.rows_written_total += len(rows_q)
            report.metadata["rows_per_table"]["quarterly_financials"] = len(rows_q)
            report.metadata["periods_covered"]["quarterly"] = [
                f"{r.fiscal_year}Q{r.fiscal_quarter}" for r in rows_q
            ]

            # ---- Stage 3: annual ----
            report.metadata["error_stage"] = "annual"
            with traced_span("yf_fetch_annual_statements"):
                df_a = retry(yfinance_client.fetch_annual_statements)(ticker)
            rows_a, missing_a = dto_builder.build_annual_rows(df_a, company)
            upsert_rows(
                conn,
                "annual_financials",
                ["ticker", "fiscal_year"],
                rows_a,
            )
            report.rows_written_total += len(rows_a)
            report.metadata["rows_per_table"]["annual_financials"] = len(rows_a)
            report.metadata["periods_covered"]["annual"] = [
                r.fiscal_year for r in rows_a
            ]

            report.metadata["error_stage"] = None
            report.metadata["missing_fields"] = sorted(
                set(missing_co + missing_mv + missing_q + missing_a)
            )
            return report
        finally:
            # Mutate metadata BEFORE the ``with track_ingestion_run`` block
            # exits — its ``__exit__`` reads ``report.metadata`` to persist
            # the audit row, so pacing must land here, not after.
            calls_after, sleep_after = yfinance_client.get_pacing_stats()
            report.metadata["pacing"] = {
                "calls": calls_after - calls_before,
                "total_sleep_seconds": round(sleep_after - sleep_before, 2),
            }
