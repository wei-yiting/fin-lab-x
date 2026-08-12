# Code Review Round 1

> Reviewer: gpt-5.6-sol | Date: 2026-08-12
>
> (Copy the reviewer slug and date verbatim — do not self-identify.)

## Summary

| Metric | Count |
|--------|-------|
| Total issues | 4 |
| Blocking | 0 |
| Major | 1 |
| Minor | 3 |
| Suggestion | 0 |
| Library checks | 1 |

## Issues

### [Major] M-1.1: The new CLI and output-path resolver have no behavioral tests
- **File:** `backend/ingestion/sec_text_pipeline/__main__.py` L37
- **Problem:** The changes add a 119-line executable surface, but the new tests invoke only the three render functions. Argument dispatch, default/`--verbose` behavior, `--section`, `inspect` file creation through `get_sec_text_inspect_dir()`, `--force` forwarding, and error exits are untested. The resolver's default and environment override are also absent from `test_data_paths.py`. This falls short of design-envelope §5's "happy path + one legible-failure case per behavior" standard and leaves the CLI acceptance criteria unproved.
- **Fix:** Add focused CLI tests using a toy `ParsedFiling`: monkeypatch `parse_filing`, route `get_sec_text_inspect_dir()` to `tmp_path`, and cover summary/default, `--verbose`, case-insensitive `--section`, inspect path/content, `--force` forwarding, and one error exit. Extend `test_data_paths.py` with default and `SEC_TEXT_INSPECT_DIR` override cases.

### [Minor] m-1.1: Malformed ticker input escapes as a traceback
- **File:** `backend/ingestion/sec_text_pipeline/__main__.py` L61
- **Problem:** `_load_filing()` catches only `FinLabError`, but `LocalFilingStore._validate_ticker()` raises `ValueError`. For example, `--ticker ../BAD --fiscal-year 2025` produces a full traceback instead of a concise CLI error. This is not a legible failure under design-envelope §5 and §7.
- **Fix:** Convert ticker-validation failures to the project error taxonomy, validate the ticker through an `argparse` type, or catch this specific `ValueError` at the CLI boundary. Print the existing message to stderr, exit with status 1, and add a regression test asserting that no traceback is emitted.

### [Minor] m-1.2: `[Speculative Generality]` Character-count helper contains an unreachable branch
- **File:** `backend/ingestion/sec_text_pipeline/inspect_view.py` L37
- **Problem:** The hunk `if isinstance(item, FlatItem): return len(item.text)` cannot run because `_item_chars()` is called only from the `StructuredItem` branch at L117–126. The generic `ParsedItem` abstraction is therefore unused indirection, contrary to design-envelope §0's reachability rule.
- **Fix:** Delete `_item_chars()` and inline the structured-item calculation at its only call site, or narrow it explicitly to `StructuredItem` without the unreachable branch.

### [Minor] m-1.3: Filing-store documentation now contradicts the implementation
- **File:** `backend/ingestion/sec_text_pipeline/filing_store.py` L5
- **Problem:** The module docstring still describes the inspect helper as a "future extension, not yet built," while this changeset adds that helper and CLI. The protocol docstring at L30–34 likewise cites hypothetical inspect-CLI listing support that this CLI does not implement.
- **Fix:** Update the module docstring to reference the implemented `inspect_view.py`/CLI, and remove the speculative listing example from `FilingStore` documentation.

## Documentation Gaps

| Folder | Missing |
|--------|---------|
| — | — |

## Official Standards Check

| Library | Version | API Used | Status | Notes |
|---------|---------|----------|--------|-------|
| python-dotenv | 1.0.1 | `load_dotenv(Path(...))` | ✅ Current | Correct, non-deprecated API. `PathLike` is supported, `override=False` preserves existing environment variables, and ignoring the boolean return is acceptable because a missing `.env` is intentionally silent. |

---

# Spec Conformance Round 1

> Reviewer: gpt-5.6-sol | Date: 2026-08-12
> (Copy the reviewer slug and date verbatim — do not self-identify.)

## Summary

| Metric | Count |
|--------|-------|
| Total findings | 2 |
| Missing | 0 |
| Scope creep | 1 |
| Misimplemented | 1 |

## Findings

### [Blocking] SP-1.1: Absent prelude 缺少規定的 chars 數
- **Type:** Misimplemented
- **Spec:** "- [ ] `inspect --ticker X --fiscal-year Y` 產出完整 markdown:每 Item 依 Render 規則攤開(StructuredItem:detection_source / prelude 判定含 chars 數 / blocks 的 heading 與內容;FlatItem:kind + 字數),可對照 SEC 原文檢查" (Linear DEV-134 description)
- **File:** `backend/ingestion/sec_text_pipeline/inspect_view.py` L34
- **Problem:** valid prelude 與 reclassified leading block 都顯示 chars 數,但 absent 分支只輸出 `absent`。因此 `prelude == ""` 且第一個 block heading 非空時,不符合 StructuredItem 的「prelude 判定含 chars 數」要求;summary table 也沿用相同缺漏。
- **Fix:** 將 absent verdict 輸出為例如 `absent (0 chars)`,並更新 inspect markdown 與 summary table 的 toy `ParsedFiling` assertions。

