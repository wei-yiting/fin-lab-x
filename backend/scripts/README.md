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
```

| Argument | Required | Description |
|---|---|---|
| `tickers` (positional) | Yes | One or more ticker symbols to ingest |
| `--year` | No | Fiscal year to ingest (default: EDGAR's latest) |

Transient-failure retry lives inside `SECFilingPipeline.process` (not this script); failed tickers appear as `failed` in the summary and the script exits with code 1.

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

### `sweep_section_detection.py`

Pure-observation sweep (DEV-176): for each ticker's latest 10-K, reads edgartools' raw `Section.detection_method` (`toc`/`heading`/`pattern`/`html_fallback`/`unknown` — never surfaced by `sec_text_pipeline` itself) directly off `fetch_filing_bundle`, then cross-checks the real `parse_filing()` outcome. Never modifies pipeline code; `parse_filing()` still populates the shared `data/sec_text/` filing-store cache as a side effect, same as any other caller.

```bash
# Default: the DEV-176 sweep corpus (DEV-162's 16-ticker grid + AMD)
uv run python -m backend.scripts.sweep_section_detection

# Ad hoc subset
uv run python -m backend.scripts.sweep_section_detection AMD NVDA
```

| Argument | Required | Description |
|---|---|---|
| `tickers` (positional) | No | Ticker symbols to sweep (default: the 17-ticker DEV-176 sweep corpus) |

Prints a per-ticker table, raw section name shapes, a detection-method distribution (ticker-level and section-level), and the degraded-ticker list. Exits 1 if any ticker's detection method could not be determined (fetch failure).

When to run:

- Re-checking the degraded-ingest trigger rate after an edgartools upgrade (v6.0 is expected to remove the legacy fallback strategies)
- Extending the sweep corpus with new tickers

## Validation Scripts

Read-only inspection tools that do not modify state. See [`backend/scripts/validation/README.md`](validation/README.md) for details.

- `validation/validate_sec_md_cleanup.py` — surface boilerplate patterns in cached SEC markdown
- `validation/validate_sec_eval_dataset.py` — check the SEC retrieval eval dataset against a live Qdrant collection
