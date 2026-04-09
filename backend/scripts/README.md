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
