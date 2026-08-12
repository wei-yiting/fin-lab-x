# Executable Verification Plan

> 從 `artifacts/current/verification-plan.md` 的 Automated Verification 區段抽出，
> 供 bdd-e2e-loop 的 Verifier subagent 執行。沒有未解析的 `[POST-CODING: ...]`
> placeholder——僅存的一個（S-inspect-04 的截斷長度上限）已在 implementation 落地時
> 被另一個 coding agent 解成具體值（500）並更新回 verification-plan.md。
>
> 執行環境：`cwd` 為 repo root（`/Users/dong.wyt/Documents/dev-projects/fin-lab-x-wt/
> sec-filing-inspect-cli`），Python 套件管理用 `uv run`。所有 pytest 路徑對應
> `backend/tests/ingestion/sec_text_pipeline/`、`backend/tests/common/test_data_paths.py`。
> CLI entry point 為 `python -m backend.ingestion.sec_text_pipeline`（`uv run python -m
> backend.ingestion.sec_text_pipeline ...`）。

---

## Automated Verification

### Deterministic

#### S-inspect-01: StructuredItem 的 detection_source 與所有 block 內容完整顯示
- **Method**: script（直接呼叫 render function，用手造 `ParsedFiling`，不打 EDGAR）
- **Steps**:
  1. 建構一個 `StructuredItem`（`detection_source="markdown_h3"`），兩個 `Block`：
     block 1 內容為 4,500 字的 `"x" * 4500`、block 2 內容約 1,200 字
  2. 包成 `ParsedFiling(metadata=..., items=[item])`
  3. 呼叫 `to_inspect_markdown(filing)`
  4. Assert: 輸出含 `"detection_source: markdown_h3"`
  5. Assert: 輸出含完整的 `"x" * 4500`（不是截斷版本），且不出現任何 chunk 邊界標記
- **Expected**: block 內容整段照原文出現，長度不影響完整性
- **既有測試**: `uv run pytest backend/tests/ingestion/sec_text_pipeline/test_inspect_view.py::TestInspectMarkdown::test_structured_item_fields -q`

#### S-inspect-02: Prelude 依三態規則推斷
- **Method**: script（三筆 toy fixture，各自呼叫 `to_inspect_markdown` 與 `to_summary_text`）
- **Steps**:
  1. valid 案例：`prelude` 設為非空字串（如 2,532 字）→ assert 輸出含
     `f"valid ({len(prelude):,} chars)"`
  2. reclassified 案例：`prelude=""`，`blocks=[Block(heading="", text="x"*3500), ...]`
     → assert 輸出含 `"reclassified leading block (3,500 chars in blocks[0])"`
     （`to_inspect_markdown`）或 `"reclassified (3,500 chars)"`（`to_summary_text`
     的 compact 版本）
  3. absent 案例：`prelude=""`，`blocks[0].heading` 非空 → assert 輸出含 `"absent"`
     （`to_inspect_markdown`）或對應的 compact 字串（`to_summary_text`）
- **Expected**: 三種狀態各自輸出正確的判定字串
- **既有測試**: `uv run pytest backend/tests/ingestion/sec_text_pipeline/test_inspect_view.py -k "test_structured_item_fields or test_reclassified_verdict or test_absent_verdict or test_reclassified_row_verdict_is_compact" -q`

#### S-inspect-03: 短文字 FlatItem 在 preview 長度限制內，完整顯示不截斷
- **Method**: script
- **Steps**:
  1. 建構 `FlatItem(item="4", title="Mine Safety Disclosures", text="Not applicable.")`
  2. 呼叫 `to_inspect_markdown(make_filing([item]))`
  3. Assert: 輸出含 `"- text: 16 chars"`
  4. Assert: 輸出含完整的 `"Not applicable."`，且緊接其後沒有截斷標記（如「…」）
- **Expected**: 短內容原樣顯示
- **既有測試**: `uv run pytest backend/tests/ingestion/sec_text_pipeline/test_inspect_view.py::TestInspectMarkdown::test_flat_item_fields -q`

