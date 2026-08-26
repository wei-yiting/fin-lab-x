# Code Review Round 3

> Reviewer: gpt-5.6-sol | Date: 2026-08-20

## Summary

Targeted verification: 192 tests passed; `ruff check` and `ruff format --check` passed. Those checks do not cover the issues below.

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
| 1 | M-1.1 | ✅ Fixed (partial scope) | "Frontend must ship in this slice" was **Dismissed (user decision)** — deliberately deferred to DEV-143 per DEV-142's own AC. Only the dangling docstring reference (to a nonexistent `frontend/src/lib/sec-citations.ts`) was fixed. |
| 2 | M-1.2 | 🚫 Dismissed (user decision) | Citation-accuracy/groundedness eval gap judged pre-existing and cross-cutting. DEV-126 is the correctly-scoped, queued guard. |
| 3 | M-1.3 | ✅ Fixed and regression-tested | `_edgar_filing_url` logs a warning on `OSError`/`ValueError`; round 2 added a regression test covering both exception types. |
| 4 | M-1.4 | ⚠️ Partially Fixed — the listed constraints exist, but whitespace-only `ticker` still passes validation and reaches EDGAR after becoming empty | `SecFilingSearchInput`: `query` min_length=1 + blank-after-strip validator, `ticker` min_length=1/max_length=10, `fiscal_year` ge=1994. |
| 5 | M-1.5 | ✅ Fixed | ADR renamed 0008→0017. |
| 6 | M-1.6 | 🚫 Dismissed (user decision) | "Phase 1"/"Phase 2" — ratified repo glossary vocabulary. |
| 7 | m-1.1 | ✅ Fixed | Issue-ID citations removed from two code/test docstrings. |
| 8 | m-1.2 | ✅ Fixed | README's capability table: `search_sec_filings` → `sec_filing_search`. |
| 9 | M-2.1 | ⚠️ Partially Fixed — the contradiction and amendment are gone, but the original structural finding remains: the ADR is still 973 words and combines generation placement, citation numbering, and artifact transport | ADR-0017's Decision paragraph rewritten to match the shipped design; the Amendment section removed and folded into Consequences. |
| 10 | M-2.2 | ✅ Fixed | `FilingRef.filing_date` (dead field) removed; `accession_number` now has a real production consumer. |
| 11 | M-2.3 | ✅ Fixed | Same item as #3. |
| 12 | m-2.1 | ✅ Fixed | `WORKFLOW_PROFILE` documented in README. |
| 13 | m-2.2 | ✅ Fixed | Stale `search_sec_filings`/LangSmith references fixed in `docs/agent_architecture.md`; `docs/file_structure.md` gained a `sec_filing_search.py` entry. |
| 14 | S-2.1 | ⚠️ Partially Fixed — the map and path are corrected, but the new relationship paragraph incorrectly says only the first two SEC surfaces share `sec_core` | `tools/README.md` gained a `sec_filing_search.py` entry, "two SEC paths"→"three SEC paths". |

## Issues

### [Major] M-3.1: `sec_filing_search` creates a redundant Langfuse tool span
- **File:** `backend/agent_engine/tools/sec_filing_search.py` L238
- **Problem:** `Orchestrator`'s `CallbackHandler` already traces tool execution, while `search()` already emits the nested `sec_retrieval` span. Adding `@observe(name="sec_filing_search")` therefore produces a redundant same-name layer without custom metadata or `get_current_observation_id()`. This directly contradicts `streaming_observability_guardrails.md` Rule 3 and `tools/README.md` L22–27.
- **Fix:** Remove `@observe` from `sec_filing_search`, remove it from `TOOLS_WITH_OBSERVE`, and assert that it relies on `CallbackHandler`. Keep the existing nested `sec_retrieval` span.

### [Major] M-3.2: ADR-0017 still combines three decisions in a 973-word record
- **File:** `docs/adr/0017-rag-generation-in-orchestrator-loop.md` L3
- **Problem:** The semantic contradiction from round 2 is fixed, but the structural part is not. The opening Decision spans generation placement, citation identity/numbering, and API/frontend resolution. Consequences add `ToolMessage.artifact` transport. At 973 words, it remains roughly twice the design-envelope §4 guideline and fails the required structural test: these are independently reversible decisions, not one wicked decision needing a single long record.
- **Fix:** Keep ADR-0017 focused on retrieval-as-tool and generation in the Orchestrator. Move citation identity/numbering and artifact transport into one or more separately numbered ADRs with their own rejected alternatives and consequences.

### [Major] M-3.3: Whitespace-only tickers bypass boundary validation
- **File:** `backend/agent_engine/tools/sec_filing_search.py` L82
- **Problem:** `Field(min_length=1)` checks the untrimmed string. `"   "` is accepted by `SecFilingSearchInput`; the tool then strips it to `""` and invokes `locate_filing_ref`, causing an avoidable EDGAR lookup with an invalid ticker.
- **Fix:** Add a `ticker` validator that strips input and rejects a blank result before the tool body runs. Add a whitespace-only regression case.

### [Major] M-3.4: EDGAR filing metadata is coerced instead of validated
- **File:** `backend/common/sec_core.py` L403
- **Problem:** `locate_filing_ref()` uses `str(filing.accession_number)` and `str(filing.period_of_report)` without validating either. A missing accession becomes the apparently valid string `"None"` and later produces `sec://None/...`; malformed dates leak raw `ValueError` or can pass a non-ISO date through as `fiscal_year_end`.
- **Fix:** Validate the two EDGAR metadata values before constructing `FilingRef`. Reject missing/malformed values with a contextual `SECError`, and add tests for absent accession and malformed `period_of_report`.

