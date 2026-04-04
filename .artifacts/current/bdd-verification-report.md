# BDD Verification Report

## Meta
- Date: 2026-04-04
- Scenarios: `.artifacts/current/bdd-scenarios.md`
- Verification Plan: `.artifacts/current/verification-plan.md`
- Execution Mode: Docker Sandbox (Stage 1) + Host Manual (Stage 2)

---

## Part 1: 測試紀錄與修復過程

### Scenario 進展矩陣

僅列出**曾經失敗過**的 scenario。首輪即通過且從未回歸的 scenario 不列入。

| Scenario | 類型 | Round 1 | Round 2 | Final |
|----------|------|---------|---------|-------|
| S-dl-06 | Deterministic | FAIL | PASS | PASS |

> 標記說明: PASS = 通過, FAIL = 失敗, ERROR = 執行錯誤, SKIP = 該輪未執行, REGRESS = 前輪通過但本輪失敗

**始終通過:** 25 個 automated scenario 在所有輪次中均通過，未列入上表。

### 修復歷程

#### Round 1: Full Suite

**驗證結果:** 25 pass / 1 fail / 0 error

**失敗 Scenarios:**

| Scenario | 預期 | 實際 | 分類 |
|----------|------|------|------|
| S-dl-06: Lowercase/uppercase tickers produce identical results | `Path("data/sec_filings/nvda").exists()` 回傳 False（無 duplicate directory） | `Path.exists()` 回傳 True — macOS 掛載的 volume 是 case-insensitive | Test Bug（非 Implementation Bug） |

**Fixer 修復:**

| Scenario | Root Cause | 修復方式 | 變更檔案 |
|----------|-----------|---------|---------|
| S-dl-06 | Docker container 掛載的 `/workspace` 來自 macOS host，filesystem 是 case-insensitive。`Path("data/sec_filings/nvda").exists()` 因為和 `NVDA` 是同一個目錄而回傳 True，造成 test assertion false positive。Production code 行為正確（ticker 已 normalize 為 uppercase，沒有 duplicate directory）。 | 改用 `os.listdir()` 檢查實際目錄名稱列表，而非 `Path.exists()`，以正確在 case-insensitive filesystem 上驗證無 duplicate directory。 | `.artifacts/current/temp/bdd_test_runner.py` |

**回歸觀察:** 無。Round 2 full regression check 全部 26 個 automated scenario 通過。

---

## Part 2: 最終狀態

### Automated Scenarios

| Scenario | Status | 首次通過輪次 | 修復摘要 |
|----------|--------|------------|---------|
| S-dl-06: Lowercase/uppercase tickers produce identical results | PASS | Round 2 | Round 2 修正 test assertion 以使用 `os.listdir()` 取代 `Path.exists()` — production code 本身正確 |

**始終通過:** 25 個 scenario 在所有輪次中均通過。

完整 automated scenario 列表（26 個全部 PASS）：
- **Feature: SEC Filing Download & Caching**: S-dl-01, S-dl-02, S-dl-03, S-dl-04, S-dl-05, S-dl-06, S-dl-07, S-dl-08, J-dl-01, J-dl-02, J-dl-03
- **Feature: HTML Preprocessing**: S-prep-01, S-prep-02, S-prep-03, J-prep-01
- **Feature: Markdown Conversion & Output Quality**: S-conv-01, S-conv-02, S-conv-03, S-conv-04, J-conv-01
- **Feature: Filing Store & Output Contract**: S-store-01, S-store-02, S-store-03, S-store-04, S-store-05, J-store-01

### Manual Behavior Test

> 因技術限制需要人工輔助的 behavior verification。Manual Round 1-2 因 test instructions 錯誤（missing factory method、missing `EDGAR_IDENTITY`）而失敗，非 implementation bug。Round 3 修正 instructions 後執行。

#### S-dl-07-manual: Overlapping writes to same filing produce a complete, valid file (real SEC calls)
- **結果**: Pass
- **User 回饋**: Store verification 成功（`store.get()` 回傳有效 ParsedFiling）。YAML frontmatter 包含完整 10 個 fields。Markdown body 內容完整。User 注意到 markdown body 開頭有額外一段 `---\ntitle: aapl-20250927\n---`，這是 html-to-markdown (Rust) converter 從 HTML `<title>` tag 自動產生的 title block — 不是 concurrent write 造成的 corruption，是 converter 正常行為（Docker sandbox 用 markdownify fallback 所以沒有此段）。
- **備註**: 此 converter title block 屬 output 品質細節，可在後續迭代考慮是否 strip。不影響 concurrent write safety 的驗證結論。

#### S-dl-05-manual: Invalid inputs produce distinct, actionable errors (real SEC calls)
- **結果**: Pass
- **User 回饋**: 兩個 error 確實 distinct：
  - `DEFINITELYNOTAREALTICKER12345` → `TickerNotFoundError: Ticker not found: DEFINITELYNOTAREALTICKER12345`
  - `TSM` → `FilingNotFoundError: No 10-K filing found for TSM`
- **備註**: Traceback 是 Python 未捕捉 exception 的正常輸出。在 production 中 caller（agent tool / batch script）會 catch 這些 exception 並取得結構化的 error class 和 message。

### User Acceptance Test

> 待 PR review 時由 User 執行的產品驗收

#### J-conv-01-uat: Full pipeline output quality check
- **狀態**: Pending — 待 PR review 驗收
- **驗收問題**: Does the parsed Markdown faithfully represent the 10-K filing content in a RAG-friendly format?
- **驗證步驟**: Process 3-5 real tickers (NVDA, AAPL, MSFT), open `.md` files in Markdown viewer, verify heading hierarchy, financial tables readability, no residual HTML/XBRL, correct frontmatter, compare html-to-markdown vs markdownify output.
- **預期結果**: Clean, structured Markdown that a human can read and a MarkdownNodeParser can chunk into meaningful sections.

#### S-prep-03-uat: Older filing preprocessing quality
- **狀態**: Pending — 待 PR review 驗收
- **驗收問題**: Does the pipeline handle older SEC filings (pre-2015) without destroying content?
- **驗證步驟**: Process 2-3 older filings (e.g., AAPL FY2010, GE FY2008), inspect `.md` files for content preservation and heading structure.
- **預期結果**: Content preserved for older filings; heading detection is best-effort for pre-semantic-HTML filings.

### Summary

| 指標 | 值 |
|------|-----|
| Automated Scenarios | 26 |
| Manual Behavior Test Scenarios | 2 |
| User Acceptance Test Scenarios | 2 |
| Automated 通過 | 26 / 26 |
| Manual 通過 | 2 / 2 |
| Automated 輪數 | 2 / 5 |
| Manual 觸發的 Re-verification 輪數 | 0 / 3 |
| Fix Rounds | 1 |
| 升級為 Design Issue | 0 |

### 最終狀態: 全部通過

---

## 未解決的問題

所有 scenarios 均已通過。

**觀察紀錄（非 blocking）:**
1. **html-to-markdown converter title block**: Rust 版 converter 會在 Markdown body 開頭插入 `---\ntitle: ...\n---` block（來自 HTML `<title>` tag）。markdownify fallback 不會。可考慮在 converter output 後 strip 此段以保持一致性。
2. **`EDGAR_IDENTITY` 環境變數**: Pipeline 需要 `EDGAR_IDENTITY` 環境變數才能呼叫 SEC API。目前在 `SECDownloader.__init__()` 中從 env var 讀取，但沒有在缺少時 raise 明確錯誤 — 而是讓 edgartools 在第一次 HTTP request 時才 raise `IdentityNotSetException`。可考慮在 constructor 中 early fail。
