# Code Review Round 1

> Reviewer: gpt-5.5 (reasoning effort: high) | Date: 2026-08-21

## Summary

| Metric | Count |
|--------|-------|
| Total issues | 2 |
| Blocking | 0 |
| Major | 1 |
| Minor | 1 |
| Suggestion | 0 |
| Library checks | 1 |

## Issues

### [Major] M-1.1: Degraded filings are persisted but still cannot be embedded or retrieved
- **File:** `backend/ingestion/sec_text_pipeline/parser.py` L165
- **Problem:** The parser now saves degraded filings as `ParsedFiling(metadata=..., items=[], degraded_text=text)`, and the new glossary claims "All content stays retrievable" (`CONTEXT.md` L52). But the current dense ingest contract only iterates `filing.items` (`backend/ingestion/sec_dense_pipeline/chunking.py` L92), so a degraded filing produces zero chunk payloads and `ingest_filing()` raises `EmptyIngestError` before any content reaches Qdrant (`backend/ingestion/sec_dense_pipeline/vectorizer.py` L97-L102). This violates the stated behavior and the design-envelope §4 JIT failure legibility / demo-facing retrieval standard: the fallback path remains a parse-cache artifact, not retrievable content.
- **Fix:** Add degraded handling at the dense chunking boundary: when `filing.is_degraded`, split `filing.degraded_text` into payloads with a stable non-Item locator (for example `item="degraded"` or another explicit contract), clear `block_heading` / `prelude`, and a `header_path` that makes degraded structure visible. Add unit coverage in `sec_dense_pipeline/unit/test_chunking.py` and an ingest test proving degraded content writes payloads and completes the marker. If dense support is intentionally a later slice, remove the "All content stays retrievable" claim and keep this parser output out of any path that promises JIT retrieval.
- **Context7:** Not library-related.

### [Minor] m-1.1: Newly added docs carry issue IDs that do not add reader-facing meaning
- **File:** `docs/adr/0018-degraded-ingest-for-fallback-detected-filings.md` L9
- **Problem:** The new ADR and README include `DEV-172`, `DEV-127`, `DEV-171`, `DEV-176`, and `DEV-138` as explanatory text. Issue IDs are tolerated by the review standard, but they belong in PR/commit metadata unless the text needs them. Here the surrounding prose already explains the decision, rejected alternatives, and re-evaluation triggers; the IDs add session metadata noise.
- **Fix:** Remove the `DEV-*` references where the descriptive text stands alone. Keep durable ADR numbering; that is repo architecture documentation, not session metadata.

## Documentation Gaps

| Folder | Missing |
|--------|---------|
| None | No pragmatic README gap found in the changed folders. |

## Official Standards Check

Results of Context7 verification for each library used in the changes:

| Library | Version | API Used | Status | Notes |
|---------|---------|----------|--------|-------|
| pydantic | 2.12.5 locked, `>=2.0` declared | `BaseModel`, `ConfigDict(extra="forbid")`, `Field(discriminator="kind")`, `Field(min_length=1)`, `model_validate`, `model_validate_json`, `model_dump`, `model_dump_json` | ✅ Current | Matches pydantic v2 documented patterns. Discriminated union members use `Literal` tags with defaults, additive fields have defaults, and v2 validation/serialization APIs are used. |

---

# Spec Conformance Round 1

> Reviewer: gpt-5.5 (reasoning effort: high) | Date: 2026-08-21

## Summary

| Metric | Count |
|--------|-------|
| Total findings | 0 |
| Missing | 0 |
| Scope creep | 0 |
| Misimplemented | 0 |

## Findings

No findings.

## Covered Requirements

✅ Degraded detection methods `pattern`, `html_fallback`, and `unknown` trigger degraded ingest — `backend/ingestion/sec_text_pipeline/parser.py`
✅ Detection method is recorded at filing metadata level and passed through to stored output — `backend/ingestion/sec_text_pipeline/filing_models.py`
✅ AMD-like pattern fixture with semantic section name and empty item metadata parses as degraded instead of `EmptyFilingError` — `backend/tests/ingestion/sec_text_pipeline/test_parser.py`
✅ Degraded parse stores `items=[]`, cleaned `degraded_text`, and `section_detection_method` — `backend/ingestion/sec_text_pipeline/parser.py`
✅ Standard `toc` / `heading` path still uses structured item parsing and does not become degraded — `backend/tests/ingestion/sec_text_pipeline/test_parser.py`
✅ Additive schema fields have defaults so pre-change stored JSON validates — `backend/tests/ingestion/sec_text_pipeline/test_filing_models.py`
✅ `EmptyFilingError` now means degraded full-document text is empty after cleaning — `backend/ingestion/sec_text_pipeline/parser.py`
✅ Noise cleaning has direct positive and negative unit coverage for cover/TOC, signatures, page artifacts, and blank-line collapse — `backend/tests/ingestion/sec_text_pipeline/test_degraded.py`
✅ Inspect view renders degraded marker and full-text preview — `backend/ingestion/sec_text_pipeline/inspect_view.py`
✅ ADR-0018 records the degraded ingest decision and rejected alternatives — `docs/adr/0018-degraded-ingest-for-fallback-detected-filings.md`
✅ `CONTEXT.md` adds the "Degraded ingest" vocabulary entry — `CONTEXT.md`

---
