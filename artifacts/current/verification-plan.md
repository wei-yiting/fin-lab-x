# Verification Plan

## Meta

- Scenarios Reference: `artifacts/current/bdd-scenarios.md`
- Generated: 2026-08-12

> 這份 verification plan 比一般情況特殊：implementation 已經存在（commit `046e047` +
> `1ec26d1`），而且已經被平行的 `code-review-loop` review 過兩輪。因此本文件除了寫「怎麼
> 驗證」之外，也對每個 scenario 標註了現況——已經被哪個既有測試涵蓋、還是全新缺口。標為
> **「尚未實作」**的項目執行下方步驟時預期會失敗，這是準確訊號，不是計畫缺陷。所有 CLI 命令
> 以 `python -m backend.ingestion.sec_text_pipeline ...` 為準，對應 `__main__.py` 的實際
> entry point。
>
> **2026-08-12 使用者裁決（缺口清單逐項覆核後）**：交接文件列出的 9 個候選缺口，裁決結果為
> 3 收 6 駁——收 S-inspect-04（實作 + 測試）、S-inspect-08（顯式分隔斷言）、S-inspect-11
> CLI 層（legible-failure 測試）；其餘（S-inspect-05/12/13/16/18 的補測建議、J-inspect-02
> 的 journey 測試）標為「既有覆蓋 / inspection 驗證」。依據：envelope §5 標準 +
> review round 1 M-1.1 已裁決的測試範圍收斂；各項理由記在該 scenario 的現況欄。

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
- **現況**: 已涵蓋 —— `test_inspect_view.py::TestInspectMarkdown::test_structured_item_fields`
  斷言了 detection_source 顯示與 block 內容完整出現；4,500 字這個具體長度沒有專門測過，但
  render 邏輯（`_render_item_markdown`）對 block content 沒有任何截斷分支，屬於同一條路徑

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
- **現況**: 已涵蓋 —— `test_inspect_view.py::test_structured_item_fields` /
  `test_reclassified_verdict` / `test_absent_verdict`（markdown 版本）與
  `test_reclassified_row_verdict_is_compact`（summary 版本）

#### S-inspect-03: 短文字 FlatItem 在 preview 長度限制內，完整顯示不截斷
- **Method**: script
- **Steps**:
  1. 建構 `FlatItem(item="4", title="Mine Safety Disclosures", text="Not applicable.")`
  2. 呼叫 `to_inspect_markdown(make_filing([item]))`
  3. Assert: 輸出含 `"- text: 16 chars"`
  4. Assert: 輸出含完整的 `"Not applicable."`，且緊接其後沒有截斷標記（如「…」）
- **Expected**: 短內容原樣顯示
- **現況**: 已涵蓋 —— 截斷邏輯落地後（見 S-inspect-04），
  `test_inspect_view.py::test_flat_item_fields` 補上了「短文字完整顯示且無截斷標記」的
  斷言（`FLAT_BODY in md` + `"…" not in md`），確認 `_flat_preview` 對短於上限的文字
  是 no-op

#### S-inspect-04: 長文字 FlatItem 的 preview 被截斷，但完整字數仍照實顯示
- **Method**: script
- **Steps**:
  1. 建構 `FlatItem(item="9b", title="Other Information", text="x" * 2000)`
  2. 呼叫 `to_inspect_markdown(make_filing([item]))`
  3. Assert: 輸出含 `"- text: 2,000 chars"`（完整字數，不是截斷後長度）
  4. Assert: 輸出含 500 個 `"x"` 加上截斷標記（`"x" * 500 + "…"`），且**不含**
     `"x" * 501`（截斷點之後的原文不應出現）
- **Expected**: 字數統計反映完整長度，但顯示的內容本身有長度上限
- **現況**: 已實作並涵蓋 —— `inspect_view.py` 新增 `_FLAT_PREVIEW_LIMIT = 500` 與
  `_flat_preview()`（上限取 500 而非交接文件建議的 200：FlatItem 目前的實際來源是
  「未能結構化的 Item」，preview 需要長到足以判斷「正文 vs. stub 殘渣」）；
  `test_inspect_view.py::test_flat_item_long_text_preview_truncated` 逐字對應本
  scenario 的三個 assertion。截斷長度的最終驗收見 Manual Verification 的
  S-inspect-04 條目

