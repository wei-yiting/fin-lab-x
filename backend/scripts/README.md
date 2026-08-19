# Backend Scripts

CLI tools used during development and operations. Not imported by production code.

## Main Scripts

### `embed_sec_filings.py`

Batch ingest SEC 10-K filings into the dense vector pipeline (`sec_dense_pipeline`, the structured-contract pipeline — not the frozen `_html` baseline). For each ticker, calls `parse_filing_with_retry()` (filing-store cache first, EDGAR on miss) and then `ingest_filing_with_retry()` to chunk, embed, and upsert into Qdrant.

```bash
# Latest fiscal year per ticker (resolved from EDGAR)
uv run python -m backend.scripts.embed_sec_filings NVDA AAPL INTC

# Specific year
uv run python -m backend.scripts.embed_sec_filings NVDA --fiscal-year 2024
```

| Argument | Required | Description |
|---|---|---|
| `tickers` (positional) | Yes | One or more ticker symbols to ingest |
| `--fiscal-year` | No | Fiscal year to ingest (default: each ticker's latest 10-K) |

The summary table reports the resolved fiscal year per ticker, so an omitted `--fiscal-year` still tells the operator which year was actually ingested.

Both the parse and ingest steps carry a single retry on transient failures via `retry_transient` (ADR-0013); a failure that survives the retry does not abort the batch — it is recorded as `failed` in the summary and the script exits with code 1.

The script intentionally runs without Braintrust tracing — observability lives in the `search()` JIT path only.

When to run:

- After changing chunking or embedding parameters
- When pre-warming Qdrant for a new dev environment or eval run
- When EDGAR publishes a new fiscal year for a covered ticker

### `refresh_model_context_registry.py`

Regenerates the committed `backend/agent_engine/utils/model_context_registry.yaml` from `litellm` model metadata. Reads every `versions/*/orchestrator_config.yaml`, collects the unique model names, and writes back a fresh `(context_window, source)` mapping. Existing `source: manual` entries are preserved on lookup failures; unknown models are logged and skipped.

```bash
uv run --extra dev python backend/scripts/refresh_model_context_registry.py
```

Dev-only because `litellm` is a ~80MB dependency we deliberately keep out of the production path — the runtime reads the materialized YAML directly.

When to run:

- After adding a new `model.name` to any version's `orchestrator_config.yaml`
- When `litellm` publishes updated context-window metadata for an existing model

## Validation Scripts

Read-only inspection tools that do not modify state. See [`backend/scripts/validation/README.md`](validation/README.md) for details.

- `validation/validate_sec_md_cleanup.py` — surface boilerplate patterns in cached SEC markdown
- `validation/validate_sec_eval_dataset.py` — check the SEC retrieval eval dataset against a live Qdrant collection
