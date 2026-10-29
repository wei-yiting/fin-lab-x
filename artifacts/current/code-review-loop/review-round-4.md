# Code Review Round 4

> Reviewer: gpt-5.6-luna | Date: 2026-08-26

## Summary

| Metric | Count |
|--------|-------|
| Total issues | 2 |
| Blocking | 0 |
| Major | 1 |
| Minor | 1 |
| Suggestion | 0 |
| Library checks | 0 |

## Previous Round Status

| # | Issue ID | Status | Notes |
|---|----------|--------|-------|
| 1 | M-1.1 / SP-1.1 | Fixed (Round 1) | |
| 2 | m-1.1 | Dismissed (user decision) | not re-raised |
| 3 | B-2.1 / SP-2.1 | Fixed (Round 2) | |
| 4 | M-2.1 | Fixed (Round 2) | |
| 5 | B-3.1 | Fixed (Round 3, via field removal not correction) | |
| 6 | m-3.1 | Fixed (Round 3) | |

## Issues

### [Major] M-4.1: Valid whitespace-prefixed Item segments are silently left unnormalized

- **File:** `backend/evals/scenarios/sec_retrieval_ab/html_arm_compat.py` L74
- **Problem:** `_ITEM_SEGMENT_RE` is applied to `segment` without stripping it first. The frozen pipeline's `parse_item()` applies `level.strip()` before the same regex, while `_build_header_path()` preserves heading text whitespace. For a path such as `NVDA / 2026 / Part I /   Item 1. Business`, the source emits `Item 1`, but this compatibility layer fails to find the Item segment and returns the original Part-level path. That creates a false scoring miss in the eval measurement zone, contrary to `docs/design-envelope.md` §4.
- **Fix:** Apply `.strip()` to each segment before `_ITEM_SEGMENT_RE.match()`, and extend the existing synthetic defensive-path coverage with a leading-whitespace case.

### [Minor] m-4.1: Tests do not verify the documented non-mutation contract

- **File:** `backend/tests/evals/test_html_arm_compat.py` L87
- **Problem:** Several assertions construct their expected value from `chunk` after calling `normalize_chunk()`. An implementation that mutated `chunk` in place would therefore still pass. The production implementation currently returns copies, but the tests do not protect that contract.
- **Fix:** Snapshot each input before normalization and assert both `normalized is not chunk` and `chunk == original`; apply the same check to inputs passed through `normalize_chunks()`.

## Documentation Gaps

| Folder | Missing |
|--------|---------|

## Official Standards Check

N/A — no external libraries in this change.

---

# Spec Conformance Round 4

> Reviewer: gpt-5.6-luna | Date: 2026-08-26

## Summary

| Metric | Count |
|--------|-------|
| Total findings | 0 |
| Missing | 0 |
| Scope creep | 0 |
| Misimplemented | 0 |

## Findings

None.

## Covered Requirements

All spec requirements confirmed implemented (full fresh top-to-bottom pass across the entire
accumulated diff, not just the delta since Round 3). See full agent output for the detailed
per-requirement table. Explicitly confirmed: removing `ingested_at`/`score` from real fixtures
does not weaken the Testing Decisions' representative-scenario coverage (those scenarios are
about `header_path`/`item` shape, not about those two unused metadata fields).

---

## Orchestrator Verification (2026-08-26)

**M-4.1**: traced the claim through `backend/ingestion/sec_dense_pipeline_html/vectorizer.py`:
`parse_item()` (L27) does call `.strip()` on each segment before matching; `_build_header_path()`
(L67-87) builds `segments` from `raw_path.strip("/").split("/")` (L75) — only the *outer*
boundary is stripped, not each inner segment — except the node's own trailing heading segment,
which gets `heading_text = heading_match.group(2).strip()` (L80) individually. So it's
structurally possible for an ancestor segment (e.g. from a heading with irregular spacing in the
source markdown) to reach `header_path` with un-stripped whitespace, while `parse_item()`
extracts a clean `item` value from the same raw text. `html_arm_compat.py`'s
`_ITEM_SEGMENT_RE.match(segment)` (no `.strip()`) would then fail to locate that segment.

However: I checked all 84 unique chunks in the actual recorded reference CSV
(`2026-08-19_73faf5f.csv`) for any header_path segment with leading/trailing whitespace — zero
instances. Unlike M-2.1's `Item 9A(T)` (where `vectorizer.py`'s own regex explicitly,
deliberately encodes support for that historical SEC form — clear evidence of an anticipated
real case), this finding rests on an internal implementation detail of a third-party library
(llama_index's `MarkdownNodeParser`) that may or may not ever actually inject such whitespace,
and has not been observed in the one real dataset this module targets. Per design-envelope §4,
eval measurement rigor ("can these scores be trusted?") is a Production-Grade Zone that does
apply here — but per the Reachability rule (§0), no evidence yet shows this path is reachable
with real data. That said, the fix (`.strip()` before the regex match) is a one-line, zero-cost
hardening of an existing regex — not new machinery, not exhaustive filing-variant coverage — so
the YAGNI cost/benefit calculus is favorable regardless of reachability uncertainty.

**m-4.1**: confirmed by inspection — every existing assertion is of the shape
`normalized == {**chunk, "header_path": ...}`, which passes equally whether `normalize_chunk`
returns a fresh dict or mutates and returns the same object. The module's own docstring
explicitly promises `chunk` is never mutated; no test currently protects that promise.

## Discussion Gate Resolution (orchestrator + user, 2026-08-26)

Both undisputed — user agreed to fix both:
1. **M-4.1** — add `.strip()` before `_ITEM_SEGMENT_RE.match()`, plus a defensive-path test for
   a leading/trailing-whitespace segment. Accepted despite weaker reachability evidence than
   M-2.1, because the fix cost is a one-line regex hardening, not new machinery.
2. **m-4.1** — add non-mutation assertions (`chunk == original` snapshot, `normalized is not
   chunk`) to protect the module docstring's explicit "chunk is never mutated" contract.