#### S-inspect-05: 三種 detection_source 值都能正確顯示
- **Method**: script
- **Steps**:
  1. 對 `detection_source` 分別為 `"markdown_h3"`、`"markdown_h4"`、`"text_fallback"`
     （第三個是手造的 toy 值，目前 real data 不會出現）的三個 `StructuredItem`，各自
     呼叫 `to_inspect_markdown`
  2. Assert: 每次輸出都含 `f"detection_source: {值}"`，且不會因為第三個值而拋出例外
- **Expected**: render 邏輯對任意字串值都能正確顯示，不假設固定的字面值集合
- **現況**: 既有覆蓋 + inspection 驗證（2026-08-12 使用者裁決：不補測試）——
  `markdown_h3`/`markdown_h4` 已被現有測試涵蓋；`"text_fallback"` 的 forward-compat
  以 code inspection 驗證：`_render_item_markdown` 是
  `f"- detection_source: {item.detection_source}"` 直接字串插值，對 `detection_source`
  沒有任何分支，補測試等於在測 f-string 插值本身。它想防的回歸（未來改成 hardcode
  mapping）是臆測性的，且 DEV-136 落地時自己的驗收會立刻撞到

#### S-inspect-06: 摘要表對混合 kind 的 filing 給出一致的欄位配置
- **Method**: script
- **Steps**:
  1. 建構一份 `ParsedFiling`，items 為 `[StructuredItem(item="7", detection_source=
     "markdown_h3", blocks=[...]), FlatItem(item="1a", text="Not applicable.")]`
  2. 呼叫 `to_summary_text(filing)`
  3. Assert: 輸出恰好兩個 item 資料列（不含 header 列），對應 `"7 "` 開頭與 `"1a "` 開頭
  4. Assert: `"1a"` 那一列的 detection_source/prelude/blocks 欄位顯示 `"—"`，`"7"` 那
     一列顯示實際值
- **Expected**: 混合 kind 時欄位一致、缺值有明確 placeholder
- **現況**: 已涵蓋 —— `test_inspect_view.py::TestSummaryText::test_counts_and_rows`；
  `__main__.py` 的 CLI 層也有 `test_main.py::test_default_prints_summary` 佐證整合路徑

#### S-inspect-07: `--verbose` 摘要表不洩漏任何內文
- **Method**: script
- **Steps**:
  1. 沿用 S-inspect-06 的 filing
  2. 呼叫 `to_summary_text(filing)`
  3. Assert: 輸出不含該 StructuredItem 任一 block 的完整內容
  4. Assert: 輸出不含該 FlatItem 的 `text` 內容
- **Expected**: 摘要表符合 AC「不含內文」
- **現況**: 已涵蓋 —— `test_inspect_view.py::test_excludes_body_content`；CLI 層
  `test_main.py::test_default_prints_summary` 也斷言 `FLAT_BODY not in out`

#### S-inspect-08: StructuredItem 的 prelude 與多個 block 串接，保留 heading 當區隔
- **Method**: script
- **Steps**:
  1. 建構 `StructuredItem`，`prelude` 非空，`blocks=[Block(heading="Results of
     Operations", text="...continuing operations."), Block(heading="Liquidity",
     text="Legal proceedings include...")]`
  2. 呼叫 `to_section_text(filing, "7")`
  3. Assert: 輸出含 `prelude`、兩個 block 各自的 heading 與 text
  4. Assert: 輸出**不含** `"...continuing operations.Legal proceedings include..."`
     （兩段內文黏在一起的錯誤形式）
  5. Assert: 輸出不含 `"##"`（無 markdown 標記）
- **Expected**: 多 block 串接有清楚邊界
- **現況**: 已涵蓋 —— `test_inspect_view.py::TestSectionText::test_structured_section_
  keeps_all_content`（內容都出現且無 `##`）+ 新增的
  `test_structured_section_blocks_stay_separated`：兩個 block 的情境下對整段輸出做
  **精確相等**斷言，直接鎖住 `"\n\n"` join 的分隔契約（比否定式反例斷言更強——改成
  `"".join` 或單 `"\n"` 都會失敗）

