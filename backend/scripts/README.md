# Backend Scripts

One-off analysis and developer tools. Not imported by production code.

## `validate_sec_md_cleanup.py`

Inspects cached SEC 10-K markdown files and reports how each filing's boilerplate patterns (page separators, Part III stubs, heading variants) align with the cleanup rules in `markdown_cleaner.py`. Does not modify any files.

### Usage

```bash
uv run python backend/scripts/validate_sec_md_cleanup.py \
  --cache-dir data/sec_filings \
  --output artifacts/current/validation_cleanup_patterns.md
```

Both arguments are required. Output goes to `artifacts/` (gitignored).

### When to run

- Before or after changing a cleanup rule — diff baseline vs. updated report
- After downloading new tickers — check for unseen boilerplate variants
- When investigating a filing-specific regression

## `embed_sec_filings.py`

Batch ingest SEC filings into the dense vector pipeline. Reads cleaned SEC 10-K markdown files from the local filing store, chunks them with structural awareness, generates OpenAI embeddings, and upserts the resulting vectors into Qdrant.

### Usage

```bash
uv run python -m backend.scripts.embed_sec_filings NVDA AAPL INTC
uv run python -m backend.scripts.embed_sec_filings NVDA --max-retries 5
```

| Argument | Required | Description |
|---|---|---|
| `tickers` (positional) | Yes | One or more ticker symbols to ingest |
| `--max-retries` | No | Max retry attempts per ticker (default: 3) |

### When to run

- After downloading or updating SEC filing markdown files
- When re-indexing with changed chunking or embedding parameters
- To populate a fresh Qdrant instance for development or evaluation

## `validate_sec_eval_dataset.py`

Validates the SEC retrieval eval dataset against a live Qdrant collection. Checks that `expected_header_paths` entries have matching chunks and reports near-miss warnings for case mismatches.

### Usage

```bash
uv run python -m backend.scripts.validate_sec_eval_dataset
uv run python -m backend.scripts.validate_sec_eval_dataset --csv path/to/dataset.csv
```

| Argument | Required | Description |
|---|---|---|
| `--csv` | No | Path to dataset CSV (default: `backend/evals/scenarios/sec_retrieval/dataset.csv`) |

Collection and Qdrant URL are configured via environment variables `SEC_QDRANT_COLLECTION` and `QDRANT_URL`.

### When to run

- After changing chunking strategy, embedding model, or retrieval parameters
- When adding new ground-truth entries to the evaluation dataset
- As a smoke test after re-indexing the vector store
