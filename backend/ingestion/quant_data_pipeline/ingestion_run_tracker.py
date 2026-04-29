"""Audit wrapper for quant ingestion runs.

Wraps a fetcher invocation in a context manager that writes one
``ingestion_runs`` row per call (success or error) with caller-supplied
counters and metadata. Callers do not write audit rows directly; they
mutate the yielded ``RunReport`` and the wrapper persists it on exit.
"""

import json
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from duckdb import DuckDBPyConnection
from pydantic import BaseModel


@dataclass
class RunReport:
    rows_written_total: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


class _IngestionRunRow(BaseModel):
    """Typed shape of one ``ingestion_runs`` row.

    Module-private: constructed only by ``track_ingestion_run`` and consumed
    only by ``_record_run``. Pydantic validation enforces required fields
    and column types at the audit boundary.
    """

    run_id: str
    pipeline: str
    ticker: str
    target_filing_type: str | None = None
    target_fiscal_year: int | None = None
    target_fiscal_quarter: int | None = None
    target_accession_number: str | None = None
    started_at: datetime
    finished_at: datetime
    status: str
    error_class: str | None = None
    error_message: str | None = None
    rows_written_total: int = 0
    metadata: dict[str, Any] | None = None


def _record_run(conn: DuckDBPyConnection, row: _IngestionRunRow) -> None:
    data = row.model_dump()
    # JSON column is serialized at the DB boundary; DuckDB's driver does
    # not auto-convert dict → JSON.
    if data.get("metadata") is not None:
        data["metadata"] = json.dumps(data["metadata"])
    columns = list(data.keys())
    placeholders = ", ".join(["?"] * len(columns))
    sql = (
        f"INSERT INTO ingestion_runs ({', '.join(columns)}) "
        f"VALUES ({placeholders})"
    )
    conn.execute(sql, list(data.values()))


@contextmanager
def track_ingestion_run(
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
        _record_run(
            conn,
            _IngestionRunRow(
                run_id=run_id,
                pipeline=pipeline,
                ticker=ticker,
                target_filing_type=target_filing_type,
                target_fiscal_year=target_fiscal_year,
                target_fiscal_quarter=target_fiscal_quarter,
                target_accession_number=target_accession_number,
                started_at=started_at,
                finished_at=datetime.now(UTC),
                status="error",
                error_class=type(exc).__name__,
                error_message=str(exc),
                rows_written_total=report.rows_written_total,
                metadata=report.metadata,
            ),
        )
        raise
    _record_run(
        conn,
        _IngestionRunRow(
            run_id=run_id,
            pipeline=pipeline,
            ticker=ticker,
            target_filing_type=target_filing_type,
            target_fiscal_year=target_fiscal_year,
            target_fiscal_quarter=target_fiscal_quarter,
            target_accession_number=target_accession_number,
            started_at=started_at,
            finished_at=datetime.now(UTC),
            status="success",
            rows_written_total=report.rows_written_total,
            metadata=report.metadata,
        ),
    )
