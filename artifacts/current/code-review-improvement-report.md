# Code Review Improvement Report

> **Task:** DEV-132 — sec_text_pipeline 骨架(ParsedFiling schema + stub v2 + FlatItem parse + JSON filing store)
> **Date:** 2026-08-06
> **Rounds:** 4(3 輪全幅 + 1 輪 targeted confirm)
> **Reviewer model:** Codex `gpt-5.6-sol`(quality 軸 + spec 軸,read-only)
> **Fixer model:** Claude Fable 5(isolated subagents;兩處 reviewer-specified 微修由 orchestrator 執行)

## 架構影響摘要

- **`sec_core` 新增 public 入口 `fetch_filing_bundle` + `FetchedFiling` dataclass**:citation metadata(`accession_number` / `cik` / `company_name` / `primary_document`)在 fetch 時從 edgartools public `Filing` API 捕捉,`tenk._filing` 私有存取消失。內部 fetch 拆成 locate / obj 兩層 cache;**legacy `fetch_filing_obj` 的可觀察行為(含網路呼叫序列)保持原樣**,有 regression test 鎖住。
- **`parse_filing` contract 定案**:`(ticker, fiscal_year: int, force=False, *, store=None)` — `fiscal_year` 必填(latest-year 解析延後至有 consumer 的票)、`store=` keyword-only 測試 seam、零 item 時拋 `EmptyFilingError` 且不落地(committed-or-absent)。
- **Section bleed trim 落地並收斂**:stub 判定前先切 Item 邊界;boundary 判定為 structural-only(行首 / 字串開頭 / 非字母黏接 / `PART <roman>` 字母黏接例外),inline cross-reference 與字內 `Item` 一律保留。
- **AGENTS.md §4 新增「Ingestion Rewrite Coexistence (temporary until sunset)」**:凍結 baseline、sec_core only-add、schema 凍結例外三規則的權威落點;sunset 票(DEV-139)已註記屆時整段刪除。

## Summary

| 指標 | 數值 |
| --- | --- |
| 總輪數 | 4 |
| 發現 issues 總數 | 20(quality 16 + spec 4) |
| Blocking | 0/0 |
| Major(quality) | 8/11 fixed、2 declined by ruling(M-1.2、M-1.5)、1 resolved via AGENTS.md(M-2.4) |
| Minor(quality) | 5/5 fixed |
| Spec findings (SP-) | 2/4 fixed(SP-1.2、SP-1.3)、2 declined by ruling(SP-1.1、SP-2.1) |
| 文件修正 | README 新增、docstring 決策編號全清、AGENTS.md 段落、force 語意文件化 |

## Spec Conformance(Spec 軸)

| ID | 類型 | Spec 依據 | 結果 |
| --- | --- | --- | --- |
| SP-1.1 | Misimplemented | "parse_filing(ticker, year, force)" | declined — `fiscal_year` 為 repo 慣例(裁決記錄於 issue description) |
| SP-1.2 | Misimplemented | "stub items 在 parse 階段直接 drop" | fixed — boundary trim 先於 stub 判定(= M-1.1) |
| SP-1.3 | Scope creep | "單一 public method parse_filing(ticker, year, force)" | fixed — latest-year 模式移除;`store=` 依裁決保留為 keyword-only seam |
| SP-2.1 | Scope creep | "parse_filing(ticker, year, force) -> ParsedFiling" | declined — `EmptyFilingError` 依 envelope §2 legible-failure 裁決納入 contract(記錄於 issue description) |

Round 3 spec 軸:**0 findings,12 項需求全數確認**。

## Reading Guide