#### S-inspect-09: `--section` 查詢 FlatItem 時直接輸出原始文字
- **Method**: script
- **Steps**:
  1. 建構 `FlatItem(item="1a", text=<某段完整文字>)`
  2. 呼叫 `to_section_text(filing, "1a")`
  3. Assert: 回傳值等於 `item.text`（完全相等，不多不少）
- **Expected**: FlatItem 分支直接印 text，不誤入 block-join 邏輯
- **現況**: 已涵蓋 —— `test_inspect_view.py::TestSectionText::test_flat_section_is_
  raw_text`；CLI 層 `test_main.py::test_section_prints_plain_text` 也驗證了整合路徑
  （用大寫 `"1A"` 查詢，同時驗證了大小寫不敏感）

#### S-inspect-10: `--section` 的 key 比對大小寫不敏感
- **Method**: script
- **Steps**:
  1. 建構 `FlatItem(item="1a", ...)`
  2. 呼叫 `to_section_text(filing, "1A")` 與 `to_section_text(filing, " 1a ")`
  3. Assert: 兩次回傳值相等，且都等於 `item.text`
- **Expected**: key 比對不分大小寫、忽略前後空白
- **現況**: 已涵蓋 —— `test_inspect_view.py::TestSectionText::test_key_is_case_insensitive`
  （2026-08-13 修正：測試包在 `TestSectionText` class 裡，bdd-e2e-loop Round 1 發現
  原本漏寫 class 名稱，pytest node ID 收不到）

#### S-inspect-11: 查詢一個這份 filing 沒有的 key，列出可用的 key 清單
- **Method**: script（render 層）+ script（CLI 整合層，見下方 CLI 部分）
- **Steps（render 層）**:
  1. 建構一份只有 `items=[item(key="7"), item(key="1a")]` 的 filing
  2. 呼叫 `to_section_text(filing, "99")`
  3. Assert: 拋出 `ValueError`，訊息含 `"available: 7, 1a"`
- **Steps（CLI 整合層）**:
  1. `SEC_TEXT_INSPECT_DIR=$(mktemp -d) python -m backend.ingestion.sec_text_pipeline
     --ticker AAPL --fiscal-year 2024 --section 99`（monkeypatch `parse_filing`
     回傳上述 toy filing，比照 `test_main.py` 現有測試的 patch 方式）
  2. Assert: exit code 為 1
  3. Assert: stderr 含 `"available: 7, 1a"`
  4. Assert: stderr **不含** `"Traceback"`
- **Expected**: render 層拋出的 `ValueError` 被 CLI 邊界正確攔截並轉成 legible failure
- **現況**: 已涵蓋 —— render 層 `test_inspect_view.py::TestSectionText::test_unknown_key_lists_available`；
  CLI 層新增 `test_main.py::test_unknown_section_key_fails_legibly`（exit code 1、
  stderr 含 `"available: 7, 1a"`、無 Traceback），覆蓋 `_run_view` 原本零覆蓋的
  `except ValueError` 分支。這是 `--section` Rule 被指定的 legible-failure case，
  屬 envelope §5 標準之內
  （2026-08-13 修正：render 層測試包在 `TestSectionText` class 裡，同上一條的
  node ID 缺漏）

#### S-inspect-12: 對同一 ticker/fiscal_year 重複執行 `inspect`，覆蓋既有檔案
- **Method**: script（CLI 整合層）
- **Steps**:
  1. 設定 `SEC_TEXT_INSPECT_DIR` 指向一個乾淨的臨時目錄
  2. monkeypatch `parse_filing` 回傳 toy filing A，執行
     `main(["inspect", "--ticker", "NVDA", "--fiscal-year", "2025"])`
  3. 記錄輸出路徑與檔案內容（`(tmp_path / "NVDA" / "10-K" / "2025.md").read_text()`）
  4. 改 monkeypatch `parse_filing` 回傳內容不同的 toy filing B，再次執行同一條指令
  5. Assert: 兩次印出的路徑字串相同
  6. Assert: 該路徑下只有一個檔案（用 `list((tmp_path / "NVDA" / "10-K").iterdir())`
     確認沒有第二個檔案，例如帶時間戳的變體）
  7. Assert: 該檔案內容現在反映的是 filing B 的內容，不是 filing A 的殘留內容