### [Major] SP-1.2: 額外公開未要求的 `--force` mode
- **Type:** Scope creep
- **Spec:** "Detection 結果的人讀驗證面:獨立 view module `sec_text_pipeline/inspect_view.py` 的 `to_inspect_markdown(filing: ParsedFiling) -> str`(整份 render:…)+ CLI 三入口(新增 `sec_text_pipeline/__main__.py`,`python -m backend.ingestion.sec_text_pipeline`,比照 `_html` pipeline 的 CLI 慣例)— `--verbose`(一頁摘要表;無 mode flag 時預設此行為)、`--section <key>`(單 Item 純文字)、`inspect` subcommand(render 到 gitignored 目錄、印出路徑)。這是 prelude 判定人工抽查與四象限 failure 分析的標準工具。" (Linear DEV-134 description)
- **File:** `backend/ingestion/sec_text_pipeline/__main__.py` L53
- **Problem:** spec 明確列出三個 CLI 入口,但實作另外在所有入口公開 `--force`,新增 cache-bypass/reparse 行為與 CLI API surface。Acceptance criterion 只要求 cache miss 自動 fetch + parse,並未要求強制重新 parse。
- **Fix:** 移除 CLI 的 `--force` option、相關參數傳遞與 README 說明;CLI 直接呼叫 `parse_filing(ticker, fiscal_year)`。既有 `parse_filing(..., force=...)` API 不需變更。

## Covered Requirements

✅ 新增獨立 `inspect_view.py` 與 `to_inspect_markdown(filing: ParsedFiling) -> str`,且未修改凍結的 `filing_models.py` — `backend/ingestion/sec_text_pipeline/inspect_view.py`
✅ StructuredItem 顯示 kind、detection_source、valid/reclassified prelude verdict,以及每個 block 的 heading、內容與明確邊界 — `backend/ingestion/sec_text_pipeline/inspect_view.py`
✅ FlatItem 顯示 `kind=flat`、字數與完整 text,未虛構 detection_source、prelude 或 blocks — `backend/ingestion/sec_text_pipeline/inspect_view.py`
✅ Prelude verdict 於 render 時依 schema 推斷,並以空的第一個 block heading 作為 reclassified marker — `backend/ingestion/sec_text_pipeline/inspect_view.py`
✅ Render 對 `detection_source` 採值透明呈現,可自動支援後續 `text_fallback`,且未引入 chunk rendering — `backend/ingestion/sec_text_pipeline/inspect_view.py`
✅ `--verbose` 輸出不含內文的摘要表,無 mode flag 時採相同行為 — `backend/ingestion/sec_text_pipeline/__main__.py`
✅ `--section <key>` 輸出單一 Item plain text,CLI key 大小寫不敏感 — `backend/ingestion/sec_text_pipeline/__main__.py`
✅ `inspect --ticker X --fiscal-year Y` 寫出完整 markdown 並印出路徑 — `backend/ingestion/sec_text_pipeline/__main__.py`
✅ Inspect 目錄使用 env-var overridable resolver,且 `data/sec_text_inspect/` 與 `data/sec_text/` 均已明確加入 gitignore — `backend/common/data_paths.py`
✅ CLI 直接呼叫 cache-first 的 `parse_filing`,cache miss 會自動 fetch + parse — `backend/ingestion/sec_text_pipeline/__main__.py`
✅ Render tests 使用 toy `ParsedFiling` 並做結構斷言,不存取 EDGAR — `backend/tests/ingestion/sec_text_pipeline/test_inspect_view.py`

---

# Round 1 裁決(user,2026-08-12)

| ID | 裁決 | 處置 |
|---|---|---|
| M-1.1 | Accepted(範圍收斂) | 三 mode 各一條 happy path + 一條 legible-failure + data_paths default/override;不重測 render 層已覆蓋的 case-insensitivity |
| m-1.1 | Accepted | CLI boundary 加 catch `ValueError`;壞 ticker 回歸測試併入 M-1.1 的 failure case |
| m-1.2 | Accepted | `_item_chars` 簽名收斂為 `StructuredItem`,移除不可達分支 |
| m-1.3 | Accepted | `filing_store.py` module docstring 改指已落地的 inspect view;Protocol docstring 移除 speculative listing 舉例 |
| SP-1.1 | **Dismissed** | Spec Render 規則明文僅 valid/reclassified 帶 chars 數,absent 定義即「無 prelude」;AC 括號為規則縮寫 → 已改寫 AC 措辭消除歧義(spec 文字修正,code 不變) |
| SP-1.2 | **Declined(ratified 保留)** | `--force` 屬「比照 _html CLI 慣例」範圍;工具用途為抽查活躍變動中的 detection(DEV-136),無 `--force` 時需手動刪 store JSON。裁決寫入 issue description |
