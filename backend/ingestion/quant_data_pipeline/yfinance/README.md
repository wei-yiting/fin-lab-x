# yfinance ingestion subsystem

## Purpose

This subsystem ingests company metadata, market valuations, and quarterly /
annual financial statements for a single ticker from the yfinance API and
upserts the result into DuckDB. The entry point is
`refresh_yfinance_ticker(conn, ticker) -> RunReport`. One call writes to
four owned tables — `companies`, `market_valuations`, `quarterly_financials`,
`annual_financials` — plus one audit row in `ingestion_runs`.

The subsystem assumes a single DuckDB connection and a single writer per
ticker (DuckDB does not support concurrent writers). It is caller-agnostic:
no global tracing setup, no batch loop, no scheduling. The CLI and any
future agent tool wrap it; the subsystem itself just does one ticker per
call.

---

## Public API

| Symbol | Import path | Description |
|---|---|---|
| `refresh_yfinance_ticker` | `backend.ingestion.quant_data_pipeline.yfinance` | Idempotent fetch + upsert for one ticker. Returns `RunReport`. |
| `YFINANCE_OWNED_COLUMNS` | `backend.ingestion.quant_data_pipeline.yfinance` | `frozenset[str]` of columns this subsystem writes. Cross-subsystem upsert isolation boundary — SEC pipeline must NOT include any column in this set in its `DO UPDATE SET` clause. |
| `YFinanceRateLimitError` | `backend.ingestion.quant_data_pipeline.yfinance` | Retryable. Yahoo 429 / cookie-limited. |
| `YFinanceTickerNotFoundError` | `backend.ingestion.quant_data_pipeline.yfinance` | Non-retryable. Ticker absent from Yahoo. |
| `YFinanceEmptyResponseError` | `backend.ingestion.quant_data_pipeline.yfinance` | Non-retryable. Required field missing (`lastFiscalYearEnd`, `longName`, or every period's `Total Revenue`). |

---

## Caller models

The subsystem supports two callers; both wrap the same `refresh_yfinance_ticker`.

**CLI batch** — sequential loop across the ticker universe, no Langfuse:

```
python -m backend.ingestion.quant_data_pipeline refresh-yfinance [TICKER...]
```

Without explicit tickers the CLI reads the configured universe YAML. Per-ticker
failures are isolated (logged + continue); exit code is 0 if at least one
ticker succeeded, non-zero only if every ticker failed.

**Agent JIT** — call `refresh_yfinance_ticker` from inside an `@observe`-decorated
function so the orchestrator's `traced_span` sites emit nested spans into the
caller's Langfuse trace. The subsystem itself does not start a trace; tracing
emit is governed entirely by whether the caller has an active outer span.

---

## Tuning knobs

All four knobs live in `constants.py`:

| Constant | Default | Meaning |
|---|---|---|
| `PACING_MIN_INTERVAL_SECONDS` | `1.0` | Minimum gap between outbound yfinance HTTP calls. Applied per attribute access (each statement DataFrame triggers 3 paced calls). |
| `RETRY_MAX_ATTEMPTS` | `3` | Total attempts (initial + 2 retries) before re-raising a `TransientError`. |
| `RETRY_BASE_DELAY_SECONDS` | `60.0` | Exponential backoff base. Intentionally 60s — Yahoo enforces a long rate-limit window and a shorter base triggers immediate re-block. The foundation `quant_retry` default of 1s is too aggressive for yfinance. |
| `YF_NETWORK_RETRIES` | `2` | yfinance's built-in network retry knob (applied at module import via `yf.config.network.retries`). Layered under the subsystem's own retry decorator. |

The orchestrator's retry decorator reads these from the `constants` module at
call time, so tests can `monkeypatch.setattr(constants, ...)` without
threading overrides through call sites.

---

## `missing_fields` semantics

`report.metadata["missing_fields"]` is the consolidated sorted list of
destination column names that appeared as missing in **at least one** stage's
per-stage missing list. Sources of "missing":

- Info stage: `sector` / `industry` absent or empty string.
- Market valuations stage: any valuation field absent / None / NaN.
- Quarterly stage: union over all materialized quarterly periods of the
  destination columns that were None after coercion.
- Annual stage: same union, over annual periods.

**Cross-source dedup**: if `dividend_yield_pct` is missing on every quarter
and also missing on every annual row, it appears once.

**Partial-coverage caveat**: the union loses per-stage granularity.

> Example: quarterly `Deferred Revenue` is absent for every quarter but the
> annual balance sheet exposes `Current Deferred Revenue` (the second item in
> `DEFERRED_REVENUE_FALLBACK`). The annual stage fills `deferred_revenue_usd`
> for every annual row, but the quarterly stage still marks
> `deferred_revenue_usd` as missing — so it appears in `missing_fields`. Do
> not read that as "every row is NULL"; query the table to confirm coverage.

---

## Test seam — `use_ticker_factory_for_test`

`yfinance_client` exposes a `ContextVar`-scoped factory override so unit
tests can inject a stub `Ticker` without monkeypatching `yfinance.Ticker`
globally. The override is restored automatically on `with`-block exit,
including via exception.

```python
from backend.ingestion.quant_data_pipeline.yfinance.yfinance_client import (
    use_ticker_factory_for_test,
)
from backend.tests.ingestion.quant_data_pipeline.yfinance.stubs import (
    StubTicker, make_stub_factory,
)

stub = StubTicker(info={"longName": "Acme Inc.", "lastFiscalYearEnd": 1735603200})
with use_ticker_factory_for_test(make_stub_factory(stub)):
    refresh_yfinance_ticker(conn, "ACME")
```

Use `StubTicker.raise_on_attrs={"info": SomeError(...)}` to exercise the
`_classify` error-mapping paths per fetch stage.

---

## Live test trigger

Six live tests live in `test_yfinance_api_drift.py` and are SKIPPED in
default CI (filtered out by the `pytest` `addopts` in `pyproject.toml`).
Run manually as a drift watchdog:

```
uv run pytest -m live_yfinance backend/tests/ingestion/quant_data_pipeline/yfinance/
```

Coverage:

- 5 tickers (MSFT, NVDA, KO, AAPL, JPM) — `held_pct_institutions` in `[0, 100]`
  sanity-checks that yfinance has not changed its 0..1 vs percent convention
  (we apply a ×100 converter).
- NVDA `fy_end_day == 25` — pins our `lastFiscalYearEnd` Unix-timestamp →
  `(month, day)` decoder against a non-month-end fiscal close (NVDA closes
  on the last Friday of January).

Expected runtime is roughly 30-60 seconds; output is rate-limit-sensitive
and can be flaky if Yahoo throttles.

---

## Tracing model

The orchestrator opens three sibling spans inside the run:
`yf_fetch_info`, `yf_fetch_quarterly_statements`, `yf_fetch_annual_statements`.
Each one wraps a retry-decorated fetch call, so the retry decorator emits
per-attempt `fetch_attempt` events nested under the active span.

Behavior depends entirely on the caller:

| Caller context | Result |
|---|---|
| Outer `@observe` active (agent JIT) | `traced_span` yields a real Langfuse span; full trace tree per ticker, including retry attempts. |
| No outer trace (CLI batch) | `traced_span` yields a no-op; nothing emitted to Langfuse. |

The CLI deliberately does **not** wrap the per-ticker call in `@observe` —
batch refresh is opaque to Langfuse by design. If you need tracing for a
batch run, wrap the CLI loop yourself at the call site.

---

## Idempotency contract

- Re-running `refresh_yfinance_ticker` for the same ticker replaces row
  contents at the primary key. No history is retained inside these tables.
- `market_valuations` PK is `(ticker, as_of_date)`, so multiple same-day
  refreshes collapse to one row.
- Cross-subsystem upsert: yfinance owns only the columns in
  `YFINANCE_OWNED_COLUMNS`. SEC-only columns on the same row survive a
  yfinance refresh because they are not in the `DO UPDATE SET` clause.
  Symmetrically, SEC writers must exclude every column in
  `YFINANCE_OWNED_COLUMNS` from their own update set.
- `companies.sector` / `companies.industry` and every non-PK column on
  `market_valuations` are coalesced on conflict — a transient `None` /
  `NaN` from yfinance does not blank out a previously-stored value.

---

## Schema-stable audit metadata

`report.metadata` always carries six keys, regardless of which stage failed:

| Key | Type | On success | On error |
|---|---|---|---|
| `periods_covered` | `dict[str, list]` | `{"quarterly": [...], "annual": [...]}`. | Whatever stages completed; absent stages omitted. |
| `rows_per_table` | `dict[str, int]` | One entry per of the 4 owned tables. | Only stages that upserted successfully. |
| `missing_fields` | `list[str]` | Consolidated sorted list (see semantics above). | Empty list — partial-stage missing data is not consolidated on the error path. |
| `pacing` | `dict` | `{"calls": int, "total_sleep_seconds": float}` deltas across this run. | Same; recorded in `finally`. |
| `retry_count` | `int` | Number of retries that actually slept (terminal-raise attempt does not count). | Same. |
| `error_stage` | `str \| None` | `None`. | One of `"info"`, `"normalize"`, `"quarterly"`, `"annual"` — the stage executing when the exception fired. |

The audit row is written in `track_ingestion_run.__exit__`, so all metadata
mutation must happen before the orchestrator's `with` block exits. Pacing
is updated in a `finally` for that reason.

---

## File layout

```
yfinance/
├── README.md                      this file
├── __init__.py                    public surface re-exports
├── constants.py                   tuning knobs (pacing, retry)
├── dto_builder.py                 pure transforms: info / DataFrames → row models
├── field_mappings.py              static lookup tables + YFINANCE_OWNED_COLUMNS
├── refresh_orchestrator.py        entrypoint, retry decorator, stage sequencing
├── yfinance_client.py             I/O layer, pacing, ContextVar test seam
└── yfinance_pipeline_errors.py    3 subsystem error classes

backend/tests/ingestion/quant_data_pipeline/yfinance/
├── conftest.py                    tmp_duckdb fixture, pacing reset
├── stubs.py                       StubTicker + make_stub_factory
├── test_cli_batch.py              CLI subcommand integration
├── test_dst_pacing.py             pacing edge cases
├── test_dto_builder.py            pure-transform unit tests
├── test_field_mappings.py         lookup-table invariants
├── test_idempotent_rerun.py       upsert + cross-subsystem ownership
├── test_journey_hybrid_yfinance.py end-to-end + audit row shape
├── test_market_valuations_coalesce.py NaN-flash coalesce protection
├── test_missing_fields.py         consolidation semantics
├── test_refresh_orchestrator_core.py error_stage + retry decorator
├── test_tracing.py                traced_span emit on / off
├── test_yfinance_api_drift.py     live yfinance smoke (live_yfinance marker)
├── test_yfinance_client.py        _classify + ContextVar test seam
└── test_yfinance_pipeline_errors.py error-class taxonomy
```