#### S-inspect-04: 長文字 FlatItem 的 preview 被截斷，但完整字數仍照實顯示
- **Method**: script
- **Steps**:
  1. 建構 `FlatItem(item="9b", title="Other Information", text="x" * 2000)`
  2. 呼叫 `to_inspect_markdown(make_filing([item]))`
  3. Assert: 輸出含 `"- text: 2,000 chars"`（完整字數，不是截斷後長度）
  4. Assert: 輸出含 500 個 `"x"` 加上截斷標記（`"x" * 500 + "…"`），且**不含**
     `"x" * 501`（截斷點之後的原文不應出現）
- **Expected**: 字數統計反映完整長度，但顯示的內容本身有長度上限（實際上限 500）
- **既有測試**: `uv run pytest backend/tests/ingestion/sec_text_pipeline/test_inspect_view.py::TestInspectMarkdown::test_flat_item_long_text_preview_truncated -q`

#### S-inspect-05: 三種 detection_source 值都能正確顯示
- **Method**: script
- **Steps**:
  1. 對 `detection_source` 分別為 `"markdown_h3"`、`"markdown_h4"`、`"text_fallback"`
     （第三個是手造的 toy 值，目前 real data 不會出現）的三個 `StructuredItem`，各自
     呼叫 `to_inspect_markdown`
  2. Assert: 每次輸出都含 `f"detection_source: {值}"`，且不會因為第三個值而拋出例外
- **Expected**: render 邏輯對任意字串值都能正確顯示
- **既有測試**: 無專屬測試（使用者裁決 code inspection 已足夠）；`markdown_h3`/
  `markdown_h4` 由 S-inspect-01/02 的既有測試間接涵蓋。`text_fallback` 這一分支
  Verifier 直接跑一段 ad-hoc Python script 驗證（見下方 Verifier 指示）

#### S-inspect-06: 摘要表對混合 kind 的 filing 給出一致的欄位配置
- **既有測試**: `uv run pytest backend/tests/ingestion/sec_text_pipeline/test_inspect_view.py::TestSummaryText::test_counts_and_rows backend/tests/ingestion/sec_text_pipeline/test_main.py::test_default_prints_summary -q`

#### S-inspect-07: `--verbose` 摘要表不洩漏任何內文
- **既有測試**: `uv run pytest backend/tests/ingestion/sec_text_pipeline/test_inspect_view.py::TestSummaryText::test_excludes_body_content backend/tests/ingestion/sec_text_pipeline/test_main.py::test_default_prints_summary -q`

#### S-inspect-08: StructuredItem 的 prelude 與多個 block 串接，保留 heading 當區隔
- **既有測試**: `uv run pytest backend/tests/ingestion/sec_text_pipeline/test_inspect_view.py -k "test_structured_section_keeps_all_content or test_structured_section_blocks_stay_separated" -q`

#### S-inspect-09: `--section` 查詢 FlatItem 時直接輸出原始文字
- **既有測試**: `uv run pytest backend/tests/ingestion/sec_text_pipeline/test_inspect_view.py::TestSectionText::test_flat_section_is_raw_text backend/tests/ingestion/sec_text_pipeline/test_main.py::test_section_prints_plain_text -q`

#### S-inspect-10: `--section` 的 key 比對大小寫不敏感
- **既有測試**: `uv run pytest backend/tests/ingestion/sec_text_pipeline/test_inspect_view.py::TestSectionText::test_key_is_case_insensitive -q`

#### S-inspect-11: 查詢一個這份 filing 沒有的 key，列出可用的 key 清單
- **既有測試**: `uv run pytest backend/tests/ingestion/sec_text_pipeline/test_inspect_view.py::TestSectionText::test_unknown_key_lists_available backend/tests/ingestion/sec_text_pipeline/test_main.py::test_unknown_section_key_fails_legibly -q`

#### S-inspect-12: 對同一 ticker/fiscal_year 重複執行 `inspect`，覆蓋既有檔案
- **既有測試**: `uv run pytest backend/tests/ingestion/sec_text_pipeline/test_main.py::test_inspect_writes_file_and_prints_path -q`（精確路徑相等斷言，見 verification-plan.md 現況說明的裁決理由）

