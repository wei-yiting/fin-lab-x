# DEV-134 Inspect View + CLI — 尚待補齊的實作與測試

> **✅ 已結案（2026-08-12 使用者裁決）**：本清單經逐項覆核後 3 收 6 駁——
> **A1**（FlatItem preview 截斷，上限 500）、**B2**（block 分隔的精確相等斷言）、
> **B3**（`--section` 不存在 key 的 CLI 層測試）已實作；**B1/B4/B5/B6/B7/B8** 裁決為
> 「既有覆蓋 / inspection 驗證」不補（B5、B7 的現況描述有事實錯誤：精確相等斷言已存在、
> `test_parser.py:216-218` 已測三值訊息）。逐項理由見 `verification-plan.md` 各
> scenario 的現況欄。本文件保留作紀錄，不再是待辦清單。

> 交接用文件，給接手的 coding agent。完整脈絡見同目錄的 `bdd-scenarios.md`
> （behavior 定義）與 `verification-plan.md`（每條 scenario 的驗證方法與現況）。
> 本文件只列「還沒做完」的部分，已經涵蓋的不重複列出。
>
> 分支：`feat/sec-filing-inspect-cli`。相關檔案：
> `backend/ingestion/sec_text_pipeline/inspect_view.py`、`__main__.py`，測試在
> `backend/tests/ingestion/sec_text_pipeline/test_inspect_view.py`、`test_main.py`。

---

## A. 需要實作（不只是補測試）

### A1. FlatItem 的 preview 截斷邏輯

- **對應 scenario**: `S-inspect-04`（`bdd-scenarios.md`）
- **現況**: `inspect_view.py` 的 `_render_item_markdown()` 對 FlatItem 目前直接印出
  完整 `item.text`，沒有任何截斷邏輯
- **目標行為**: FlatItem 在 `to_inspect_markdown()` 的輸出裡，顯示完整字數（不受截斷
  影響）+ 一段有長度上限的 preview（超過上限就截斷並加上截斷標記，如 `"…"`）
- **需要決定的實作細節**: 截斷長度上限的具體數字（design 沒有指定，implementation
  階段自行決定一個合理值，例如 200 字元）
- **這是既有 AC 的釐清，不是新範圍**——見本次對話裡對 `S-inspect-04` 由來的說明，
  必要時可比照 DEV-134「Review 裁決紀錄」SP-1.1 的處置模式，把 Linear 描述裡
  「字數（或 preview）」那句話也一併改清楚
- **驗收**: 補 `test_inspect_view.py` 的測試——短文字（低於上限）完整顯示不截斷、
  長文字在上限處截斷並保留完整字數統計、截斷點之後的原文不出現在輸出裡

---

## B. 只需要補測試（實作已經正確，缺的是鎖定行為的測試）

### B1. `detection_source` 的第三個值（forward-compat）沒有 regression test

- **對應 scenario**: `S-inspect-05`
- **現況**: `_render_item_markdown()` 是 `f"- detection_source: {item.detection_source}"`
  直接字串插值，沒有 if/elif 分支限制字面值——實作形狀本身就是對的，只是沒有測試
  明確鎖定「未來 DEV-136 補上 `text_fallback` 值時，render 不會漏顯示或報錯」這件事
- **需要補的測試**: `test_inspect_view.py` 加一個 fixture，`detection_source` 設為
  `"text_fallback"`（toy 值，不代表真的接了 DEV-136），assert 輸出正確顯示

### B2. `--section` 多 block 串接沒有「不會黏在一起」的反例斷言

- **對應 scenario**: `S-inspect-08`
- **現況**: `test_structured_section_keeps_all_content` 斷言了 prelude/heading/block
  text 都出現，但沒有斷言「兩段不同 block 的內文不會連在一起」這個否定形式
- **需要補的測試**: 加一個 assert，確認輸出裡不會出現前一個 block 結尾直接接到
  下一個 block 開頭的字串（例如 `assert "...continuing operations.Legal proceedings"
  not in text`）

### B3. `--section` 查不存在的 key，CLI 整合層沒有測試

- **對應 scenario**: `S-inspect-11`
- **現況**: `to_section_text()` 拋出的 `ValueError`（render 層）已經測過
  （`test_unknown_key_lists_available`）；`__main__.py._run_view()` 確實有
  `except ValueError as exc: print(str(exc), file=sys.stderr); raise SystemExit(1)`
  這段程式碼攔截它，但 `test_main.py` 沒有任何測試走到這條路徑
- **需要補的測試**: `test_main.py` 加一個測試，monkeypatch `parse_filing` 回傳一份
  只有部分 key 的 toy filing，執行 `--section 99`（不存在的 key），assert exit code
  為 1、stderr 含 `"available: ..."`、不含 `"Traceback"`

### B4. 重複執行 `inspect` 是否覆蓋，沒有顯式測試

