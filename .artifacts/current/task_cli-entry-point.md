# Task: SEC Filing Pipeline CLI Entry Point

## Problem

Currently, using the SEC filing pipeline requires writing Python import statements:

```python
from backend.ingestion.sec_filing_pipeline import SECFilingPipeline
p = SECFilingPipeline.create()
result = p.process('AAPL', '10-K', fiscal_year=2025)
```

This is not acceptable for terminal usage. There should be a simple CLI command, comparable to the eval pipeline's entry point.

## Requirements

### Single Filing

```bash
uv run python -m backend.ingestion.sec_filing_pipeline AAPL 10-K
uv run python -m backend.ingestion.sec_filing_pipeline AAPL 10-K --fiscal-year 2025
uv run python -m backend.ingestion.sec_filing_pipeline AAPL 10-K --force
```

- Ticker and filing type are positional arguments
- `--fiscal-year` is optional (omitted = latest)
- `--force` bypasses cache
- On success: print a concise summary (ticker, fiscal_year, parsed_at, content length, file path)
- On error: print the error type and message to stderr, exit with non-zero code

### Batch

```bash
uv run python -m backend.ingestion.sec_filing_pipeline batch NVDA AAPL TSLA --filing-type 10-K
```

- Subcommand `batch` with multiple tickers
- Print per-ticker summary (status, fiscal_year, file path or error)
- Exit code: 0 if all succeed, 1 if any fail

### Output Control

- Default output: concise summary (one-liner per filing)
- `--verbose`: include full metadata (cik, accession_number, source_url, converter, etc.)
- `--json`: output as JSON (for programmatic consumption)
- Never print the full markdown content to stdout — only metadata and file path

## Implementation Location

- Add `__main__.py` to `backend/ingestion/sec_filing_pipeline/`
- Use `argparse` (no extra dependencies)

## Existing API Reference

- `SECFilingPipeline.create()` — factory with default dependencies
- `SECFilingPipeline.process(ticker, filing_type, fiscal_year=None, force=False)` → `ParsedFiling`
- `SECFilingPipeline.process_batch(tickers, filing_type)` → `dict[str, BatchResult]`
- `ParsedFiling.metadata: FilingMetadata` — all metadata fields
- `ParsedFiling.markdown_content: str` — the markdown body
- Error types: `TickerNotFoundError`, `FilingNotFoundError`, `UnsupportedFilingTypeError`, `TransientError`

## Design Gap

The original design (`design.md` §3.5) specifies two callers:

1. **Batch pre-load script** — "script 執行，一次下載多家公司的 10-K"
2. **Agent tool** — "agent 在 runtime 偵測到 store 裡沒有某 ticker 的資料，觸發 download + parse"

"Batch script + Agent tool entry point" is explicitly listed in the scope table. The implementation delivered only the Python API (`process()` / `process_batch()`), but neither the CLI script nor the agent tool integration was built. This task covers the CLI script; the agent tool integration is a separate task.

## Origin

Discovered during BDD manual verification (2026-04-05): manual test steps required users to write multi-line Python import chains just to invoke the pipeline, which is poor UX and error-prone.