- **Expected**: 同路徑覆寫，不累積多檔
- **現況**: 既有覆蓋（2026-08-12 使用者裁決：不補測試）——
  `test_main.py::test_inspect_writes_file_and_prints_path` 對輸出路徑做**精確相等**
  斷言（`tmp/AAPL/10-K/2024.md`，路徑中無時間戳、無序號），已鎖住「同 ticker/年度
  必然同路徑」；同路徑 `write_text` 覆寫是 pathlib 的語意。要讓本 scenario 失敗
  （檔名變成非確定性），現有測試必先失敗——補「執行兩次」的測試等於在測 stdlib

#### S-inspect-13: 三種輸出模式對 filing header 的顯示行為
- **Method**: script
- **Steps**:
  1. 建構一份帶完整 `FilingMetadata`（ticker/fiscal_year/accession_number/cik/
     primary_document 皆有值）的 filing
  2. 分別呼叫 `to_inspect_markdown(filing)`、`to_summary_text(filing)`、
     `to_section_text(filing, <某個 key>)`
  3. Assert: 前兩者的輸出都含 `metadata.ticker`、`metadata.accession_number`
  4. Assert: 第三者（`to_section_text`）的輸出**不含** `metadata.accession_number`
- **Expected**: header 只出現在需要對照 filing 身份的模式，`--section` 保持純粹
- **現況**: 既有覆蓋（2026-08-12 使用者裁決：不補測試）——
  `to_inspect_markdown` 含 header：`test_inspect_view.py::TestInspectMarkdown::test_metadata_header`
  直接斷言（2026-08-13 修正：node ID 補上 `TestInspectMarkdown` class 名稱）。
  `to_summary_text` 含 header：`test_counts_and_rows` 斷言的 counts 行
  （`"2 items (structured 1 / flat 1)"`）正是 `_header_lines()` 的第三行，
  inclusion 已被執行到。`to_section_text` 不含 header：
  `test_flat_section_is_raw_text`（render 層）與 `test_section_prints_plain_text`
  （CLI 層）都是**精確相等**斷言——這是最強形式的否定斷言，accession/header/任何
  多餘字元都進不來，「否定式斷言完全沒測過」的說法不成立

#### S-inspect-14: 未快取過的 ticker 直接查詢，自動完成 fetch+parse
- **Method**: script（CLI 整合層，用 monkeypatch 模擬 cache miss → 呼叫 `parse_filing`
  這件事本身，不驗證 `parse_filing` 內部的 cache 邏輯——那是 DEV-132 的測試責任）
- **Steps**:
  1. monkeypatch `parse_filing` 為一個 mock，回傳 toy filing
  2. 執行 `main(["--ticker", "MSFT", "--fiscal-year", "2024"])`（不帶 `--force`）
  3. Assert: `parse_filing` 被呼叫一次，參數為 `("MSFT", 2024, False)`
  4. Assert: 沒有任何跡象顯示 operator 需要下額外指令（即整個流程是這單一條指令完成的）
- **Expected**: CLI 直接把 fetch/parse 責任交給 `parse_filing`，本身不做 cache 判斷
- **現況**: 已涵蓋 —— `test_main.py::test_default_prints_summary` 斷言了
  `parse.assert_called_once_with("AAPL", 2024, False)`（等價驗證，換了 ticker 名稱
  而已）

#### S-inspect-15: 預設輸出路徑與環境變數覆寫路徑
- **Method**: script
- **Steps**:
  1. 不設定任何環境變數，`monkeypatch.chdir` 到一個任意臨時目錄（驗證與 cwd 無關）
  2. Assert: `get_sec_text_inspect_dir() == REPO_ROOT / "data" / "sec_text_inspect"`
  3. 設定 `SEC_TEXT_INSPECT_DIR` 環境變數指向另一個臨時目錄
  4. Assert: `get_sec_text_inspect_dir()` 回傳該環境變數指定的路徑
  5. 額外檢查：`grep -n "sec_text_inspect" .gitignore`，確認該路徑被 gitignore 涵蓋