| 順序 | 檔案 | 在本次變更中的角色 | 風險 |
| --- | --- | --- | --- |
| 1 | `backend/ingestion/sec_text_pipeline/filing_models.py` | 凍結的 ParsedFiling schema contract(union、blocks≥1、detection_source、citation 欄位、extra="forbid") | ⚠️ |
| 2 | `backend/common/sec_core.py` | 參數化 stub helper + fetch 拆層(locate/obj/bundle)+ 新 public `fetch_filing_bundle`;既有 API 行為凍結 | ⚠️ |
| 3 | `backend/ingestion/sec_text_pipeline/stub_detection.py` | v2 pseudo-stub patterns(remove-then-measure 機制掛載) | |
| 4 | `backend/ingestion/sec_text_pipeline/parser.py` | parse_filing 主流程 + structural boundary trim + EmptyFilingError | |
| 5 | `backend/ingestion/sec_text_pipeline/filing_store.py` | JSON store(atomic write、ticker validation) | |
| 6 | `AGENTS.md` | 共存契約段落(temporary until sunset) | ⚠️ |
| 7 | `backend/ingestion/sec_text_pipeline/README.md` + `__init__.py` | package 導覽 + public surface | |
| 8 | `backend/tests/ingestion/sec_text_pipeline/`(conftest + fixture + 4 test files) | Seam-1 tests,AAPL FY2025 錄製 fixture | |
| 9 | `backend/tests/common/`(conftest + test_sec_core) | sec_core 等價性 / bundle / document-access regression tests | |

## 所有修正問題詳解

### M-1.1 / SP-1.2(Major)— Section bleed 讓 stub 逃過 drop
- **問題:** `section.text()` 未切 Item 邊界就做 stub 判定。AAPL FY2025 Item 11 本體是純 incorp stub,但 edgartools 把 Items 12–15 黏進其 body,灌高 remaining-content 讓它逃過判定,並把外來 item 內文一起存進 FlatItem(citation 會標錯章節)。
- **修法:** `_parse_items` 在 stub 判定前先 `_trim_section_text` 切到自身邊界。
- **影響:** stub drop 恢復正確;FlatItem 不再攜帶外來 item 內文。
- **驗證:** fixture regression(Item 11 drop、9C 無 "Item 10.")+ 真實 AAPL 實跑(17 items,10/11/12/13 全 drop)。

### SP-2.1(quality 軸,Major)→ X-3.1(Major)— trim 的兩輪 false-positive 收斂
- **問題:** 第一版 trim 把任何位置的外來 `Item N.` 當邊界 — inline cross-reference("...under Item 1A. Risk Factors...")會截斷正文(round 2 抓到);改 structural 判定後,字內 `Item`(`SubItem 1.`)的前導字母仍被當黏接邊界(round 3 抓到)。
- **修法:** boundary = 行首 / 字串開頭 / 非字母黏接(`reference.Item 12.`、`53PART IVItem 15.`);字母黏接僅限前綴以 `PART <roman>` 結尾;`ITEM` ALL-CAPS heading 變體納入、小寫排除。
- **影響:** 消除靜默內文刪除(envelope §2 紅線),同時保住全部觀察到的 bleed 裁切。
- **驗證:** round 4 targeted confirm — 14 案例 assertion matrix 全過;`TestTrimSectionText` 5 個 regression tests;真實 AAPL substantive items 長度位元不變。

### M-1.2(Major)— declined by ruling(行為不動)
- **問題:** reviewer 認為 `force=True` 應重打 EDGAR,實際只繞過 filing store(fetch 有 in-process lru)。
- **裁決:** `force` 的語意就是「重 parse 同一份 immutable filing」— filing 每 (ticker, year) 不變,修正版是獨立 10-K/A。docstring 已文件化;測試改名 `test_force_bypasses_store_and_reparses` 並驗證 store 被略過、新結果覆寫(m-2.2)。

### M-1.3(Major)— `tenk._filing` 私有屬性依賴
- **問題:** citation metadata 從 edgartools 私有屬性挖,升級可無預警斷裂。
- **修法:** `sec_core.fetch_filing_bundle`(only-add)在 fetch 流程中、`filing.obj()` 之前從 public `Filing` API 捕捉四欄位;parser 改吃 bundle。
- **影響:** 邊界上只用 documented API;`fetch_filing_obj` 對既有 caller 位元不變。
- **驗證:** `test_fetch_filing_bundle_carries_metadata_and_same_tenk` + document-access regression(見 M-2.1)。

### M-1.4(Major)— 空 parse 被靜默 cache 成成功
- **問題:** `items=[]` 直接落地並回傳,下游看到的是「成功但查無內容」,cache 還會固化這個錯誤。
- **修法:** `EmptyFilingError(SECError)`(帶 ticker/年度/accession)在 save 前拋出,不落地。
- **影響:** envelope §2「committed or absent / legible failure」成立。
- **驗證:** `test_all_sections_empty_or_stub_raises_and_saves_nothing`。

