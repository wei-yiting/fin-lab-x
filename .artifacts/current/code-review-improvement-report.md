# Code Review Improvement Report

> **Task:** SEC 10-K Download & Parsing Pipeline
> **Date:** 2026-04-04
> **Rounds:** 4
> **Reviewer model:** Codex (GPT)
> **Fixer model:** Claude

## 架構影響摘要

- Pipeline cache 路徑重構：`fiscal_year=None` 時改為先透過 `store.list_filings()` 查詢本地最新 cache，避免每次都打 SEC API（M-1.1）
- Converter factory 統一：`SECFilingPipeline.create()` 改用 `create_converter()` factory，消除 production code 與 factory 的分歧路徑（S-3.1）
- Downloader 錯誤邊界補完：transient exceptions（`ConnectionError`, `TimeoutError`, `OSError`）現在正確映射為 `TransientError`，使 retry 邏輯能涵蓋真實網路失敗（M-2.3）

## Summary

| 指標 | 數值 |
| --- | --- |
| 總輪數 | 4 |
| 發現 issues 總數 | 15 |
| Blocking | 0/0 fixed |
| Major | 7/7 fixed |
| Minor | 6/6 fixed |
| Suggestion | 2/2 adopted |
| 文件修正 | 1（WHY comment on fiscal year derivation） |

## 所有修正問題詳解

### M-1.1（Major）
- **問題：** `fiscal_year=None` 時 pipeline 先 download 再查 cache，導致「抓最新 10-K」路徑每次都打 SEC
- **修法：** 在 `pipeline.py` 中，`fiscal_year=None` 時先用 `store.list_filings()` 查找本地最新年度，命中則直接回傳 cache
- **影響：** 減少不必要的 SEC API 呼叫，降低 rate limit 風險
- **驗證：** `test_cache_check_uses_list_filings_when_fiscal_year_omitted` ✅

### M-1.2（Major）
- **問題：** `html-to-markdown` 的 `convert()` 回傳型別假設錯誤，只處理 dict 不處理 string
- **修法：** 明確設定 `extract_metadata=True`，加入三路 type check（`str` → `Mapping` → `TypeError`）
- **影響：** 防止非 dict 回傳導致 primary converter 靜默失敗
- **驗證：** `TestAdapterResponseShapes` (3 tests) ✅

### M-1.3（Major）
- **問題：** `_promote_headings()` 核心 heuristic 無 WHY comment
- **修法：** 在 `html_preprocessor.py` 方法前加入 comment block 說明 SEC filing 缺語意 heading、reverse traversal 原因、descendant guard 用途
- **影響：** 維護者能理解 heading promotion 規則的設計意圖
- **驗證：** Code review Round 2 確認 ✅

### M-2.1（Major）
- **問題：** `pydantic` 未列為直接 dependency，僅靠 `fastapi` transitive 引入
- **修法：** 在 `pyproject.toml` 加入 `pydantic>=2.0`
- **影響：** 消除 fragile packaging，確保 clean install 能正確解析 dependencies
- **驗證：** `uv sync` 成功 ✅

### M-2.2（Major）
- **問題：** converter type check 只用 `isinstance(result, dict)`，non-dict Mapping 會被 stringify
- **修法：** 改用 `collections.abc.Mapping` check，並在 unexpected type 時 raise `TypeError`
- **影響：** 正確處理 `html-to-markdown` 各版本可能的回傳型別
- **驗證：** `TestAdapterResponseShapes` 覆蓋 dict/str/TypeError ✅

### M-2.3（Major）
- **問題：** `SECDownloader.download()` 只映射 `CompanyNotFoundError`，其餘 edgartools exceptions 繞過 retry
- **修法：** 在 `sec_downloader.py` 加入 outer try/except，將 `ConnectionError`/`TimeoutError`/`OSError` 映射為 `TransientError`
- **影響：** Batch retry 邏輯能正確處理真實網路/SEC 失敗
- **驗證：** `TestTransientErrorMapping` (8 tests) 覆蓋所有 call sites ✅

### M-3.1（Major）
- **問題：** Integration test `test_s_dl_03_non_calendar_fy_nvda` 未實際驗證 `period_of_report` 推導
- **修法：** 新增 `TestFiscalYearDerivation` 2 個 unit tests，用 mock 設定 `period_of_report` 和 `filing_date` 年份不同，驗證 `fiscal_year` 取自 `period_of_report`
- **影響：** 確保 fiscal year 推導邏輯有回歸保護
- **驗證：** `test_fiscal_year_derived_from_period_of_report_not_filing_date`, `test_fiscal_year_differs_from_filing_date_year` ✅

### m-1.1（Minor）
- **問題：** Fallback threshold `0.01` 是 magic number
- **修法：** 抽為 `_MIN_OUTPUT_RATIO = 0.01` 並加 comment
- **影響：** 維護者可理解 fallback 觸發條件
- **驗證：** 既有 `test_below_one_percent_triggers_fallback` 仍通過 ✅

### m-2.1（Minor）
- **問題：** Integration test hardcode 個人 email
- **修法：** 改為從 `EDGAR_IDENTITY` env var 讀取，未設定時 skip
- **影響：** 消除 source control 中的個人資料
- **驗證：** Integration tests skip when env not set ✅