- **Expected**: resolver 正確解析預設與覆寫路徑，且與 cwd 無關
- **現況**: 已涵蓋 —— `test_data_paths.py::test_resolves_repo_root_independent_of_cwd`
  與 `test_env_override_sec_text_inspect_dir`；`.gitignore` 的 `data/sec_text_inspect/`
  規則已在 diff 中確認存在

#### S-inspect-16: 同時給兩個互斥的 mode flag，CLI 立即拒絕
- **Method**: script（CLI 整合層）
- **Steps**:
  1. `python -m backend.ingestion.sec_text_pipeline --ticker AAPL --fiscal-year 2024
     --verbose --section 7` → assert exit code 為 2（argparse 的標準 usage-error
     exit code），assert stderr 含 `"not allowed with argument"` 或等價的
     mutually-exclusive 錯誤訊息
  2. `python -m backend.ingestion.sec_text_pipeline inspect --ticker AAPL
     --fiscal-year 2024 --verbose` → assert exit code 為 2，assert stderr 含
     `"unrecognized arguments"` 或等價訊息
  3. 兩種情況都額外確認：沒有任何網路請求發生（monkeypatch `parse_filing` 為一個
     會直接 raise 的 mock，assert 它從未被呼叫）
- **Expected**: 兩種衝突組合都在參數解析階段被拒絕，不觸發任何 fetch/parse
- **現況**: inspection 驗證（2026-08-12 使用者裁決：不補測試）——
  `--verbose`/`--section` 互斥由 `parser.add_mutually_exclusive_group()` 宣告式設定
  保證；`inspect` 的 parser 未註冊那兩個 flag，argparse 對未知參數原生報 usage error。
  exit code 2 與「parse 失敗即中止、不會走到 `_load_filing`」都是 argparse 的文件化
  行為——runtime 測試測的是 argparse 而非本專案程式碼。這類 flag 衝突排列組合正是
  bdd-scenarios.md Context 聲明「刻意不做窮舉」的範疇；scenario 保留為文件化行為，
  驗證方法為 code inspection

#### S-inspect-17: 已有快取的 ticker 加上 `--force`，略過快取重新 parse
- **Method**: script（CLI 整合層，驗證的是「CLI 正確把 `--force` 轉發為
  `force=True`」，不是 `parse_filing` 內部真的略過快取這件事本身——那屬於 DEV-132
  已驗證的範圍）
- **Steps**:
  1. monkeypatch `parse_filing` 回傳 toy filing
  2. 執行 `main(["inspect", "--ticker", "NVDA", "--fiscal-year", "2025", "--force"])`
  3. Assert: `parse_filing` 被呼叫時第三個參數（`force`）為 `True`
- **Expected**: `--force` flag 正確轉發到 `parse_filing(ticker, fiscal_year, force=True)`
- **現況**: 已涵蓋 —— `test_main.py::test_inspect_writes_file_and_prints_path` 本身就
  帶了 `--force`，並斷言 `parse.assert_called_once_with("AAPL", 2024, True)`；三個
  entry point（default/`--section`/`inspect`）共用同一個 `_make_parser()`，`--force`
  是共同定義的參數，其餘兩個入口沒有專門測試但屬於同一條程式路徑

#### S-inspect-18: Filing 全部 section 皆空或 stub，CLI 印出含 ticker/年度/accession 的清楚錯誤
- **Method**: script（CLI 整合層）
- **Steps**:
  1. monkeypatch `parse_filing` 直接 raise
     `EmptyFilingError("Parsed 0 substantive items for ZZZZ FY2020 (accession
     0000000000-20-000000); refusing to cache an empty filing.")`
  2. 執行 `main(["--ticker", "ZZZZ", "--fiscal-year", "2020"])`
  3. Assert: `SystemExit` 且 exit code 為 1
  4. Assert: stderr 同時含 `"ZZZZ"`、`"2020"`、`"0000000000-20-000000"` 三項資訊
  5. Assert: stderr 含 `"EmptyFilingError"`（例外類型名稱，來自 `_load_filing` 的
     `f"{type(exc).__name__}: {exc}"` 格式）