### [Minor] m-3.1: `_filing_key` is a one-line Middle Man
- **File:** `backend/agent_engine/tools/sec_filing_search.py` L114
- **Problem:** Fowler smell — Middle Man / Speculative Generality. `_filing_key()` is called only by `_citation_id()` and merely returns `chunk.accession_number or fallback_accession_number`.
- **Fix:** Inline the fallback into `_citation_id()` and retain a short WHY explanation there.

### [Minor] m-3.2: Tools README excludes the new search tool from its shared-core description
- **File:** `backend/agent_engine/tools/README.md` L16
- **Problem:** The paragraph names all three SEC surfaces, then says "The first two share" `FilingType`, the error taxonomy, and `sec_core` — `sec_filing_search.py` also imports these.
- **Fix:** State that all three surfaces use the shared SEC core, then distinguish which helpers each one consumes.

## Documentation Gaps

| Folder | Missing |
|--------|---------|
| — | None |

## Official Standards Check

| Library | Version | API Used | Status | Notes |
|---------|---------|----------|--------|-------|
| — | — | No new or modified library surface since prior verification | Not re-run | M-3.1 concerns repo guardrails, not Langfuse API availability. |

---

# Spec Conformance Round 3

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
| 1 | SP-1.1 | Major, Misimplemented (round 1) | ✅ Resolved by design (verified) | Tool carries no ordinal; model owns `[N]` numbering. |
| 2 | SP-1.2 | Major, Misimplemented (round 1) | ✅ Resolved (verified) | `CITATION BY SOURCE TYPE` table marks SEC evidence as no-URL/stable-ID-only. |
| 3 | SP-1.3 | Major, Scope creep (round 1) | 🚫 Dismissed (user decision; unchanged) | `WORKFLOW_PROFILE` kept deliberately. |
| 4 | SP-1.4 | Minor, Scope creep (round 1) | 🚫 Dismissed (user decision; unchanged) | Bundled with SP-1.3. |
| 5 | SP-2.1 | Blocking→Major, Misimplemented (round 2) | ✅ Fixed (verified) | Legacy-chunk citation ID falls back to `filing_ref.accession_number`. |
| 6 | SP-2.2 | Minor, Scope creep (round 2) | 🚫 Dismissed (user decision; unchanged) | `_DEFAULT_SYSTEM_PROMPT` sync is a drift fix, not scope creep. |

## Findings

None.

## Covered Requirements

✅ 新 async `sec_filing_search(query, ticker, fiscal_year?)` tool 已包裝既有 retriever `search()` — `backend/agent_engine/tools/sec_filing_search.py`
✅ Tool 已註冊，且僅加入 `reader` profile — `backend/agent_engine/tools/__init__.py`, `backend/agent_engine/agents/profiles/reader/orchestrator_config.yaml`
✅ Evidence 按 `(ticker, year, item)` 分組、組內依文件順序排列、每組僅一個 prelude — `backend/agent_engine/tools/sec_filing_search.py`
✅ `[N]` 由 model 依全答案 first-use order 編號，並以 bottom definition 綁定 chunk `source` — `backend/agent_engine/agents/profiles/reader/system_prompt.md`
✅ Stable citation ID 使用 `sec://{accession}/{item_key}#{chunk_index}` — `backend/agent_engine/tools/sec_filing_search.py`
✅ Legacy chunk 缺少 accession 時，fallback 已正確使用 `filing_ref.accession_number` — `backend/agent_engine/tools/sec_filing_search.py`
✅ Fiscal year 解析、來源與 fiscal-year end date 均回報，未知 ticker/year 產生 legible error — `backend/agent_engine/tools/sec_filing_search.py`, `backend/common/sec_core.py`
✅ EDGAR URL 從 persisted filing metadata out-of-band 取得；store cold/read failure 誠實退化為 null — `backend/agent_engine/tools/sec_filing_search.py`
✅ EDGAR URL 僅存在 UI artifact，不進入 model context，並透過 persistent SSE data part 傳遞 — `backend/agent_engine/streaming/event_mapper.py`, `backend/agent_engine/streaming/sse_serializer.py`
✅ Evidence shape 包含 `source/title/content`，並提供 FlatItem 的 Item-level honest degradation — `backend/agent_engine/tools/sec_filing_search.py`
✅ Language sandwich 同時包住成功與空結果內容 — `backend/agent_engine/tools/sec_filing_search.py`
✅ 空結果提供 legible message；retriever/JIT errors 正確 bubble — `backend/agent_engine/tools/sec_filing_search.py`
✅ Reader prompt 涵蓋 language policy、claim-adjacent evidence gap、跨 ticker/year attribution、pinpoint/synoptic routing 與 SEC no-URL 契約 — `backend/agent_engine/agents/profiles/reader/system_prompt.md`
✅ SEC citation table 仍明定 `[N]: <source>`、stable ID copied verbatim、no title、no URL — `backend/agent_engine/agents/profiles/reader/system_prompt.md`
✅ Retrieval 沿用既有 JIT cache 與 `sec_retrieval` trace，並新增可觀察的 tool span — `backend/agent_engine/tools/sec_filing_search.py`
✅ `baseline/` 在指定 diff range 完全無 diff，且仍不含 `sec_filing_search` — `backend/agent_engine/agents/profiles/baseline/`
✅ Acceptance criteria 的 grouping、numbering contract、stable ID、year、EDGAR URL、FlatItem、sandwich、empty result 與 error bubble 均有相應測試 — `backend/tests/tools/test_sec_filing_search.py`

---
