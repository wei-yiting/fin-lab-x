# Code Review Round 1

> Reviewer: Codex | Date: 2026-04-04

## Summary

| Metric | Count |
|--------|-------|
| Total issues | 5 |
| Blocking | 0 |
| Major | 3 |
| Minor | 1 |
| Suggestion | 1 |
| Library checks | 6 |

## Issues

### [Major] M-1.1: `latest` path cache hit still hits SEC

- **File:** `backend/ingestion/sec_filing_pipeline/pipeline.py` L94
- **Problem:** When `fiscal_year` is `None`, the pipeline always calls `download()` first, then checks cache using `raw.fiscal_year`. This means the most common "get latest 10-K" path always hits SEC even if the file is already cached locally. `from_cache=True` on this path is also misleading — it indicates the final returned object is cached, not that the remote request was avoided.
- **Fix:** Before downloading, determine whether a local cache hit is possible — e.g., use `store.list_filings()` to find the most recent cached year. If not feasible, at minimum do not mark this path as `from_cache=True`.
- **Context7:** N/A

### [Major] M-1.2: `html-to-markdown` return type assumption is wrong

- **File:** `backend/ingestion/sec_filing_pipeline/html_to_md_converter.py` L27
- **Problem:** `result = htm_convert(...)` is followed by `result["content"]`. According to official references, `convert(html, options=ConversionOptions(...))` returns a `str` in all documented examples. Only when `extract_metadata=True` (the default) might the return be a dict-like structure. The code does not explicitly set `extract_metadata`, nor does it branch on return type, so if a string is returned it will `TypeError` and force the fallback converter.
- **Fix:** Either explicitly set `ConversionOptions(extract_metadata=False, heading_style="atx")` or handle both `str` and dict-like return types.
- **Context7:** Official pattern is `convert(html, options=ConversionOptions(...))` returning string; metadata extraction enabled may produce `content` structure.

### [Major] M-1.3: SEC heading promotion core heuristic has no explanation

- **File:** `backend/ingestion/sec_filing_pipeline/html_preprocessor.py` L118
- **Problem:** `_promote_headings()` performs reverse traversal, descendant deduplication, bold detection, block-child filtering, tag renaming, and content rewriting. This is the core rule that determines whether the parser can structure a 10-K correctly, but there are no comments explaining WHY. Per review standards, non-trivial business rules without WHY comments are Major.
- **Fix:** Add a short comment block before the method or core loop explaining: (1) why this heuristic exists (SEC filings lack semantic headings), (2) why reverse traversal, (3) what the descendant guard prevents.

### [Minor] m-1.1: Fallback threshold `0.01` is a bare magic number

- **File:** `backend/ingestion/sec_filing_pipeline/html_to_md_converter.py` L69
- **Problem:** `len(md) < len(html) * 0.01` directly decides whether to abandon the primary converter, but there is no named constant or rationale. Maintainers cannot judge whether short documents, HTML fragments, or table-dense content would be incorrectly downgraded.
- **Fix:** Extract to a named constant, e.g., `_MIN_OUTPUT_RATIO = 0.01`, and add a brief comment explaining the rationale.

### [Suggestion] S-1.1: `create_converter()` is an abstraction unused by production code

- **File:** `backend/ingestion/sec_filing_pipeline/html_to_md_converter.py` L43
- **Suggestion:** `create_converter()` is only used in tests. The actual production path `SECFilingPipeline.create()` directly hardcodes `HtmlToMarkdownAdapter()` and `MarkdownifyAdapter()`. This is a classic "used once" abstraction. Either remove it or wire it into `pipeline.create()` to avoid valueless indirection.

## Documentation Gaps

| Folder | Missing |
|--------|---------|
| `backend/ingestion/sec_filing_pipeline` | `README.md` — should explain pipeline stages, cache behavior, converter fallback rules, and extension guidelines for new filing types or preprocessor rules |

## Official Standards Check

| Library | Version | API Used | Status | Notes |
|---------|---------|----------|--------|-------|
| edgartools | >=5.17.1 | `Company(ticker)`, `get_filings(form=...)`, `.latest()`, `set_identity()` | ✅ Current | Usage matches official references. `period_of_report[:4]` for fiscal year is correct. |
| html-to-markdown | >=3.0.2,<4.0.0 | `convert(..., options=ConversionOptions(heading_style="atx"))` | ❌ Wrong | Code assumes dict-like return and accesses `["content"]`; official examples return string. Need explicit `extract_metadata=False` or type branching. |
| markdownify | >=1.2.0 | `markdownify(..., heading_style=ATX)` | ✅ Current | ATX heading usage matches official reference. |
| beautifulsoup4 | >=4.12.0 | `BeautifulSoup(...)`, `find_all()`, `unwrap()`, `decompose()` | ✅ Current | Standard API usage. |
| pyyaml | >=6.0.2 | `yaml.dump(...)`, `yaml.safe_load(...)` | ✅ Current | dump and safe_load usage matches official reference. |
| pydantic | v2 | `BaseModel` | ✅ Current | Standard usage. |
