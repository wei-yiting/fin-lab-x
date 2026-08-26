# Code Review Round 5

> Reviewer: gpt-5.6-sol | Date: 2026-08-20

## Summary

| Metric | Count |
|--------|-------|
| Total issues | 0 |
| Blocking | 0 |
| Major | 0 |
| Minor | 0 |
| Suggestion | 0 |
| Library checks | 0 |

## Previous Round Status

| # | Issue ID | Status | Notes |
|---|----------|--------|-------|
| 1 | M-1.1 | ✅ Independently verified (partial scope) | Frontend-must-ship-together **Dismissed (user decision)**, deferred to DEV-143 by design. |
| 2 | M-1.2 | 🚫 Dismissal independently verified | Citation-accuracy eval gap pre-existing/cross-cutting; DEV-126 is the scoped guard. |
| 3 | M-1.3 / M-2.3 | ✅ Independently verified + regression-tested | |
| 4 | M-1.4 / M-3.3 | ✅ Independently verified | `query`/`ticker` blank-after-strip validators, `fiscal_year` `ge=1994`. Further tightening dismissed at round 4 (M-4.1). |
| 5 | M-1.5 | ✅ Independently verified | |
| 6 | M-1.6 | 🚫 Dismissal independently verified | Ratified glossary vocabulary. |
| 7 | m-1.1 / m-4.1 | 🚫 Dismissal independently verified | Standing exceptions (DEV-143 transitional wording; ADR issue-ID convention). |
| 8 | m-1.2 / m-2.2 | ✅ Independently verified | |
| 9 | M-2.1 / M-3.2 | ✅ Independently verified | ADR-0017 split three ways (ADR-0017/0018/0019). |
| 10 | M-2.2 | ✅ Independently verified | |
| 11 | m-2.1 | ✅ Independently verified | |
| 12 | S-2.1 / m-3.2 | ✅ Independently verified | |
| 13 | SP-1.3 / SP-1.4 | 🚫 Dismissal independently verified | |
| 14 | SP-2.1 | ✅ Independently verified | |
| 15 | SP-2.2 | 🚫 Dismissal independently verified | |
| 16 | M-3.1 | 🚫 Dismissal independently verified | Pre-existing `@observe` convention on all sibling SEC tools. |
| 17 | M-3.4 / M-4.2 / SP-4.1 | ✅ Independently verified | `locate_filing_ref()` validates accession-number format + full ISO date. |
| 18 | m-3.1 | ✅ Independently verified | |
| 19 | M-4.3 | 🚫 Dismissal independently verified | Qdrant filter is a DB-level guarantee; narrow accession-drift edge case logged to DEV-160. |
| 20 | M-4.4 | ✅ Independently verified | ADR-0018 corrected; cross-references ADR-0019. |
| 21 | m-4.2 | ✅ Independently verified | |

## Issues

None. The fresh Quality/Standards review found no actionable defects after calibration against the design envelope.

198 tests (the affected modules) passed independently in this round's verification; ruff lint and formatting checks also passed for all changed Python files.

## Documentation Gaps

| Folder | Missing |
|--------|---------|
| — | None |

## Official Standards Check

| Library | Version | API Used | Status | Notes |
|---------|---------|----------|--------|-------|
| — | — | No new or modified library surface since Round 3 | Not re-run | `datetime.date.fromisoformat` is standard-library usage, no external verification needed. |

---

# Spec Conformance Round 5

> Reviewer: gpt-5.6-sol | Date: 2026-08-20

## Summary

| Metric | Count |
|--------|-------|
| Total findings | 0 |
| Missing | 0 |
| Scope creep | 0 |
| Misimplemented | 0 |

## Previous Spec Findings Status

