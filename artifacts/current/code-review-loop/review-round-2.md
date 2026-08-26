# Code Review Round 2

> Reviewer: gpt-5.6-sol | Date: 2026-08-19

## Summary

| Metric | Count |
|--------|-------|
| Total issues | 6 |
| Blocking | 0 |
| Major | 3 |
| Minor | 2 |
| Suggestion | 1 |
| Library checks | 1 |

## Issues

### [Major] M-2.1: ADR-0017 的決策本文與最終 citation contract 互相矛盾
- **File:** `docs/adr/0017-rag-generation-in-orchestrator-loop.md` L3
- **Problem:** Decision 本文仍稱 tool 回傳「numbered chunks」，且 `[N]` 指向 tool 提供的編號；但 L81–94 的 amendment 與目前實作明確規定 tool 不提供 ordinal，由 model 自行編號。此 ADR 共 971 words，開場 Decision 超過 1–2 句，並把 generation placement、citation numbering、`ToolMessage.artifact` transport 三項決策塞在同一紀錄。這違反 design-envelope §4 對 ADR 正確性、單一決策與約 500-word soft ceiling 的要求。
- **Fix:** 此 ADR 尚在本 changeset 中，合併前直接整理：讓 ADR-0017 僅記錄 generation 留在 Orchestrator loop 的決策，並把最終 citation identity/numbering/artifact contract 移至獨立 ADR；刪除已失效的 numbered-chunk 敘述與 amendment 疊補方式。

### [Major] M-2.2: `FilingRef` 暴露兩個沒有 production consumer 的欄位
- **File:** `backend/common/sec_core.py` L377
- **Problem:** `filing_date` 與 `accession_number` 只被 tests 讀取；唯一 production caller `sec_filing_search` 僅使用 `fiscal_year` 與 `period_of_report`。Tests 不算 runtime consumer。這在 shared core 新增無需求的 schema surface，違反 design-envelope §0 Reachability rule；依 §7，此類 consumer-less schema fields 至少是 Major over-engineering。
- **Fix:** 從 `FilingRef`、`locate_filing_ref()`、相關 docstrings/tests 移除這兩個欄位。若 `accession_number` 現在確實有必要，先讓 production code 用它落實具體 invariant；不要僅為未來用途保留。

### [Major] M-2.3: Round 1 的 observability 修正沒有 regression test
- **File:** `backend/tests/tools/test_sec_filing_search.py` L302
- **Problem:** 現有 test 只驗證合法 cold store 回傳 `None`；沒有讓 `LocalFilingStore.get()` 拋出 `OSError`/`ValueError`，也沒有斷言 warning。Round 1 修正的唯一行為差異正是「read failure 會留下 log」，目前可被移除而整個 suite 仍為綠燈。Observability 是 design-envelope §4 Production-Grade Zone，§5 要求此區域 thorough testing。
- **Fix:** 新增 parametrized test，讓 store read 分別拋出 `OSError` 與 `ValueError`；斷言 artifact 仍為 `{"edgar_url": None}`，且 `caplog` 包含 ticker、fiscal year 與 failure context。

### [Minor] m-2.1: `WORKFLOW_PROFILE` 是未文件化的 runtime control
- **File:** `backend/api/main.py` L41
- **Problem:** 新增的 live-serving profile selector 只出現在程式與 tests；root/backend README、Quick Start、environment-variable 說明皆未提及。預設仍為 `baseline`，操作員無法從 durable repo documentation 得知如何啟用已標示為 Implemented 的 `reader`。
- **Fix:** 在 API 或 root README 記錄 `WORKFLOW_PROFILE`、預設值、可用 profile 的來源，並提供 `WORKFLOW_PROFILE=reader` 啟動範例。

### [Minor] m-2.2: Architecture 文件仍使用退役的 tool 與 observability 名稱
- **File:** `docs/agent_architecture.md` L20
- **Problem:** L20 與 L138 仍寫不存在的 `search_sec_filings`，L104 又宣稱 runtime 使用 LangSmith；目前實作是 `sec_filing_search` 與 Langfuse（Braintrust migration pending）。同時 `docs/file_structure.md` 的 tools map 也沒有列出新 tool。這些文件本輪已更新為 `reader` Implemented，留下互相矛盾的架構說明會直接誤導 contributor。
- **Fix:** 將兩處 tool name 改為 `sec_filing_search`，把 observability 敘述對齊目前 Langfuse／待遷移 Braintrust 的狀態，並在 `docs/file_structure.md` tools map 加入 `sec_filing_search.py`。

### [Suggestion] S-2.1: Tools README 沒有解釋第三種 SEC access surface
- **File:** `backend/agent_engine/tools/README.md` L4
- **Suggestion:** Map 目前只列 whole-section tools 與 downloader，且仍以「two SEC paths」描述介面。加入 `sec_filing_search.py`，說明它如何包裝 frozen dense retriever、何時相對於 whole-section tools 使用；順便把 Extension Algorithm 的舊 `versions/` 路徑改成 `agents/profiles/`。

## Documentation Gaps

| Folder | Missing |
|--------|---------|
| `backend/agent_engine/tools/` | `README.md` 缺少 `sec_filing_search.py` 的責任、與另外兩種 SEC tool surface 的關係及 profile enablement 路徑。 |

## Official Standards Check

| Library | Version | API Used | Status | Notes |
|---------|---------|----------|--------|-------|
| Pydantic | 2.12.5 | `field_validator`, `Field(min_length=, max_length=, ge=)` | ✅ | Context7 官方 Pydantic v2 文件確認 decorator 順序 `@field_validator(...)` 後接 `@classmethod` 正確；default after-validation、`ValueError`、字串長度與數值下限 constraints 均為 current API。 |

---
# Spec Conformance Round 2

> Reviewer: gpt-5.6-sol | Date: 2026-08-19

## Summary

| Metric | Count |
|--------|-------|
| Total findings | 2 |
| Missing | 0 |
| Scope creep | 1 |
| Misimplemented | 1 |

## Findings

### [Blocking] SP-2.1: Legacy chunks produce citation IDs without an accession number

- **Type:** Misimplemented
- **Spec:** "每個 chunk 帶 stable citation ID（accession number + item + chunk index 組成）" (DEV-130, User Story 16)
- **File:** `backend/agent_engine/tools/sec_filing_search.py` L114
- **Problem:** `_filing_key()` falls back to `ticker-FY{year}` when a chunk lacks `accession_number`, even though `locate_filing_ref()` already resolved an authoritative `accession_number` for this exact filing.
- **Fix:** Use `filing_ref.accession_number` as the fallback when `chunk.accession_number` is absent.

### [Minor] SP-2.2: Reader slice also changes fallback prompts for unrelated profiles

- **Type:** Scope creep
- **File:** `backend/agent_engine/agents/base.py` L215
- **Problem:** `_DEFAULT_SYSTEM_PROMPT` (used by quant/graph/analyst placeholders) was also modified.
- **Fix:** Revert `_DEFAULT_SYSTEM_PROMPT` to BASE behavior.

## Covered Requirements

(37 requirements confirmed covered — see full agent transcript.)

---