### M-1.5(Major)— declined by ruling(schema 凍結維持)
- **問題:** `StructuredItem` 分支無 production producer,違反 envelope §0 reachability。
- **裁決:** schema 一次凍結是本票明文交付物(後續 tickets 對穩定契約開發);例外記錄於 AGENTS.md 共存段落與 issue description。

### M-2.1(Major)— bundle refactor 改變 frozen `fetch_filing_obj` 行為
- **問題:** 第一版 bundle 讓所有 legacy fetch 都多一次 `filing.document` SGML/homepage 網路呼叫 — 簽名沒變但 observable behavior 變了。
- **修法:** 拆出 `_locate_filing_cached`;`_fetch_filing_obj_cached` = locate + `filing.obj()`(原始行為);只有 bundle path 讀 metadata。
- **影響:** frozen baseline 的網路行為復原。
- **驗證:** `_InstrumentedDocFiling` regression — `fetch_filing_obj` 從不觸碰 `filing.document`;bundle 恰讀一次;兩入口共用一次 `edgar.Company`。

### M-2.2(Major)— metadata 讀取洩漏 raw exception
- **問題:** `filing.document` 是網路呼叫,429/5xx 未映射為 `SECError` family。
- **修法:** metadata 讀取包進 `_classify_edgar_error`;缺 primary document → `SECError` 帶 ticker+accession。
- **驗證:** 429→`RateLimitError`(retry_after 保留)、503→`TransientError`、missing→`SECError` 三測試。

### M-2.3(Major)— ticker path traversal
- **問題:** `^[A-Z0-9.\-]+$` 接受 `"."`/`".."`,路徑可跳出 base_dir。
- **修法:** `^[A-Z0-9][A-Z0-9.\-]*$`(舊 store 凍結不動)。
- **驗證:** `"."`/`".."`/`"..."`/`".AAPL"`/`"-AAPL"` 拒絕、`BRK.B` 通過。

### M-2.4(Major)— resolved via AGENTS.md(ADR declined)
- **問題:** 共存契約(凍結 baseline / only-add / schema 例外)無 repo 內權威落點,reviewer 連兩輪重新舉報已裁決事項。
- **裁決與修法:** 共存是 time-boxed → 不立 ADR;AGENTS.md §4 新增六行段落(每個 agent session 自動載入);DEV-139 sunset 票註記屆時刪除。

### m-1.1 / m-1.2 / m-1.3 / m-2.1 / m-2.2(Minor,全修)
- `extra="forbid"` 全 model + 未知欄位測試;corrupt-JSON 斷言收窄為 `pydantic.ValidationError`;package README 新增;docstring/comment 決策編號(design.md §、DEV-XX、R8、Q1)全數移除、理由 self-contained 化(`envelope §` 引用保留 — repo 內可解析);inspect helper 改 future 式;force 測試改名補強。

## 文件修正

| 目錄 | 修正內容 |
| --- | --- |
| `backend/ingestion/sec_text_pipeline/README.md` | 新增:scope、module map、資料流、A/B 邊界、兩段 cache、extension guidelines |
| `AGENTS.md` | §4 新增 Ingestion Rewrite Coexistence 段落(temporary until sunset) |
| 全 package + sec_core + tests | docstring 決策編號清除,理由 inline 化 |
| Linear DEV-132 | description 新增「Review 裁決紀錄」段(四項裁決 durable 化) |
| Linear DEV-139 | sunset 砍除清單 + AC 加入 AGENTS.md 段落刪除 |

## 未處理項目

無 — 所有 findings 均 fixed 或 declined-by-ruling(裁決已 durable 化於 AGENTS.md / issue description)。

## Final Verification Results

### Code Level

- [x] Unit Tests: `uv run pytest backend/tests/ -q` → **979 passed, 49 deselected**
- [x] Lint: `uv run ruff check backend/` → All checks passed
- [x] Format: `uv run ruff format --check backend/` → 171 files already formatted

### Behavior Level