- **Expected**: operator 能從錯誤訊息直接看到是哪份 filing 出問題
- **現況**: 既有覆蓋（2026-08-12 使用者裁決：不補測試）——「訊息含 ticker/年度/
  accession 三值」的實質保證已在訊息被**建構**的那一層測過：
  `test_parser.py:216-218` 明文斷言三值都在（`assert "AAPL" in str(excinfo.value)`
  等三條）。CLI 層剩下的只有「`FinLabError` 子類會被 `except (FinLabError,
  ValueError)` 接住」——與已測的 `ValueError` 走同一段 handler，測第二個 tuple 成員
  等於在測 Python 的 except 語意。且提議的測法（monkeypatch 手寫訊息的 exception
  再斷言 stderr 含三值）是循環的：證明的只是自己 mock 的字串會被 print 出來

#### S-inspect-19: 格式不正確的 ticker，CLI 印出清楚訊息而非洩漏 traceback
- **Method**: script（CLI 整合層）
- **Steps**:
  1. 執行 `main(["--ticker", "../BAD", "--fiscal-year", "2024"])`（不需要 monkeypatch，
     ticker 格式驗證發生在真正呼叫 EDGAR 之前）
  2. Assert: `SystemExit` 且 `.code == 1`
  3. Assert: stderr 含 `"Invalid ticker"`
  4. Assert: stderr **不含** `"Traceback"`
- **Expected**: 格式錯誤在 CLI 邊界被攔下，不洩漏原始例外堆疊
- **現況**: 已涵蓋 —— `test_main.py::test_malformed_ticker_fails_legibly`（逐字對應）

---

### Journey Scenarios（Deterministic）

#### J-inspect-01: 首次對未快取的 ticker 執行完整 inspect，並對照 SEC 原文核對
- **Method**: script（真實 EDGAR fetch，非 toy fixture —— Journey 場景需要真的走一次
  cache-miss → fetch → parse → render 的完整彈道）
- **Steps**:
  1. 確認 filing store 與 inspect 輸出目錄裡都沒有 AAPL FY2024 的殘留檔案（若有，先手動
     刪除，模擬「從未查過」的狀態）
  2. `time python -m backend.ingestion.sec_text_pipeline inspect --ticker AAPL
     --fiscal-year 2024`，記錄執行時間（應包含明顯的網路等待）與印出的檔案路徑
  3. `cat <印出的路徑>`，人工核對輸出內容：
     - 每個 Item 是否都依 render 規則正確攤開（StructuredItem 三要素、FlatItem 兩要素）
     - 挑 2-3 個 Item，對照 [SEC EDGAR 原文](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&company=apple)
       確認 detection_source 與 prelude 判定合理
  4. Assert（腳本層可自動化的部分）：印出的路徑存在、檔案非空、檔案開頭符合
     `f"# AAPL 10-K FY2024"` 格式
  5. 人工核對的部分（步驟 3）記錄在 Manual Verification 的 User Acceptance Test
- **Expected**: 完整彈道走通，operator 能拿著檔案內容對照 SEC 原文
- **現況（2026-08-13，bdd-e2e-loop Round 1 執行紀錄）**: 原本指定 MSFT FY2024，Round 1
  真的跑了一次，結果必然是 `EmptyFilingError`——edgartools 5.17.1 對 MSFT/GE/DIS 回傳
  spaced section 名，`Section.item = None`，`parser.py::_parse_items` 因此 skip 全部
  24 個 section。**這不是 inspect CLI 的 bug**：legible failure 彈道本身運作正常，正是
  DEV-127 Known Limitation #3 定義的行為（「上游邊界，不在我們 detection 可修範圍 →
  ParsedFiling 缺項 + legible failure」）。修復已在 DEV-136 branch 進行中（`.item` 缺時
  從 section name 推導 key，含 regression tests，尚未 merge）；upstream 根治見 DEV-147。
  使用者裁決：**DEV-136 merge 前，本 Journey 改用 AAPL FY2024**（未快取過，保留
  cache-miss 語意；`.item` 欄位在 Round 1 的診斷腳本裡已確認能正確填值）。DEV-136
  merge 後可回頭用 MSFT 補跑，一併驗證 `text_fallback` 的 detection_source 顯示
  （S-inspect-05 的真實資料版本）

