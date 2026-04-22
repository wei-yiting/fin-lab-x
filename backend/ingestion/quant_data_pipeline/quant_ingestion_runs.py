import json
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from duckdb import DuckDBPyConnection


@dataclass
class RunReport:
    rows_written_total: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


def _insert_run(
    conn: DuckDBPyConnection,
    run_id: str,
    pipeline: str,
    ticker: str,
    target_filing_type: str | None,
    target_fiscal_year: int | None,
    target_fiscal_quarter: int | None,
    target_accession_number: str | None,
    started_at: datetime,
    finished_at: datetime,
    status: str,
    error_class: str | None,
    error_message: str | None,
    rows_written_total: int,
    metadata: dict[str, Any],
) -> None:
    conn.execute(
        """
        INSERT INTO ingestion_runs (
            run_id, pipeline, ticker,
            target_filing_type, target_fiscal_year, target_fiscal_quarter, target_accession_number,
            started_at, finished_at,
            status, error_class, error_message,
            rows_written_total, metadata
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            run_id,
            pipeline,
            ticker,
            target_filing_type,
            target_fiscal_year,
            target_fiscal_quarter,
            target_accession_number,
            started_at,
            finished_at,
            status,
            error_class,
            error_message,
            rows_written_total,
            json.dumps(metadata),
        ],
    )


@contextmanager
def ingestion_run(
    conn: DuckDBPyConnection,
    pipeline: str,
    ticker: str,
    *,
    target_filing_type: str | None = None,
    target_fiscal_year: int | None = None,
    target_fiscal_quarter: int | None = None,
    target_accession_number: str | None = None,
) -> Iterator[RunReport]:
    """Audit wrapper: always writes one ingestion_runs row (success or error)."""
    run_id = str(uuid4())
    started_at = datetime.now(UTC)
    report = RunReport()
    try:
        yield report
    except Exception as exc:
        _insert_run(
            conn,
            run_id,
            pipeline,
            ticker,
            target_filing_type,
            target_fiscal_year,
            target_fiscal_quarter,
            target_accession_number,
            started_at,
            datetime.now(UTC),
            status="error",
            error_class=type(exc).__name__,
            error_message=str(exc),
            rows_written_total=0,
            metadata=report.metadata,
        )
        raise
    _insert_run(
        conn,
        run_id,
        pipeline,
        ticker,
        target_filing_type,
        target_fiscal_year,
        target_fiscal_quarter,
        target_accession_number,
        started_at,
        datetime.now(UTC),
        status="success",
        error_class=None,
        error_message=None,
        rows_written_total=report.rows_written_total,
        metadata=report.metadata,
    )
