# Backend Scripts

One-off analysis scripts and developer tools that live outside the main package modules.

Scripts here are not part of the runtime pipeline. They are intended for ad-hoc validation, regression analysis, and data spot-checks during development. None of them are imported by production code.

## `validate_sec_md_cleanup.py`

Walks a `LocalFilingStore` cache directory and produces a markdown report describing how each cached SEC 10-K filing would be affected by the cleanup rules in `backend/ingestion/sec_filing_pipeline/markdown_cleaner.py`. The script does **not** modify any cached files — it only inspects them and writes a report.

### When to run

- **Before changing a cleanup rule** in `MarkdownCleaner` — capture a baseline report so you can diff before/after
- **After downloading new tickers** to the cache — confirm the new filings don't introduce boilerplate variants the existing rules miss
- **When investigating a regression** on a specific filing — use the per-filing breakdown table to spot anomalies (zero stub counts, missing heading anchors, etc.)
- **When adding a new validation ticker** to the project's anchor set

### Usage

```bash
uv run python backend/scripts/validate_sec_md_cleanup.py \
  --cache-dir /path/to/data/sec_filings \
  --output artifacts/current/validation_cleanup_patterns.md
```

Both arguments are required. The script discovers all `*.md` files under `--cache-dir` recursively, parses the YAML frontmatter to extract ticker / fiscal year / converter, then runs detection regexes on the body.

### What the report contains

The output is a markdown file with the following sections:

| Section | Purpose |
| --- | --- |
| **Per-filing breakdown** | Per-(ticker, fiscal year) row with TOC link count, bare `---` count, strict page-separator match count, table separator count, Item 10-14 stub/real/total split, Item 1C / 9A presence, truncated heading count, false-positive risk count, and whether the cover-page anchor (`# Part I` or `## Item 1` fallback) was found |
| **Heading variants (aggregated)** | Frequency table of detected Part / Item heading shapes across all filings, plus per-variant samples to make it easy to spot a new shape |
| **Truncated headings** | Lists every Item heading whose title is shorter than 5 characters (R2.2 defensive code — currently empty for the validation set) |
| **Empty-title headings** | Lists every Item heading with an empty title that wasn't merged from the next line — surfaces AMZN-style cases |
| **Item 1C / 9A / 9B / 9C presence** | Per-filing matrix confirming the word-boundary protection is preserving non-stub item sections |
| **False positive risks** | Lists any case where the detection regex would incorrectly match an Item that should be preserved (e.g. table separator with digit-line preceding) |
| **Bare `---` vs strict page separator (gap analysis)** | Surfaces filings where the spec's page-separator regex misses some bare `---` lines — should be all zeros if the regex is correct |

### What each number tells you

| Statistic | Healthy value | Diagnostic if unhealthy |
| --- | --- | --- |
| Cover anchor `Y/N` | `Y` for most modern filings | `N` means the filing has neither `# Part I` nor `## Item 1` heading. Cleaner falls back to pass-through. Common for very old filings (GE 2008) or color-based hierarchies (INTC). |
| Bare `---` after cleanup (verified separately) | 0 in body, 2 in frontmatter | A non-zero body count means a page-separator pattern slipped through. Investigate by reading the gap analysis section. |
| Item 10-14 `stub/real/total` | `5/0/5` for typical 10-K | `0/0/0` means no `## Item 10-14` headings exist (BRK.B, JPM, INTC) — Part III is structured differently. `1/4/5` or similar means most items are real content (rare for Part III). |
| Truncated heading count | `0` in current set | Non-zero means the converter is dropping characters from a heading. Check whether MSFT moved back to `markdownify` fallback. |
| FP risks | `0` or low | High count means a cleanup rule is too aggressive. Read each warning to find the specific filing. |

### Output location

Reports are typically written to `artifacts/current/validation_cleanup_patterns.md`. The `artifacts/` directory is gitignored — reports are not committed. If you need a snapshot for a PR, link to the validation script invocation rather than committing the report.

### Adding a new validation ticker

1. Download the filing into the cache directory: `uv run python -m backend.ingestion.sec_filing_pipeline {TICKER} 10-K --fiscal-year {YEAR}`
2. Re-run `validate_sec_md_cleanup.py`
3. Inspect the new row in the per-filing breakdown
4. If you see a new boilerplate variant, update `backend/ingestion/sec_filing_pipeline/markdown_cleaner.py` and the heading-variant detection logic in this script in tandem