- [x] 真實 ticker 全鏈路(AC1):AAPL FY2025 `parse_filing("AAPL", 2025, force=True)` → 17 items 全 FlatItem、stub(6/10/11/12/13)全 drop、substantive items 長度完整、JSON round-trip 綠
- [x] `fetch_filing_bundle` metadata 與 parse 結果一致(accession `0000320193-25-000079` / cik `320193` / `aapl-20250927.htm`)
- [x] v1 `is_stub_section` 位元等價(equivalence tests)+ inflight single-flight tests 全過

### Runtime / Observable Level

- [x] Round 4 targeted confirm:trim 邊界 14 案例 read-only assertion matrix 全過(Codex 實測)

## All Changed Files

| 檔案 | Review 修正摘要 |
| --- | --- |
| `backend/common/sec_core.py` | classify_stub_section(參數化 helper)、FetchedFiling + fetch_filing_bundle、fetch 拆層(locate/obj)、metadata error mapping;既有 API 位元不變 |
| `backend/ingestion/sec_text_pipeline/filing_models.py` | 凍結 schema;extra="forbid" |
| `backend/ingestion/sec_text_pipeline/parser.py` | parse_filing 主流程;structural boundary trim(三輪收斂);EmptyFilingError;簽名定案 |
| `backend/ingestion/sec_text_pipeline/stub_detection.py` | v2 patterns(bounded multi-word 第三 pattern) |
| `backend/ingestion/sec_text_pipeline/filing_store.py` | JSON store;ticker validation 收緊 |
| `backend/ingestion/sec_text_pipeline/__init__.py` / `README.md` | public surface + package 導覽 |
| `AGENTS.md` | 共存契約段落 |
| `backend/tests/…`(7 files + fixture) | Seam-1 tests(AAPL FY2025 錄製)、trim/stub/store/bundle/document-access regressions |

## Learning Notes

### 採用的工程策略

- **錄製真實資料當 fixture,而不是手寫「像真的」資料** — M-1.1 之所以被抓到,是因為 fixture 換成真 AAPL FY2025 後帶進了 Item 11 bleed 與重複 Item 8 兩個真實 quirk;synthetic fixture 版本讓同一個 bug 安然通過了兩輪測試。
- **只增不減的凍結邊界靠「行為」定義,不是「簽名」** — M-2.1:`fetch_filing_obj` 簽名與函式本體一字未改,但內部委派讓它多打一次網路 — observable behavior(含網路呼叫序列)才是凍結的單位,regression test 直接斷言「不觸碰 `filing.document`」。

### 權衡取捨

- **裁決的 durability 是流程成本問題**:M-1.5 / force 語意在裁決後仍被下一輪 reviewer 重新舉報,直到寫進 AGENTS.md(每 session 自動載入)與 issue description 才停止 — 裁決不落在 reviewer 必經的面上,就得每輪重付溝通成本(M-2.4 的真正效益)。
- **ADR vs AGENTS.md**:time-boxed 的規則放 AGENTS.md(sunset 時隨凍結管線一起刪),永久架構決策才進 ADR — 這次 declined ADR 是因為需求本質是「共存期間 reviewer 找得到」而非「歷史記錄」。

### 關鍵收穫

- **文字邊界 heuristic 要用「觀察到的形態」做判別器,而不是寬鬆匹配**(SP-2.1 → X-3.1 兩輪收斂):inline 引用前必有空格、bleed 黏接必無空格、字母黏接僅 `PART <roman>` 一種 — 每輪 false positive 都逼出一個更精確的 lexical constraint,最後由 14 案例 matrix 鎖住。
- **「移除匹配句 → 檢查剩餘內容量」機制的前提是輸入邊界正確**(M-1.1):remaining-content 判定對「本體 + 黏進來的外來內文」完全失效 — 任何 content-volume heuristic 都隱含「輸入已正確切界」的前置條件。
- **cache 會固化錯誤**(M-1.4):silent empty 不只是一次壞回答 — 落地後每次 cache hit 都重播它;失敗必須在落地前擋下(committed or absent)。
- **跨 model review 的價值在盲點互補**(整個 loop):Claude 事前 review + Codex 兩軸抓到的集合幾乎不重疊 — bleed、over-trim、legacy 行為漂移全部來自第二雙眼睛。