| # | Finding ID | Verdict | Status now | Notes |
|---|-----------|---------|-------------|-------|
| 1 | SP-1.1 | Major, Misimplemented (round 1) | ✅ Resolved by design (verified round 5) | |
| 2 | SP-1.2 | Major, Misimplemented (round 1) | ✅ Resolved (verified round 5) | |
| 3 | SP-1.3 | Major, Scope creep (round 1) | 🚫 Dismissed (user decision, unchanged) | |
| 4 | SP-1.4 | Minor, Scope creep (round 1) | 🚫 Dismissed (user decision, unchanged) | |
| 5 | SP-2.1 | Blocking→Major, Misimplemented (round 2) | ✅ Fixed (verified round 5, re-verified after round 4's validation tightening) | |
| 6 | SP-2.2 | Minor, Scope creep (round 2) | 🚫 Dismissed (user decision, unchanged) | |
| 7 | SP-4.1 | Major, Misimplemented (round 4) | ✅ Fixed (verified round 5) | |

## Findings

None.

## Covered Requirements

✅ `sec_filing_search(query, ticker, fiscal_year?)` is an async tool wrapping the frozen `_html` retriever — `backend/agent_engine/tools/sec_filing_search.py`
✅ Retrieval continues through the existing JIT/cache/`sec_retrieval` path — `backend/agent_engine/tools/sec_filing_search.py`
✅ Evidence is grouped by `(ticker, year, item)`, ordered by `chunk_index` within each group, with one prelude per group — `backend/agent_engine/tools/sec_filing_search.py`
✅ The tool carries no ordinal; the model assigns `[N]` globally in first-use order and binds it through each chunk's stable `source` — `backend/agent_engine/agents/profiles/reader/system_prompt.md`
✅ Stable citation IDs use `sec://{accession}/{item_key}#{chunk_index}` — `backend/agent_engine/tools/sec_filing_search.py`
✅ Well-formed EDGAR metadata still produces the same `FilingRef` fiscal year, full period-of-report, and accession number as before round 4 — `backend/common/sec_core.py`
✅ Malformed accession numbers and invalid complete ISO dates now produce classified errors instead of usable filing identities — `backend/common/sec_core.py`
✅ Legacy chunks missing `accession_number` still fall back to the now-format-validated `filing_ref.accession_number` — `backend/agent_engine/tools/sec_filing_search.py`
✅ Omitted fiscal year resolves the latest 10-K; requested years are validated and the resolved FY/FY-end are reported — `backend/agent_engine/tools/sec_filing_search.py`
✅ Evidence chunks expose `source`, `title`, `content`, optional subsection, and score; FlatItem locators honestly degrade to Item level — `backend/agent_engine/tools/sec_filing_search.py`
✅ Language directives sandwich both successful and empty retrieval results — `backend/agent_engine/tools/sec_filing_search.py`
✅ Empty results return a ticker/year-specific legible message; lookup and retrieval errors bubble to existing tool-error handling — `backend/agent_engine/tools/sec_filing_search.py`
✅ EDGAR URLs are resolved out-of-band from persisted filing metadata and degrade to `null` when unavailable — `backend/agent_engine/tools/sec_filing_search.py`
✅ EDGAR URLs exist only in `ToolMessage.artifact`, never model-visible content — `backend/agent_engine/tools/sec_filing_search.py`
✅ Tool artifacts are streamed as persistent `data-tool-artifact` parts associated with the correct tool call — `backend/agent_engine/streaming/event_mapper.py`, `backend/agent_engine/streaming/sse_serializer.py`
✅ `reader` receives `sec_filing_search` and its dedicated citation/routing prompt — `backend/agent_engine/agents/profiles/reader/orchestrator_config.yaml`, `backend/agent_engine/agents/profiles/reader/system_prompt.md`
✅ Reader prompt covers source-specific citations, SEC no-URL behavior, claim-adjacent evidence gaps, cross-call attribution, and pinpoint/synoptic routing — `backend/agent_engine/agents/profiles/reader/system_prompt.md`
✅ Existing token streaming remains intact while the UI-only artifact is added alongside tool output — `backend/agent_engine/streaming/event_mapper.py`
✅ `baseline/` has no diff in the specified range and contains neither `sec_filing_search` nor the `sec://` citation contract — `backend/agent_engine/agents/profiles/baseline/`
✅ Frontend citation parsing and Sources UI remain outside this backend changeset — `frontend/`

---
