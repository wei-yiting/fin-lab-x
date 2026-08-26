# Code Review Round 4

> Reviewer: gpt-5.6-sol | Date: 2026-08-20

## Summary

| Metric | Count |
|--------|-------|
| Total issues | 6 |
| Blocking | 0 |
| Major | 4 |
| Minor | 2 |
| Suggestion | 0 |
| Library checks | 0 |

## Previous Round Status

| # | Issue ID | Status | Notes |
|---|----------|--------|-------|
| 1 | M-1.1 | ✅ Fixed (partial scope) | Frontend-must-ship-together **Dismissed (user decision)**. |
| 2 | M-1.2 | 🚫 Dismissed (user decision) | Citation-accuracy eval gap pre-existing/cross-cutting; DEV-126 is the scoped guard. |
| 3 | M-1.3 / M-2.3 | ✅ Fixed + regression-tested | |
| 4 | M-1.4 / M-3.3 | ⚠️ Partially Fixed | `query` AND `ticker` reject blank-after-strip; `fiscal_year` bounded (see M-4.1). |
| 5 | M-1.5 | ✅ Fixed | |
| 6 | M-1.6 | 🚫 Dismissed (user decision) | Ratified glossary vocabulary. |
| 7 | m-1.1 | ⚠️ Partially Fixed | See m-4.1. |
| 8 | m-1.2 / m-2.2 | ✅ Fixed | |
| 9 | M-2.1 / M-3.2 | ✅ Fixed | ADR-0017 split three ways. |
| 10 | M-2.2 | ✅ Fixed | |
| 11 | m-2.1 | ✅ Fixed | |
| 12 | S-2.1 / m-3.2 | ✅ Fixed | |
| 13 | SP-1.3 / SP-1.4 | 🚫 Dismissed (user decision) | |
| 14 | SP-2.1 | ✅ Fixed | |
| 15 | SP-2.2 | 🚫 Dismissed (user decision) | |
| 16 | M-3.1 | 🚫 Dismissed (investigated) | Pre-existing `@observe` convention on all sibling SEC tools. |
| 17 | M-3.4 | ⚠️ Partially Fixed | See M-4.2. |
| 18 | m-3.1 | ✅ Fixed | |

## Issues

### [Major] M-4.1: Tool input validation still omits required shape and upper bounds
- **File:** `backend/agent_engine/tools/sec_filing_search.py` L74
- **Problem:** `query` has no maximum length, `ticker` accepts arbitrary nonblank text, and `fiscal_year` has only a lower bound.
- **Fix:** Add a documented maximum query length, constrain ticker syntax, and reject fiscal years later than the current valid filing year.

### [Major] M-4.2: Filing identity validation accepts malformed dates and blank accession numbers
- **File:** `backend/common/sec_core.py` L408
- **Problem:** `int(period_of_report[:4])` validates only the year prefix; a whitespace-only accession number passes `if not accession_number`.
- **Fix:** Parse the complete date as ISO format, reject blank-after-strip accession numbers, validate the accession format.

### [Major] M-4.3: Retrieved chunks are never checked against the requested filing
- **File:** `backend/agent_engine/tools/sec_filing_search.py` L283
- **Problem:** The tool requests one `(ticker, fiscal_year)` but trusts every returned chunk's `ticker`/`year`/`accession_number`.
- **Fix:** Verify every chunk matches the normalized requested ticker/fiscal year/accession number before building groups.

### [Major] M-4.4: ADR-0018 misstates the shipped evidence schema and omits the transport cross-reference
- **File:** `docs/adr/0018-sec-citations-are-prompt-driven-and-model-numbered.md` L6
- **Problem:** The Decision says each chunk carries `ticker`/`year`/`item`/`header_path` — these actually live on `EvidenceGroup`, not `EvidenceChunk`. No cross-reference to ADR-0019.
- **Fix:** Rewrite the schema description to match the actual group/chunk structure; add an ADR-0019 cross-reference.

### [Minor] m-4.1: Durable code and ADRs still contain issue IDs
- **File:** `backend/agent_engine/tools/sec_filing_search.py` L48
- **Problem:** `EvidenceChunk` docstring says "once DEV-143 lands"; ADR-0010/0017/0018 retain DEV-125/DEV-126 references.
- **Fix:** Replace with durable descriptions.

### [Minor] m-4.2: `sec_core`'s module contract omits its new production consumer
- **File:** `backend/common/sec_core.py` L12
- **Problem:** Docstring doesn't mention `sec_filing_search` as a shared consumer.
- **Fix:** Add it to the "Shared by" sentence.

## Documentation Gaps

| Folder | Missing |
|--------|---------|
| — | None |

## Official Standards Check

| Library | Version | API Used | Status | Notes |
|---------|---------|----------|--------|-------|
| — | — | No new library surface since Round 3 | Not re-run | |

---

# Spec Conformance Round 4

> Reviewer: gpt-5.6-sol | Date: 2026-08-20

## Summary

| Metric | Count |
|--------|-------|
| Total findings | 1 |
| Missing | 0 |
| Scope creep | 0 |
| Misimplemented | 1 |

## Previous Spec Findings Status

| # | Finding ID | Verdict | Status now | Notes |
|---|-----------|---------|------------|-------|
| 1 | SP-1.1 | Major, Misimplemented (round 1) | ✅ Resolved by design (verified round 4) | |
| 2 | SP-1.2 | Major, Misimplemented (round 1) | ✅ Resolved (verified round 4) | |
| 3 | SP-1.3 | Major, Scope creep (round 1) | 🚫 Dismissed (user decision, unchanged) | |
| 4 | SP-1.4 | Minor, Scope creep (round 1) | 🚫 Dismissed (user decision, unchanged) | |
| 5 | SP-2.1 | Blocking→Major, Misimplemented (round 2) | ✅ Fixed (verified round 4) | |
| 6 | SP-2.2 | Minor, Scope creep (round 2) | 🚫 Dismissed (user decision, unchanged) | |

## Findings

### [Major] SP-4.1: EDGAR identity validation still accepts non-empty malformed metadata
- **Type:** Misimplemented
- **Spec:** Round 4 verification note for M-3.4; guards DEV-130 User Story 16.
- **File:** `backend/common/sec_core.py` L408
- **Problem:** The M-3.4 guard rejects a falsy accession number and a year-prefix-unparseable `period_of_report`, but not non-empty malformed values (`"not-an-accession"`, `"2025-invalid"`, `"2025-99-99"`).
- **Fix:** Validate the stripped accession against the complete EDGAR accession format and parse the complete `period_of_report` as an ISO date.

## Covered Requirements

(19 requirements confirmed covered — see round 4's full transcript; unchanged from round 3's coverage plus confirmation that ADR-0017/0018/0019 preserve the runtime decisions.)

---