- **對應 scenario**: `S-inspect-12`
- **現況**: 現在的行為（用 `write_text` 直接覆寫）是「覆蓋」沒錯，但這只是實作剛好
  用了會覆蓋的寫法，沒有一條測試明確鎖定「重複執行同一個 ticker/年度不會累積出第二個
  檔案」這個行為本身
- **需要補的測試**: `test_main.py` 加一個測試，對同一組 `--ticker`/`--fiscal-year`
  執行兩次 `inspect`（兩次 monkeypatch 不同內容的 toy filing），assert 兩次印出的
  路徑相同、該路徑下只有一個檔案、檔案內容是第二次執行的結果

### B5. Filing header 只在 verbose/inspect 出現、`--section` 不出現，沒有顯式測試

- **對應 scenario**: `S-inspect-13`
- **現況**: `to_inspect_markdown()` 含 header 已測過（`test_metadata_header`）；
  `to_summary_text()` 也呼叫了 `_header_lines()`（讀 code 確認），但沒有專門測試；
  `to_section_text()` 不含 header 這個否定式斷言完全沒測過
- **需要補的測試**: `test_inspect_view.py` 補兩條——`to_summary_text()` 輸出含
  ticker/accession_number；`to_section_text()` 輸出不含 accession_number

### B6. Mode flag 互斥（`--verbose`+`--section`、`inspect`+`--verbose`）沒有測試

- **對應 scenario**: `S-inspect-16`
- **現況**: 機制上應該是對的——`--verbose`/`--section` 用
  `parser.add_mutually_exclusive_group()` 宣告，`inspect` 的 subparser 沒有註冊
  `--verbose`/`--section`，argparse 原生機制會處理這兩種衝突——但完全沒有測試驗證
  實際的 exit code、錯誤訊息，或「沒有觸發任何 fetch/parse」這個副作用層面的斷言
- **需要補的測試**: `test_main.py` 加兩條——`main(["--ticker", "X", "--fiscal-year",
  "2024", "--verbose", "--section", "7"])` 與
  `main(["inspect", "--ticker", "X", "--fiscal-year", "2024", "--verbose"])`，各自
  assert `SystemExit` 且 code 為 2，並且用一個會直接 raise 的 mock 取代
  `parse_filing`，assert 它從未被呼叫過

### B7. `EmptyFilingError` 在 CLI 層的訊息沒有測試

- **對應 scenario**: `S-inspect-18`
- **現況**: `_load_filing()` 的 `except (FinLabError, ValueError)` 分支目前只被
  `test_malformed_ticker_fails_legibly`（走 `ValueError` 那條路）驗證過。
  `EmptyFilingError` 是 `FinLabError` 的子類別，走同一段程式碼，但沒有專門測試
- **需要補的測試**: `test_main.py` 加一條，monkeypatch `parse_filing` 直接
  `raise EmptyFilingError("Parsed 0 substantive items for ZZZZ FY2020 (accession
  0000000000-20-000000); refusing to cache an empty filing.")`，assert exit code
  為 1，stderr 同時含 ticker、年度、accession 三個值，以及 `"EmptyFilingError"`
  這個例外類型名稱

### B8. J-inspect-02（verbose → section 銜接工作流程）完全沒有對應測試

- **對應 scenario**: `J-inspect-02`
- **現況**: 這是本輪新增的 Journey，強調「三個 CLI 入口其實是同一套工作流程」——
  現有測試都是各自獨立驗證單一 entry point，沒有測試涵蓋「同一個 ticker 先
  `--verbose` 掃視、再用 `--section` 深入某個 Item」這種跨兩次 invocation 的銜接
  情境
- **需要補的測試**: 建一個 toy filing，其中一個 Item 是 reclassified 狀態；先執行
  `--verbose` 確認能在摘要表裡找到該 Item 的 reclassified 判定，再執行
  `--section <該 item 的 key>`，assert 輸出含該 block 的完整原始內容（沒有 heading，
  因為 reclassified block 本來就沒有標題）

---

## C. 非程式碼——需要人工跑一次真實驗證（不是 coding agent 能做的）

### C1. J-inspect-01 的真實 smoke test 沒有針對本次 verification plan 記錄下來

- **對應 scenario**: `J-inspect-01`
- **現況**: `code-review-improvement-report.md` 提到其他 session 已經對 AAPL FY2025
  做過三入口 + cache hit/miss + 錯誤路徑的人工驗證，但那份紀錄不在這份 verification
  plan 的追蹤範圍內，而且用的 ticker 跟本次 Journey 指定的 MSFT 不同
- **建議動作**: 找一個尚未 inspect 過的真實 ticker（不一定要是 MSFT），實際跑一次
  `inspect` 全流程，人工對照 SEC EDGAR 原文核對輸出內容，把結果記錄下來（例如記在
  這份文件或 Linear comment 裡）