#### S-inspect-13: 三種輸出模式對 filing header 的顯示行為
- **既有測試**: `uv run pytest backend/tests/ingestion/sec_text_pipeline/test_inspect_view.py::TestInspectMarkdown::test_metadata_header backend/tests/ingestion/sec_text_pipeline/test_inspect_view.py::TestSummaryText::test_counts_and_rows backend/tests/ingestion/sec_text_pipeline/test_inspect_view.py::TestSectionText::test_flat_section_is_raw_text backend/tests/ingestion/sec_text_pipeline/test_main.py::test_section_prints_plain_text -q`

#### S-inspect-14: 未快取過的 ticker 直接查詢，自動完成 fetch+parse
- **既有測試**: `uv run pytest backend/tests/ingestion/sec_text_pipeline/test_main.py::test_default_prints_summary -q`

#### S-inspect-15: 預設輸出路徑與環境變數覆寫路徑
- **既有測試**: `uv run pytest backend/tests/common/test_data_paths.py::test_resolves_repo_root_independent_of_cwd backend/tests/common/test_data_paths.py::test_env_override_sec_text_inspect_dir -q`
- **額外檢查**: `grep -n "sec_text_inspect" .gitignore`

#### S-inspect-16: 同時給兩個互斥的 mode flag，CLI 立即拒絕
- **Method**: script（CLI 整合層，直接 subprocess 呼叫，因為使用者裁決這條走
  code-inspection、沒有專屬 pytest——Verifier 直接執行實際 CLI 指令驗證 runtime 行為）
- **Steps**:
  1. `uv run python -m backend.ingestion.sec_text_pipeline --ticker AAPL --fiscal-year 2024 --verbose --section 7`
     → assert exit code 為 2，stderr 含 mutually-exclusive 相關錯誤訊息
  2. `uv run python -m backend.ingestion.sec_text_pipeline inspect --ticker AAPL --fiscal-year 2024 --verbose`
     → assert exit code 為 2，stderr 含 unrecognized-argument 相關錯誤訊息
  3. 兩次都不需要網路（argparse 在呼叫 `parse_filing` 之前就會 exit，不會真的打 EDGAR）
- **Expected**: 兩種衝突組合都在參數解析階段被拒絕

#### S-inspect-17: 已有快取的 ticker 加上 `--force`，略過快取重新 parse
- **既有測試**: `uv run pytest backend/tests/ingestion/sec_text_pipeline/test_main.py::test_inspect_writes_file_and_prints_path -q`

#### S-inspect-18: Filing 全部 section 皆空或 stub，CLI 印出含 ticker/年度/accession 的清楚錯誤
- **既有測試**: 無 CLI 層專屬測試（使用者裁決 code inspection 已足夠，理由見
  verification-plan.md）。三值訊息建構本身由 `uv run pytest backend/tests/ingestion/sec_text_pipeline/test_parser.py -k "EmptyFiling or empty_filing" -q` 涵蓋——Verifier 用這個
  關鍵字先確認測試存在並通過，另外用一段 ad-hoc Python script 驗證 `EmptyFilingError`
  走 CLI 邊界時確實被 `except (FinLabError, ValueError)` 攔截（見下方 Verifier 指示）

#### S-inspect-19: 格式不正確的 ticker，CLI 印出清楚訊息而非洩漏 traceback
- **既有測試**: `uv run pytest backend/tests/ingestion/sec_text_pipeline/test_main.py::test_malformed_ticker_fails_legibly -q`

---

### Journey Scenarios（Deterministic）

#### J-inspect-01: 首次對未快取的 ticker 執行完整 inspect，並對照 SEC 原文核對
- **Method**: script（真實 EDGAR fetch）
- **Ticker 變更（2026-08-13）**: 原訂 MSFT FY2024，Round 1 實跑證實必然
  `EmptyFilingError`（edgartools 5.17.1 對 MSFT/GE/DIS 回傳 spaced section 名，
  `Section.item = None`；已知限制，修復在 DEV-136 branch，尚未 merge）。改用
  **AAPL FY2024**。
