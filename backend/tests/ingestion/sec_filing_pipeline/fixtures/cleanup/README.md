# Cleanup Fixture Files

Test fixtures for `MarkdownCleaner` snapshot tests.

## Provenance

Each `{ticker}/` directory contains raw/expected pairs sliced from real
SEC 10-K filings cached by the ingestion pipeline. The slices cover two
regions per ticker: the **cover page** preamble and the **Part III stub**
section.

## Why no frontmatter?

The production pipeline calls `MarkdownCleaner.clean()` on raw converter
output, which has no YAML frontmatter. Frontmatter is only attached later
by `LocalFilingStore.save()`. These fixtures reflect the production
contract — raw converter output with no frontmatter.

Defensive dual-shape tests (with frontmatter) live in `test_markdown_cleaner.py`
using the `_with_frontmatter()` helper.

## How to regenerate

1. Run the ingestion pipeline for the target ticker so a cached `.md` file
   exists under `data/sec_filings/{TICKER}/10-K/{YEAR}.md`.
2. Extract the relevant slice (cover page region or Part III Items 10-14
   region) from the stored file. **Strip the YAML frontmatter block** before
   saving as `*_raw.md`.
3. Run `MarkdownCleaner().clean()` on the raw slice and save the output as
   `*_expected.md`.
4. Manually verify the expected output against the original filing to
   confirm no real content was deleted.

## Anchor tickers

| Ticker | Role |
|--------|------|
| NVDA   | Standard case — Item 1C real content + Part III stubs + TOC link variant |
| AMT    | Hybrid protection — Item 10 exec biographies (~3000 chars) must survive |
| CRM    | Hybrid protection + heading variants — Item 10 Code of Conduct must survive |
| JNJ    | Fallback anchor (`## Item 1`) + lowercase title normalization |
