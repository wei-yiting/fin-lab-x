# Validation Scripts

Read-only diagnostic tools for SEC pipeline data quality. Run on demand; never modify state.

## `validate_sec_md_cleanup.py`

Walks a `LocalFilingStore` cache directory, runs the cleanup-rule detectors (page separators, Part III stubs, heading variants, false-positive risks) against every cached 10-K markdown, and writes a report. Used to surface new boilerplate patterns or regressions before modifying `MarkdownCleaner`.

```bash
uv run python -m backend.scripts.validation.validate_sec_md_cleanup \
  --cache-dir data/sec_filings \
  --output artifacts/current/validation_cleanup_patterns.md
```

Both arguments are required. Output goes to `artifacts/` (gitignored).

When to run:

- Before or after changing a cleanup rule — diff baseline vs. updated report
- After downloading new tickers — check for unseen boilerplate variants
- When investigating a filing-specific regression

## `validate_sec_eval_dataset.py`

Validates the SEC retrieval eval dataset against a live Qdrant collection. Checks that `expected_header_paths` entries have matching chunks and reports near-miss warnings for case mismatches.

```bash
uv run python -m backend.scripts.validation.validate_sec_eval_dataset
uv run python -m backend.scripts.validation.validate_sec_eval_dataset --csv path/to/dataset.csv
```

| Argument | Required | Description |
|---|---|---|
| `--csv` | No | Path to dataset CSV (default: `backend/evals/scenarios/sec_retrieval/dataset.csv`) |

Collection and Qdrant URL are configured via environment variables `SEC_QDRANT_COLLECTION` and `QDRANT_URL`.

When to run:

- After changing chunking strategy, embedding model, or retrieval parameters
- When adding new ground-truth entries to the evaluation dataset
- As a smoke test after re-indexing the vector store
