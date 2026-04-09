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

Runs the v2 dense embedding pipeline end-to-end: reads cleaned SEC 10-K markdown files, chunks them with structural awareness, generates OpenAI embeddings, and upserts the resulting vectors into a Qdrant collection.

### Usage

```bash
uv run python backend/scripts/embed_sec_filings.py \
  --cache-dir data/sec_filings \
  --collection sec_filings
```

### When to run

- After downloading or updating SEC filing markdown files
- When re-indexing with changed chunking or embedding parameters
- To populate a fresh Qdrant instance for development or evaluation

## `validate_sec_eval_dataset.py`

Validates the SEC evaluation dataset by checking that expected queries return relevant chunks from the Qdrant vector store. Reports recall and precision metrics against a ground-truth mapping.

### Usage

```bash
uv run python backend/scripts/validate_sec_eval_dataset.py \
  --eval-dataset data/sec_eval_dataset.json \
  --collection sec_filings
```

### When to run

- After changing chunking strategy, embedding model, or retrieval parameters
- When adding new ground-truth entries to the evaluation dataset
- As a smoke test after re-indexing the vector store
