# Backend Scripts

CLI tools used during development and operations. Not imported by production code.

## Main Scripts

### `embed_sec_filings.py`

Batch ingest SEC 10-K filings into the dense vector pipeline. For each ticker, calls `SECFilingPipeline.process()` (which downloads + parses from EDGAR if not already cached locally) and then runs `ingest_filing()` to chunk, embed, and upsert into Qdrant.

```bash
# Latest fiscal year (resolved from EDGAR)
uv run python -m backend.scripts.embed_sec_filings NVDA AAPL INTC

# Specific year
uv run python -m backend.scripts.embed_sec_filings NVDA --year 2024

# Custom retry count
uv run python -m backend.scripts.embed_sec_filings NVDA AAPL --max-retries 5
```

| Argument | Required | Description |
|---|---|---|
| `tickers` (positional) | Yes | One or more ticker symbols to ingest |
| `--year` | No | Fiscal year to ingest (default: EDGAR's latest) |
| `--max-retries` | No | Max retry attempts per ticker (default: 3) |

The script intentionally runs without Langfuse tracing — observability lives in the `search()` JIT path only.

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
