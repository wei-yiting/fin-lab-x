# BDD Verification Report — Round 1 of 5

## Scenarios

### S-inspect-01: StructuredItem 的 detection_source 與所有 block 內容完整顯示
- **Status**: PASS
- **Method**: script (existing pytest)
- **Command**: `uv run pytest backend/tests/ingestion/sec_text_pipeline/test_inspect_view.py::TestInspectMarkdown::test_structured_item_fields -q`
- **Expected**: block 內容整段照原文出現，長度不影響完整性
- **Actual**: `1 passed in 0.05s`

### S-inspect-02: Prelude 依三態規則推斷
- **Status**: PASS
- **Command**: `uv run pytest backend/tests/ingestion/sec_text_pipeline/test_inspect_view.py -k "test_structured_item_fields or test_reclassified_verdict or test_absent_verdict or test_reclassified_row_verdict_is_compact" -q`
- **Actual**: `4 passed, 10 deselected in 0.03s`

### S-inspect-03: 短文字 FlatItem 在 preview 長度限制內，完整顯示不截斷
- **Status**: PASS
- **Command**: `uv run pytest backend/tests/ingestion/sec_text_pipeline/test_inspect_view.py::TestInspectMarkdown::test_flat_item_fields -q`
- **Actual**: `1 passed in 0.04s`

### S-inspect-04: 長文字 FlatItem 的 preview 被截斷，但完整字數仍照實顯示
- **Status**: PASS
- **Command**: `uv run pytest backend/tests/ingestion/sec_text_pipeline/test_inspect_view.py::TestInspectMarkdown::test_flat_item_long_text_preview_truncated -q`
- **Actual**: `1 passed in 0.04s`

### S-inspect-05: 三種 detection_source 值都能正確顯示
- **Status**: PASS
- **Method**: ad-hoc Python script (`text_fallback` branch); `markdown_h3`/`markdown_h4` covered by S-inspect-01/02
- **Actual**: `PASS` printed, `EXIT_CODE=0` — `assert "detection_source: text_fallback" in md` held

### S-inspect-06: 摘要表對混合 kind 的 filing 給出一致的欄位配置
- **Status**: PASS
- **Actual**: `2 passed in 0.07s`

### S-inspect-07: `--verbose` 摘要表不洩漏任何內文
- **Status**: PASS
- **Actual**: `2 passed in 0.04s`

### S-inspect-08: StructuredItem 的 prelude 與多個 block 串接，保留 heading 當區隔
- **Status**: PASS
- **Actual**: `2 passed, 12 deselected in 0.04s`

### S-inspect-09: `--section` 查詢 FlatItem 時直接輸出原始文字
- **Status**: PASS
- **Actual**: `2 passed in 0.16s`

### S-inspect-10: `--section` 的 key 比對大小寫不敏感
- **Status**: ERROR
- **Command**: `uv run pytest backend/tests/ingestion/sec_text_pipeline/test_inspect_view.py::test_key_is_case_insensitive -q`
- **Actual**: Exit code 4 — pytest collection error, no such node ID
- **Details**: `test_key_is_case_insensitive` is nested inside `class TestSectionText`, not module-level. Corrected node ID `test_inspect_view.py::TestSectionText::test_key_is_case_insensitive` → `1 passed in 0.05s`. Verification-plan doc defect (missing class qualifier), not a code regression.

### S-inspect-11: 查詢一個這份 filing 沒有的 key，列出可用的 key 清單
- **Status**: ERROR
- **Actual**: Exit code 4 — pytest collection error, no such node ID
- **Details**: `test_unknown_key_lists_available` also lives inside `class TestSectionText`. Corrected node ID → `2 passed in 0.14s`. Same doc defect class as S-inspect-10.

### S-inspect-12: 對同一 ticker/fiscal_year 重複執行 `inspect`，覆蓋既有檔案
- **Status**: PASS
- **Actual**: `1 passed in 0.05s`