#### J-inspect-02: Operator 標準抽查工作流程——先 `--verbose` 掃視，再 `--section` 深入
- **Method**: script（真實 filing——bdd-e2e-loop Round 1 已用 AAPL FY2025 實際跑過一次）
- **Steps**:
  1. 對 AAPL FY2025（Round 1 確認已快取、有至少一個 Item 的 prelude 判定是
     「reclassified」，若該快取被清除則重新 inspect 一次即可）
  2. `python -m backend.ingestion.sec_text_pipeline --ticker AAPL --fiscal-year 2025
     --verbose`，掃視輸出，找到 prelude 欄位顯示 `"reclassified"` 的那一列，記下該列
     的 item key
  3. `python -m backend.ingestion.sec_text_pipeline --ticker AAPL --fiscal-year 2025
     --section <上一步記下的 key>`
  4. Assert: 兩次呼叫使用同一組 `--ticker`/`--fiscal-year`，且兩次回傳的 filing 內容
     一致（同一份 filing store JSON）
  5. Assert: `--section` 的輸出裡能看到該 item 原本被判定為 reclassified 的那個
     block 的完整原始內容（沒有 heading，因為 reclassified block 本來就沒有標題），
     且不含 `"##"`
- **Expected**: 兩個 CLI 入口銜接起來構成一次完整的抽查流程，資料一致
- **現況（2026-08-13，bdd-e2e-loop Round 1 執行紀錄）**: 原本指定 MSFT FY2024（沿用
  J-inspect-01），Round 1 因 J-inspect-01 的 MSFT 已知限制（見上方）連第一步都無法執行。
  Round 1 改用已快取的真實 AAPL FY2025 跑過整條流程：`--verbose` 印出 17 列摘要表，
  含兩個 reclassified 判定的 Item（`8`、`1a`）；`--section 8` 印出 62,190 bytes 純文字、
  zero 個 `"##"`。**流程本身已用真實資料驗證過**，本 scenario 正式改指定 AAPL FY2025
  取代原本的 MSFT FY2024 / 待定 NVDA FY2025

---

## Manual Verification

### User Acceptance Test

> 這是本 Feature 存在的核心理由——operator（也就是使用者本人）能不能真的靠這個工具完成
> 「detection 判定的人工抽查」。以下驗收問題應該在真正拿一份新 ticker 跑過 J-inspect-01
> 之後回答。

#### J-inspect-01: 首次對未快取的 ticker 執行完整 inspect，並對照 SEC 原文核對
- **Acceptance Question**: 打開 inspect 輸出的 markdown 檔案，能不能在不用回頭看程式碼的
  情況下，只憑輸出內容就判斷「這個 Item 的 detection 有沒有可能誤判」？
- **Steps**:
  1. 對一個平常沒特別關注過的 ticker 執行 `inspect`
  2. 打開輸出檔案，挑一個 prelude 判定是 valid 的 Item，讀一下附的 chars 數是否符合直覺
     （太大或太小都可能代表 detection 出了問題）
  3. 挑一個 detection_source 是 `markdown_h4`（非最常見的 `markdown_h3`）的 Item，
     打開 SEC 原文，確認這個 Item 的 markdown 結構是不是真的比較不規則、需要降級到 H4
  4. 用 `--section` 深入看一個具體 Item，確認純文字輸出讀起來順暢，沒有奇怪的斷行或
     黏在一起的內文
- **Expected**: 整個核對流程順暢，不需要額外查程式碼或猜測輸出格式的含義

#### S-inspect-04: 長文字 FlatItem 的 preview 截斷（實作落地後再驗收）
- **Acceptance Question**: FlatItem 的 preview 截斷長度，實際看起來是「夠用來判斷這個
  Item 大概在講什麼」，還是太短導致還要另外用別的方式看完整內容？
- **Steps**:
  1. 待 S-inspect-04 實作完成後，找一個 FlatItem 內容較長的真實 filing
  2. 執行 `inspect`，檢視該 FlatItem 的 preview 顯示
  3. 判斷這個長度是否符合實際抽查需求
- **Expected**: preview 長度是實作階段的技術決定，但最終應該通過這個人工檢視——如果太短
  導致完全看不出內容重點，應該回頭調整截斷長度，不需要重新走一次 behavior-validation-plan
