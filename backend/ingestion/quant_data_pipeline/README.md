# quant_data_pipeline

## Purpose

Shared infrastructure for yfinance and SEC XBRL quant ETL pipelines: DuckDB connection/schema, Pydantic row DTOs, idempotent upsert, retry, audit trail, and ticker universe.

---

## Quick Start

```python
from backend.ingestion.quant_data_pipeline.duck_db.connection import get_connection
from backend.ingestion.quant_data_pipeline.duck_db.row_models import CompanyRow
from backend.ingestion.quant_data_pipeline.duck_db.upsert import upsert_rows
from backend.ingestion.quant_data_pipeline.ingestion_run_tracker import (
    track_ingestion_run,
)

with get_connection(":memory:") as conn:
    with track_ingestion_run(conn, "yfinance", "MSFT") as report:
        report.rows_written_total = upsert_rows(
            conn, "companies", ["ticker"],
            [CompanyRow(
                ticker="MSFT", company_name="Microsoft Corp",
                sector="Technology", industry="Software",
                fy_end_month=6, fy_end_day=30,
            )],
        )
```

`get_connection(":memory:")` applies `schema.sql` automatically. `track_ingestion_run` writes one audit row to `ingestion_runs` on exit — success or exception.

---

## Public API

| Symbol | Import path | Description |
|---|---|---|
| `get_connection` | `.duck_db.connection` | Open (or create) a DuckDB database and apply `schema.sql`. |
| `upsert_rows` | `.duck_db.upsert` | Bulk-upsert a list of Pydantic row DTOs into a named table; returns row count. |
| `CompanyRow` | `.duck_db.row_models` | DTO for the `companies` table (ticker metadata, fiscal year-end). |
| `MarketValuationRow` | `.duck_db.row_models` | DTO for the `market_valuations` table (market cap, ratios, beta). |
| `YFinanceQuarterlyRow` | `.duck_db.row_models` | DTO for the `quarterly_financials` table (income, balance sheet, cash flow). |
| `YFinanceAnnualRow` | `.duck_db.row_models` | DTO for the `annual_financials` table (same schema as quarterly, no `fiscal_quarter`). |
| `IngestionRunRow` | `.duck_db.row_models` | DTO for the `ingestion_runs` table; used for direct audit inserts (advanced). |
| `normalize_fiscal_period` | `.calendar_to_fiscal_period` | Convert a calendar `period_end` date to `(fiscal_year, fiscal_quarter)` using FYE month. |
| `load_ticker_universe` | `.ticker_universe_loader` | Load the canonical ticker list from `config/ticker_universe.yaml`. |
| `track_ingestion_run` | `.ingestion_run_tracker` | Context manager that writes one `ingestion_runs` audit row (success or error). |
| `RunReport` | `.ingestion_run_tracker` | Mutable dataclass yielded by `track_ingestion_run`; caller sets `rows_written_total` and `metadata`. |
| `with_retry` | `.quant_retry` | Decorator that retries `TransientError` subclasses with exponential backoff. |
| `QuantPipelineError` | `.quant_pipeline_errors` | Base exception for all pipeline errors. |
| `TransientError` | `.quant_pipeline_errors` | Retryable: network blip, 5xx, rate limit. |
| `TickerNotFoundError` | `.quant_pipeline_errors` | Non-retryable: ticker absent from data source. |
| `DataValidationError` | `.quant_pipeline_errors` | Non-retryable: extracted data violates schema invariants. |
| `ConfigurationError` | `.quant_pipeline_errors` | Non-retryable: missing env var or invalid universe YAML. |
| `SchemaError` | `.quant_pipeline_errors` | Non-retryable: `schema.sql` missing or failed to apply at connect time. |
| `traced_span` | `backend.utils.span_tracing` | **Cross-pipeline utility** (not in this package). Yields a Langfuse span when an outer trace is active; no-op otherwise. |

---

## Conventions

- **Single writer**: DuckDB does not support concurrent writers. Batch CLI scripts must serialize across tickers (e.g., sequential loop, not `multiprocessing`).
- **`updated_at` is managed by `upsert_rows()`**: Do not declare `updated_at` in any row DTO. The upsert sets it to `now()` on every write.
- **`span_tracing.py` lives in `backend/utils/`** (cross-pipeline utility shared with the SEC dense pipeline). `quant_retry.py` lives in this package because retry behavior is pipeline-scoped.
- **`get_connection` signature**: Pass an explicit path or `":memory:"` for tests. In production the path falls back to `$DUCKDB_PATH` env var, then `data/quant.db`.
- **Audit semantics**: `track_ingestion_run()` records `report.rows_written_total` on both success and error paths. Callers should increment only AFTER a successful write (e.g., `report.rows_written_total += upsert_rows(...)`), so partial-write counts remain accurate when an exception interrupts mid-batch.

---

## Adding a New DTO

Declare Pydantic fields that match the DDL column names exactly; omit `updated_at` (it is managed by `upsert_rows()`). Pass the correct `pk_columns` list to `upsert_rows()` so the `ON CONFLICT` clause resolves correctly. Fields that belong only to one subsystem (e.g., SEC-only XBRL columns) should live in the subsystem's own DTO rather than in the shared row models here.

---

## Extending the Error Taxonomy

Subsystem code should subclass one of the four leaf error classes — `TransientError`, `TickerNotFoundError`, `DataValidationError`, or `ConfigurationError` — rather than `QuantPipelineError` directly. Prefix the class name with the pipeline to avoid collision across subsystems (e.g., `YFinanceRateLimitError(TransientError)`, `SecXbrlParseError(DataValidationError)`).

---

## Testing

```bash
uv run pytest backend/tests/ingestion/quant_data_pipeline/
```

`conftest.py` ships a `tmp_duckdb` fixture that yields an in-memory `DuckDBPyConnection` with the schema applied. Subsystem test files can reuse it by adding:

```python
pytest_plugins = ["backend.tests.ingestion.quant_data_pipeline.conftest"]
```

or by importing the fixture directly.

---

## Schema Evolution

During the iteration phase, edit `duck_db/schema.sql`, delete the local `data/quant.db`, and re-run the ETL. There is no Alembic migration layer yet; the schema is applied in full on every `get_connection()` call via `CREATE TABLE IF NOT EXISTS` statements.