### S-inspect-13: 三種輸出模式對 filing header 的顯示行為
- **Status**: ERROR
- **Actual**: Exit code 4 — pytest collection error, no such node ID
- **Details**: `test_metadata_header` lives inside `class TestInspectMarkdown`. Corrected node ID → `4 passed in 0.08s`. Same doc defect class.

### S-inspect-14: 未快取過的 ticker 直接查詢，自動完成 fetch+parse
- **Status**: PASS
- **Actual**: `1 passed in 0.06s`

### S-inspect-15: 預設輸出路徑與環境變數覆寫路徑
- **Status**: PASS
- **Actual**: pytest `2 passed, 3 warnings in 1.43s` (warnings unrelated, `edgartools` import-time deprecation); grep confirmed `.gitignore` coverage

### S-inspect-16: 同時給兩個互斥的 mode flag，CLI 立即拒絕
- **Status**: PASS
- **Method**: real CLI subprocess invocation (no dedicated pytest, per plan)
- **Actual**: Both combinations rejected at argparse stage, exit code 2, no network call attempted

### S-inspect-17: 已有快取的 ticker 加上 `--force`，略過快取重新 parse
- **Status**: PASS
- **Actual**: `1 passed in 0.05s`

### S-inspect-18: Filing 全部 section 皆空或 stub，CLI 印出含 ticker/年度/accession 的清楚錯誤
- **Status**: PASS
- **Actual**: pytest `1 passed, 25 deselected in 0.08s`; ad-hoc script confirmed CLI boundary surfaces all 3 values + exception type name

### S-inspect-19: 格式不正確的 ticker，CLI 印出清楚訊息而非洩漏 traceback
- **Status**: PASS
- **Actual**: `1 passed in 0.03s`

### J-inspect-01: 首次對未快取的 ticker 執行完整 inspect，並對照 SEC 原文核對
- **Status**: FAIL
- **Command**: `time uv run python -m backend.ingestion.sec_text_pipeline inspect --ticker MSFT --fiscal-year 2024`
- **Actual**: Exit code 1. `EmptyFilingError: Parsed 0 substantive items for MSFT FY2024 (accession 0000950170-24-087843); refusing to cache an empty filing.` No output file written. Real 42s run against live EDGAR (not a timeout/rate-limit).
- **Details**: Root cause: `parser._parse_items` skips any section where `section.item` is falsy. Live MSFT FY2024 fetch → all 24 sections have `section.item == None`. Parallel live AAPL FY2024 fetch → all sections populate `.item` correctly. MSFT-specific, not a systemic edgartools regression.

### J-inspect-02: Operator 標準抽查工作流程——先 `--verbose` 掃視，再 `--section` 深入
- **Status**: FAIL
- **Actual**: Step 1 (MSFT FY2024 `--verbose`) fails with the same `EmptyFilingError` as J-inspect-01 — can't proceed to step 2/3 against MSFT.
- **Details**: Plan's Method note allows a fallback ("可沿用...或建 toy fixture"). Verifier substituted already-cached real AAPL FY2025 data: `--verbose` → 17-row table incl. 2 reclassified items; `--section 8` on the reclassified item → exit 0, 62,190 bytes, zero `##` occurrences. Fallback run PASSES — confirms the verbose→section CLI mechanism itself is sound. Scenario still marked FAIL because it's written against MSFT FY2024 specifically and that literal journey doesn't complete.

## Full Regression

- **Command**: `uv run pytest backend/tests/ingestion/sec_text_pipeline/ backend/tests/common/test_data_paths.py -q`
- **Actual**: `133 passed, 3 warnings in 2.59s`

## Summary

| Metric | Value |
|--------|-------|
| Total | 21 |
| Passed | 16 |
| Failed | 2 |
| Errors | 3 |

**Failed scenario IDs**: J-inspect-01, J-inspect-02
**Error scenario IDs**: S-inspect-10, S-inspect-11, S-inspect-13