### m-2.2 + m-3.2（Minor）
- **問題：** Transient error mapping 測試不完整，缺 `filter()` / `latest()` 路徑
- **修法：** 新增 `TestTransientErrorMapping` 完整覆蓋 `Company()`, `get_filings()`, `filter()`, `latest()`, `html()` 各 call site
- **影響：** 確保所有 edgartools 呼叫路徑的 transient error 映射有測試保護
- **驗證：** 8 tests all pass ✅

### m-3.1（Minor）
- **問題：** Converter 新增的 Mapping/TypeError 分支無測試
- **修法：** `TestAdapterResponseShapes` 3 tests 覆蓋 dict, str, unexpected type
- **影響：** Response shape handling 有回歸保護
- **驗證：** 3 tests pass ✅

### m-4.1（Minor）
- **問題：** `derived_fy = int(str(filing.period_of_report)[:4])` 無 WHY comment
- **修法：** 在 `sec_downloader.py` L60 前加入 comment 說明為何取 `period_of_report` 而非 `filing_date`
- **影響：** 防止維護者錯誤修改為使用 `filing_date`
- **驗證：** Code review Round 4 確認 ✅

### S-1.1 / S-3.1（Suggestion）
- **問題：** `create_converter()` 未被 production code 使用
- **修法：** `SECFilingPipeline.create()` 改用 `create_converter()`，消除重複建構路徑
- **影響：** Converter 建構邏輯統一在 factory 中
- **驗證：** `TestCreateClassMethod` 更新後 pass ✅

## 文件修正

| 目錄 | 修正內容 |
| --- | --- |
| `sec_downloader.py` | 新增 fiscal year derivation WHY comment |
| `html_preprocessor.py` | 新增 heading promotion heuristic WHY comment block |

## 未處理項目

| 類型 | 內容 | 原因 | 建議後續 |
| --- | --- | --- | --- |
| Env-blocked | Integration tests (8 tests, `@sec_integration` marker) | 需要 `EDGAR_IDENTITY` env var + live SEC API access | 在 CI/CD 中設定 env var 後執行 |
| Suggestion | `backend/ingestion/sec_filing_pipeline/README.md` | Documentation gap (non-blocking) | 建議後續加入 pipeline stages 說明、storage contract、extension guidelines |
| Pre-existing | 9 lint errors in `test_pipeline.py` (8x E402, 1x F841) | Pre-existing from original implementation | 建議另外 PR 修正 |

## Final Verification Results

### Code Level

- [x] Unit Tests: 127/127 passed (8 integration deselected)
- [x] Lint: 0 new errors introduced (9 pre-existing)
- [x] Format: all 17 files formatted correctly

### Behavior Level

- [x] S-dl-01 (Cache-first): covered by `TestProcessCacheHit`, `TestProcessCacheMiss`
- [x] S-dl-02 (Batch mixed): covered by `test_batch_mixed_outcomes`
- [x] S-dl-03 (Non-calendar FY): covered by `TestFiscalYearDerivation`
- [x] S-dl-04 (Latest filing): covered by `test_cache_check_uses_list_filings_when_fiscal_year_omitted`
- [x] S-dl-05 (Error types): covered by `TestDownloadErrorMapping`, `TestProcessValidation`
- [x] S-dl-06 (Ticker normalization): covered by `TestProcessTickerNormalization`
- [x] S-prep-01~03 (Preprocessor): covered by `TestStripXBRLTags`, `TestDecorativeStyleRemoval`, `TestFontTagUnwrapping`, `TestHeadingPromotion`
- [x] S-conv-01~04 (Converter): covered by `TestAtxHeadings`, `TestConvertWithFallback`, `TestAdapterResponseShapes`
- [x] S-store-01~05 (Store): covered by store test classes

### Runtime / Observable Level

- [ ] SEC Integration tests: env-blocked (requires `EDGAR_IDENTITY`)

## All Changed Files

| 檔案 | Review 修正摘要 |
| --- | --- |
| `pipeline.py` | Cache-first for fiscal_year=None (M-1.1), wired `create_converter()` (S-3.1) |
| `html_to_md_converter.py` | Mapping/str/TypeError response handling (M-1.2, M-2.2), `_MIN_OUTPUT_RATIO` (m-1.1) |
| `html_preprocessor.py` | WHY comments on heading promotion (M-1.3) |
| `sec_downloader.py` | Transient error wrapping (M-2.3), WHY comment on fiscal year (m-4.1) |
| `pyproject.toml` | Direct `pydantic>=2.0` dependency (M-2.1) |
| `test_pipeline.py` | Cache path test update (M-1.1), integration test EDGAR_IDENTITY from env (m-2.1), create_converter test (S-3.1), removed dead variable (M-3.1) |
| `test_sec_downloader.py` | `TestTransientErrorMapping` 8 tests (M-2.3, m-2.2, m-3.2), `TestFiscalYearDerivation` 2 tests (M-3.1) |
| `test_html_to_md_converter.py` | `TestAdapterResponseShapes` 3 tests (m-3.1) |
| `uv.lock` | Updated from `uv sync` after pydantic dependency add |