- **Steps**:
  1. 檢查 `data/sec_text/AAPL/10-K/2024.json` 與 inspect 輸出目錄下 AAPL FY2024 的
     殘留檔案是否存在；若存在，記錄下來但不要刪除使用者的資料
  2. `time uv run python -m backend.ingestion.sec_text_pipeline inspect --ticker AAPL --fiscal-year 2024`
  3. `cat <印出的路徑>` 讀取內容，檢查開頭格式是否符合 `f"# AAPL 10-K FY2024"`
  4. Assert（自動化部分）：exit code 為 0、印出的路徑存在、檔案非空、檔案內容開頭符合
     `"# AAPL 10-K FY2024"` 格式
  5. 人工核對部分（對照 SEC EDGAR 原文）不在本輪自動驗證範圍內，留給 Manual/UAT
- **Expected**: 完整彈道走通

#### J-inspect-02: Operator 標準抽查工作流程——先 `--verbose` 掃視，再 `--section` 深入
- **Method**: script（真實 filing——Round 1 已用 AAPL FY2025 實際跑過一次）
- **Ticker 變更（2026-08-13）**: 原訂沿用 J-inspect-01 的 MSFT FY2024。改用
  **AAPL FY2025**（已快取，Round 1 確認有 reclassified Item `8`/`1a`）。
- **Steps**:
  1. `uv run python -m backend.ingestion.sec_text_pipeline --ticker AAPL --fiscal-year 2025 --verbose`
  2. 掃視輸出，找到 prelude 欄位顯示 `"reclassified"` 的那一列（Round 1 紀錄：`8` 或
     `1a`），記下 item key
  3. `uv run python -m backend.ingestion.sec_text_pipeline --ticker AAPL --fiscal-year 2025 --section <該 key>`
  4. Assert: 兩次呼叫都成功（exit code 0），`--section` 輸出非空且不含 markdown 標記
     （`##`）
- **Expected**: 兩個 CLI 入口銜接起來構成一次完整的抽查流程

---

## Verifier 額外指示（非既有 pytest 涵蓋的部分）

以下三個 ad-hoc 檢查沒有對應的具名 pytest，需要 Verifier 自己寫一段簡短的 Python
one-liner 或 inline script 執行並回報結果（不要建立新檔案，執行完即丟）：

1. **S-inspect-05 的 `text_fallback` 分支**：
   ```python
   from backend.ingestion.sec_text_pipeline.filing_models import ParsedFiling, StructuredItem, Block
   from backend.ingestion.sec_text_pipeline.inspect_view import to_inspect_markdown
   from backend.tests.ingestion.sec_text_pipeline.conftest import make_metadata
   item = StructuredItem(item="7", title="X", detection_source="text_fallback",
                          prelude="p", blocks=[Block(heading="H", text="t")])
   md = to_inspect_markdown(ParsedFiling(metadata=make_metadata(), items=[item]))
   assert "detection_source: text_fallback" in md
   print("PASS")
   ```

2. **S-inspect-18 的 CLI 邊界攔截**（`EmptyFilingError` 走 `except (FinLabError,
   ValueError)`）：
   ```python
   from unittest.mock import patch
   from backend.ingestion.sec_text_pipeline.__main__ import main
   from backend.ingestion.sec_text_pipeline.parser import EmptyFilingError
   import pytest, io, contextlib
   with patch("backend.ingestion.sec_text_pipeline.__main__.parse_filing",
              side_effect=EmptyFilingError(
                  "Parsed 0 substantive items for ZZZZ FY2020 "
                  "(accession 0000000000-20-000000); refusing to cache an empty filing.")):
       err = io.StringIO()
       with contextlib.redirect_stderr(err):
           try:
               main(["--ticker", "ZZZZ", "--fiscal-year", "2020"])
               raised = False
           except SystemExit as e:
               raised = True
               code = e.code
   assert raised and code == 1
   out = err.getvalue()
   assert "ZZZZ" in out and "2020" in out and "0000000000-20-000000" in out
   assert "EmptyFilingError" in out
   print("PASS")
   ```

3. **S-inspect-16**：直接跑 Steps 裡列出的兩條 CLI 指令即可，不需要額外 script。

---

## 完整回歸

Verifier 完成上述個別檢查後，額外跑一次完整套件確認沒有其他遺漏：

```bash
uv run pytest backend/tests/ingestion/sec_text_pipeline/ backend/tests/common/test_data_paths.py -q
```
