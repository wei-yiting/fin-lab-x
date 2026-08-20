# Code Review Improvement Report

> **Task:** DEV-160 — SEC text pipeline cutover：JIT retriever + production routing
> **Date:** 2026-08-20（loop 起於 2026-08-19）
> **Rounds:** 10（8 輪 code-review-loop 收斂 + 2 輪 envelope review cycle）
> **Reviewer model:** gpt-5.6-sol（Codex，rounds 1–8、10）；Claude Fable 5（round 9 envelope review，獨立 agent）
> **Fixer model:** Claude Sonnet 5 subagents（rounds 1–5、9）；orchestrator 直接修正（m-6.1、m-7.1、m-10.1）

## 架構影響摘要

- **`search()` 的介面契約收緊**：`filters` 從 optional 裸搜模式改為必填 `SearchFilters` TypedDict（`ticker` 必填、`fiscal_year` optional），boundary validation 拒絕非 dict、未知 key（含舊契約的 `year`）、錯誤型別——依據 DEV-113 A/B 實驗數據（naive search `ticker_precision@10` 最低 0.00），裸搜路徑整個移除。**下游 DEV-142/164 接線時必須帶 ticker。**
- **錯誤 taxonomy 統一**：`EmbeddingServiceError` 移至 `sec_dense_pipeline/common.py`，query-embed 與 ingest-embed 失敗同一標籤；Qdrant payload 損壞（缺欄、型別錯、無 payload）一律 `CorpusUnavailableError`；marker lookup 失敗 propagate 而非吞成 cache miss。
- **Retry 架構落位**：`retry_transient`（ADR-0013）成為全鏈路唯一 retry 機制——`parse_filing_with_retry` 住進 `sec_text_pipeline/parser.py`、公開的 `resolve_latest_fiscal_year` 住進 `backend/common/sec_core.py`（freeze 允許的 additive 變更）、Qdrant 邊界在 `vectorizer.py` 做 blanket 單次重試（qdrant-client 零內建 retry）。Embedding 不包——SDK 內建重試，避免 stacked retry。
- **並行 JIT 定案落地**：in-process `(ticker, fiscal_year)` registry + claim 後二次 marker 檢查（消除 stale-marker race），符合 envelope §1 的明文例外。
- **Operator 路徑分流**：`embed_sec_filings.py` 專屬新 collection；新增 `embed_sec_filings_html.py` 回填凍結 collection（DEV-162/138 需求），sunset 時整檔刪除。

## Summary

| 指標 | 數值 |
| --- | --- |
| 總輪數 | 10（quality 每輪 findings：15→9→5→4→1→1→1→0 → envelope 10→1→0） |
| 發現 findings 總數 | 47（quality 41 + spec 6） |
| Blocking | 5/6 fixed（SP-1.2 re-scoped → DEV-171） |
| Major | 18/21 fixed（M-1.1 reachability 半、M-1.6/F-9.6 tracing 由 user 裁決 dismiss，各附小型文件修正） |
| Minor | 14/15 fixed（F-9.8 deferred） |
| Suggestion | 3/3 adopted |
| Spec findings (SP-) | 4/6 fixed、1 re-scoped（DEV-171）、1 半 dismissed（embedding retry，ADR-0013） |
| 文件修正 | 8 個檔案（3 個 README + 3 份 docs/ + eval scenario setup + scripts README） |

## Spec Conformance（Spec 軸）

| ID | 類型 | Spec 依據 | 結果 |
| --- | --- | --- | --- |
| SP-1.1 | Misimplemented | 「檢索必須帶 ticker + fiscal_year filter 條件...不能是裸 vector search」 | Fixed（user 修改方向：ticker 改為硬性必填，引 DEV-113 數據） |
| SP-1.2 | Missing | 「Source-level missing Item → 結構化 legible error」 | Re-scoped → DEV-171（user 裁決：需 schema + tool 層設計，retriever 層做不到；Linear AC 已劃線標注） |
| SP-1.3 | Misimplemented | 「冷查詢端到端...熱查詢直接命中」 | Fixed（`SEC_DISABLE_JIT` guard 移到真正要打 EDGAR 時才觸發） |
| SP-1.4 | Missing | 「JIT fetch 路徑是 retry_transient 的首發使用者」 | Fixed（latest-year 解析納入 retry） |
| SP-1.5 | Missing | 「在 embedding/Qdrant client 邊界把可重試失敗分類為 TransientError」 | Qdrant 半 fixed；embedding 半 dismissed（user 裁決：SDK 內建重試，再包=stacked retry） |
| SP-1.6 | Misimplemented | 「latest-year 解析正確運作並回報 resolved year」 | Fixed（resolve 成功、後續失敗時 summary 仍顯示已解析年度） |

Rounds 2–10 spec 軸連續九輪零 findings——需求覆蓋完整、無 scope creep。

## Reading Guide

| 順序 | 檔案 | 在本次變更中的角色 | 風險 |
| --- | --- | --- | --- |
| 1 | `backend/ingestion/sec_dense_pipeline/retriever.py` | 核心新檔：`SearchFilters` 契約、`search()` JIT 編排、並行 registry、錯誤映射 | ⚠️ 對外 API contract + 錯誤 taxonomy |
| 2 | `backend/ingestion/sec_dense_pipeline/common.py` | 共用 async marker check（propagate 語意）+ `EmbeddingServiceError` 的家 | |
| 3 | `backend/ingestion/sec_dense_pipeline/vectorizer.py` | `ingest_filing` embed 失敗分類 + Qdrant blanket retry wrapper | |
| 4 | `backend/common/sec_core.py` | 新增公開 `resolve_latest_fiscal_year`——凍結模組，確認 diff 只加不改 | ⚠️ frozen module（additive-only 檢查） |
| 5 | `backend/ingestion/sec_text_pipeline/parser.py` | `parse_filing_with_retry` 新家 | |
| 6 | `backend/scripts/embed_sec_filings.py` | Batch cutover：`--fiscal-year`、eager 年度解析、寫新 collection | ⚠️ operator 行為改變（舊指令會灌新 collection） |
| 7 | `backend/scripts/embed_sec_filings_html.py` | 凍結 collection 的 operator 回填 script（sunset 時整檔刪） | |
| 8 | 3× README + `docs/{observability,file_structure,agent_architecture}.md` | Cutover 後的事實校正 | |
| 9 | `backend/tests/...`（8 個 test 檔 + conftest） | 抽查即可——`test_retriever.py` 的 `search_env` fixture 與 parametrized missing-key/invalid-filter 群最值得看 | |

## 所有修正問題詳解

> 依主題分組；每項含 問題/修法/影響/驗證。ID 對應 round 檔案（`artifacts/current/code-review-loop/`）。

### 介面契約與 boundary validation

**B-1.1 / SP-1.1（Blocking）+ M-2.3 + M-3.2 + M-4.1**
- **問題：** `search()` 允許無 ticker 的裸搜（DEV-113 實測有害）；後續輪又發現 filters 型別鬆散（`dict | None`）、未知 key 靜默忽略（舊 `year` key 會被吃掉改查 latest）、非 dict 輸入炸 raw `TypeError`。
- **修法：** 四輪漸進收緊為：必填 `SearchFilters` TypedDict + `_validate_filters()` runtime 驗證（非 dict／未知 key／非 str ticker／非 int fiscal_year 全部 legible `ValueError`），I/O 前完成。
- **影響：** 消除 cross-ticker bleed 與 DEV-142 遷移期 silent wrong-year 風險；錯誤全部可歸因。
- **驗證：** unit tests（None/空/fiscal-year-only/legacy-year/非 dict/錯型別 各一）+ 成功路徑斷言雙 must 條件（AC 指定驗證方式）。

**M-4.2 + M-5.1 + F-9.9（payload 邊界）**
- **問題：** `_point_to_chunk` 用 `.get(key, default)` 讀 required 欄位（`ingested_at` → 後又發現 `block_heading`/`prelude` 同型漏網），缺欄=corpus 損壞卻靜默補值；pydantic `ValidationError` 還會從 `ValueError` passthrough 漏出。
- **修法：** 兩輪逐欄修後，round 9 以 `Chunk(**payload, score=...)` 一次取代——pydantic missing-field 驗證涵蓋所有欄位，call site 統一映射 `CorpusUnavailableError`（帶 point id）。
- **影響：** 任何 payload 損壞都 legible，且刪掉 14 行手寫欄位映射。
- **驗證：** parametrized missing-key search-level test（3 欄位）+ `payload=None` test；pydantic 2.12.5 行為實測確認。

**M-2.4（marker lookup 吞錯）**
- **問題：** `check_commit_marker_complete` catch-all 回 `False`——Qdrant 真故障被當「未 ingest」，觸發整套重 ingest。
- **修法：** 只有乾淨查詢無 marker 才回 `False`；exception propagate 進 `search()` 既有映射。
- **影響：** 故障不再偽裝成 cache miss。
- **驗證：** `unit/test_common.py` propagation tests；integration 兩處依賴舊行為的斷言以更直接的檢查取代。

### JIT 行為與並行

**M-1.2 / SP-1.3（`SEC_DISABLE_JIT` 誤擋熱查詢）**
- **問題：** flag 在 marker check 前無條件擋，已 ingest 的資料也查不到。
- **修法：** guard 拆兩點——省略年度時（latest 解析本身要打 EDGAR）在 `search()` 擋；明確年度只在 marker miss 時於 `_ensure_ingested` 擋。
- **影響：** CI 防線保留，熱查詢照常服務。
- **驗證：** flag-on 熱命中/冷 miss 兩半各有 test；F-9.1 後全 suite 亦在 `SEC_DISABLE_JIT=1` 下綠燈。

**M-1.5（stale-marker race）+ m-3.2 + m-4.2（race test 品質）**
- **問題：** 第二個 caller 的 marker 查詢過期，會白做整套 re-ingest（含一個 §2 級的短暫 partial-read 窗口）；後續兩輪又修 test 本身（無 barrier 靠運氣、barrier 失敗時會 hang）。
- **修法：** claim slot 後二次 marker check，命中直接回 `cache_hit=True`；test 用 `asyncio.Event` barrier + `asyncio.wait` race + timeout。
- **影響：** 並行冪等且省 API 成本；integration gate 不會偶發卡死。
- **驗證：** race unit test + barrier integration test 連跑 15 次確定 deterministic + 人工注入早期失敗確認 fail-fast。

### Retry 與錯誤分類

**M-1.3 + M-2.1 + M-3.1 → F-9.3（Qdrant retry 的演化與簡化）**
- **問題：** 初版 `except httpx.*` 是 dead code（qdrant-client transport 先包成 `ResponseHandlingException`）且把 validation error 誤判 transient；兩輪擴充 taxonomy 後，round 9 判定整套 source-type 分類超出 envelope §2。
- **修法：** 最終形（user 裁 B 案）：blanket——任何 `ResponseHandlingException` 與 5xx `UnexpectedResponse` → `TransientError` 單次重試，4xx/其他 propagate；taxonomy 與 ~50 行註解刪除。
- **影響：** 滿足票的 AC（qdrant-client 零內建 retry）同時回到 envelope 的 simplest handling；代價僅為永久錯誤多白試一次。
- **驗證：** 3 個分類 tests（blanket / 5xx-vs-4xx / 其他 propagate）；m-10.1 再把 test 對 httpx 子類的殘餘 coupling 拆掉。

**M-1.4 / SP-1.4 + F-9.10（latest-year retry 與 wrapper 落位）**
- **問題：** `_resolve_latest_fiscal_year`（EDGAR call）裸奔無 retry；修好後 round 9 又指出 wrapper 放在 vectorizer 造成依賴方向錯誤。
- **修法：** 公開 `resolve_latest_fiscal_year` 進 `sec_core.py`（additive、freeze 合規）、`parse_filing_with_retry` 進 `parser.py`；所有 caller 與 test patch target 重指。
- **影響：** §2 single-retry policy 單點化，模組各管各的關注點。
- **驗證：** transient-then-success / permanent-no-retry tests 隨遷移；repo-wide 舊名掃描為空；full suite 綠。

**F-9.2（cold path embedding 失敗誤標）**
- **問題：** ingest 內 embedding 失敗變 `CorpusUnavailableError`，同類失敗在 query-embed 卻是 `EmbeddingServiceError`。
- **修法：** `EmbeddingServiceError` 移至 `common.py`；`ingest_filing` 的 embed call 包 `except FinLabError: raise` + `except Exception → EmbeddingServiceError`。
- **影響：** taxonomy 一致，故障可歸因。
- **驗證：** 走真實 retry chain 的 cold-path test。

**SP-1.6（batch summary 丟失已解析年度）**
- **問題/修法/影響：** resolve 成功、ingest 失敗時 summary 印 `?` → `main()` 迴圈先 eager resolve 再呼叫 `_parse_and_ingest`（S-2.1 一併移除 mutable out-param）→ operator 永遠看得到真實年度。
- **驗證：** omitted-`--fiscal-year` + ingest 失敗的 summary test。

### 可達性、operator 路徑與環境

**F-9.1（Blocking：CI 環境變數弄紅新測試）**
- **問題：** CI 全域 `SEC_DISABLE_JIT=1`，新 pipeline 測試缺凍結樹已有的 `_unset_disable_jit` autouse fixture——merge 即紅燈。8 輪 loop 從未用 CI 環境組合跑過測試，直到 round 9 才被抓到。
- **修法：** 共用 conftest 加 autouse `delenv` fixture。
- **驗證：** `SEC_DISABLE_JIT=1` 下 76 passed（先前 2 failed）。

**M-1.1（consequence 部分）**
- **問題：** batch script 切新 collection 後，operator 失去凍結 collection 的回填路徑（DEV-162 新 dataset / DEV-138 A/B 都需要）。reachability 指控本身由 user dismiss（DEV-142/161/164 為排定 consumer）。
- **修法：** 新增獨立 `embed_sec_filings_html.py`（user 裁決：符合 `_html` sunset 整檔刪除慣例，勝過 `--pipeline` flag 方案）；復活原 batch CLI test 並重指。
- **驗證：** integration test（failure isolation + commit marker + exit code）。

**F-9.7（sync marker check 無 caller）**
- **問題/修法：** async 版落地後 sync 版只剩測試在用（§0 reachability）→ 刪除、predicate inline、integration 斷言改用 raw client `retrieve()`。

### 文件與衛生

**m-1.1 + m-2.2 + m-3.1 + M-2.2（process 詞彙洩漏）**
- **問題：** `DEV-160`/`DEV-113`/`DEV-138`/`DEV-162` issue IDs 與 `M-1.2/SP-1.3` finding IDs、「the AC」等 review 詞彙洩入 production docstring、error message、test docstring——同一問題分四輪才清完（round 2 修一批、round 3 又抓到殘留）。
- **修法：** 全部改為自足的行為描述。
- **驗證：** repo-wide pattern 掃描為空。

**m-4.1 + m-6.1 + m-7.1 + F-9.5（文件正確性）**
- **問題：** vectorizer「no retry wrapper」過期敘述；凍結 README Quick Start 範例不帶 ticker（永遠走不到它宣稱的 JIT）、bash fence 混 Python top-level await（兩者皆為 round 1 修 M-1.1 時自己造成的 regression）；`docs/observability.md` 教 operator 用已改道的 script 餵 `_html` collection。
- **修法：** 各檔校正至與 code 一致；只改本 PR 弄錯的敘述，DEV-142 前仍為真的描述不動。

## 文件修正

| 目錄 | 修正內容 |
| --- | --- |
| `backend/ingestion/sec_dense_pipeline/README.md` | 補 `retriever.py`（Structure Map、search contract、JIT flow、並行、error mapping、retry 邊界、`SEC_DISABLE_JIT`）；「single JIT query entry point」措辭修正 |
| `backend/ingestion/sec_dense_pipeline_html/README.md` | 移除 issue ID；Quick Start 補 ticker filter、拆成可執行的 bash/python fences；註明回填走 `embed_sec_filings_html.py` |
| `backend/scripts/README.md` | 新增 `embed_sec_filings_html.py` 條目；tracing 敘述改為 follow-up ticket |
| `backend/evals/scenarios/sec_retrieval/README.md` | eval 預載指令改指 `embed_sec_filings_html.py`（原指令會灌錯 collection） |
| `docs/observability.md`、`docs/file_structure.md`、`docs/agent_architecture.md` | Batch CLI 目標與 pipeline 描述校正至 cutover 後事實 |

## 未處理項目

| 類型 | 內容 | 原因 | 建議後續 |
| --- | --- | --- | --- |
| Re-scoped | Source-level missing Item legible failure（SP-1.2） | 需 schema + tool 層設計，非 retriever 修得了 | **DEV-171**（已開票，blocked by DEV-160） |
| Dismissed (user) | JIT tracing / trace root（M-1.6、F-9.6） | 明文拆票，DEV-161 blocked by 本票；本 PR 無 user-facing 流量切換 | DEV-161 |
| Dismissed (user) | Embedding 失敗納入 `retry_transient`（SP-1.5 半） | SDK 內建重試；再包=ADR-0013 stacked-retry 反模式 | 無 |
| Deferred | 每次 query 4 個 ensure-collection round-trips（F-9.8） | envelope §1 <1 QPS 下非問題；修法與 M-2.4 的 propagate 裁決部分衝突 | 若日後做 bootstrap ownership 重整再議 |
| Pre-existing | `sec_filing_tools.py` 直呼無 retry 的私有 resolver（F-9.10 附帶發現） | 非本 diff regression | DEV-142 接線時改用新公開 resolver |
| Pre-existing | pyright：`PointStruct(payload=ChunkPayload)` 等 16 個既有 type errors | main 上已存在，驗證非本次引入 | 獨立清理 |

## Final Verification Results

### Code Level（orchestrator 親自執行，2026-08-20）

- [x] Unit + script + common tests：`uv run pytest backend/tests/ -q` → **1,274 passed**, 61 deselected
- [x] CI 環境組合：`SEC_DISABLE_JIT=1 uv run pytest backend/tests/ingestion/sec_dense_pipeline/ backend/tests/scripts/ -q` → **76 passed**
- [x] Integration（真 local Qdrant）：`-m integration` → **39 passed**
- [x] Lint：`ruff check backend/` → clean；`ruff format --check backend/` → 214 files formatted
- [x] Type check：pyright 對 pipeline + sec_core + parser → **零新增 errors**（16 個 pre-existing，已對照 main 確認）

### Behavior / Observable Level（Manual — 由作者親自驗證）

本 session 無 `bdd-scenarios.md` / `verification-plan.md`；經討論，Level 2/3 由作者手動執行下列 checklist（同時作為 PR 的 Manual Validation checklist）。**注意：1、2、4 會打真 EDGAR + OpenAI（產生少量 embedding 費用）；先確認 `backend/.env` 的 `EDGAR_IDENTITY`/`OPENAI_API_KEY`、Qdrant 容器運行中。**

- [ ] **冷查詢端到端**：對一個未 ingest 的 (ticker, fiscal_year) 呼叫 `search()` → 回傳非空 chunks、log 出現 `cache_hit=False`、Qdrant 出現該 ticker 的 points 與 `complete` marker
- [ ] **熱查詢**：同一 (ticker, fiscal_year) 再查一次 → 明顯變快、log `cache_hit=True`、無重新 parse/embed
- [ ] **JIT guard**：`SEC_DISABLE_JIT=1` 下對另一個未 ingest 的 ticker 查詢 → 收到 `JITDisabledError`（訊息可讀），無 EDGAR 流量
- [ ] **Batch 分流**：`embed_sec_filings.py <TICKER>` 灌進 `sec_filings_openai_large_dense_text`（新）、`embed_sec_filings_html.py <TICKER>` 灌進 baseline collection（舊），summary 各自顯示 resolved year、exit code 0

## All Changed Files

| 檔案 | Review 修正摘要 |
| --- | --- |
| `backend/ingestion/sec_dense_pipeline/retriever.py`（新，415 行） | SearchFilters 契約、guard 重排、race 修正、payload 邊界驗證、`Chunk(**payload)` |
| `backend/ingestion/sec_dense_pipeline/common.py` | async marker check（propagate 語意）、`EmbeddingServiceError`、sync 版刪除 |
| `backend/ingestion/sec_dense_pipeline/vectorizer.py` | blanket Qdrant retry、embed 失敗分類、wrapper 遷出 |
| `backend/common/sec_core.py` | +公開 `resolve_latest_fiscal_year`（additive-only） |
| `backend/ingestion/sec_text_pipeline/parser.py` | +`parse_filing_with_retry` |
| `backend/scripts/embed_sec_filings.py` | 新 contract、`--fiscal-year`、eager resolve、`BatchIngestResult` |
| `backend/scripts/embed_sec_filings_html.py`（新） | 凍結 collection 回填 |
| `backend/ingestion/sec_dense_pipeline_html/retriever.py` | 一行 error message 指向新回填 script |
| 8 個 test 檔 + conftest | 見 Reading Guide；net test:production 比 1.54× |
| 3 README + 3 docs/ | 見文件修正表 |

## Learning Notes

### 採用的工程策略

- **Ticker 必填由數據背書，不是風格偏好**——B-1.1 的裁決直接引 DEV-113 A/B 實測（naive `ticker_precision@10` 最低 0.00、「production 沒有對應物」），把「介面該多嚴」從品味之爭變成證據問題。
- **In-process registry + post-claim recheck（M-1.5）**：check-then-insert 的 atomicity 只保護 registry 本身，不保護先前觀察的新鮮度——claim 之後重驗一次外部狀態，才是完整的並行契約。
- **Retry 的家跟著關注點走（F-9.10）**：wrapper 放在「誰擁有被包的操作」的模組，而不是「誰先用到」的模組；否則 retriever 得從 ingest 模組 import EDGAR 邏輯。

### 權衡取捨

- **Correctness 驅動的精修會複利成 over-engineering（M-1.3→M-2.1→M-3.1 vs F-9.3）**：三輪各自正確的修正（dead code 移除→補 sibling types→重分類 RemoteProtocolError）疊出 70 行 taxonomy，最後被 envelope 視角一次拆回 blanket。教訓：per-finding 的局部正確 ≠ 整體適度，收斂後值得用 envelope 重看一次總量。
- **測試量的棘輪效應（F-9.4）**：每個 fix 依 §4 zone 標準配測試、沒人踩 §5 rule 5 的剎車，比例悄悄爬到 2.18×；envelope review 砍回 1.54×。§4 的嚴格與 §5 的節制需要同一個人同時拿著。

### 關鍵收穫

- **Sibling sweep 是 fix 的一部分，不是加分項**——同型漏網連發三次（m-2.2→m-3.1 的 issue ID 殘留、M-2.1 的 exception 兄弟類、M-4.2→M-5.1 的 `.get()` 鄰行），每次都多花一輪。Round 6 起把 sweep 寫進 fixer 任務後不再復發。
- **測試要用部署環境的變數組合跑（F-9.1）**：8 輪 review、上千次綠燈，全部沒發現 CI 的 `SEC_DISABLE_JIT=1` 會弄紅新測試——因為沒有人用那個環境跑過。「本地綠」≠「CI 綠」，環境矩陣是驗證的一維。
- **Schema 驗證交給 schema（F-9.9）**：rounds 4–6 逐欄位手修 `.get()`→`[key]`，round 9 用 `Chunk(**payload)` 讓 pydantic 一次管所有欄位——在錯誤的 altitude 上迭代，每步都對，但整條路不如換一層抽象。
- **凍結樹的既有寫法不是契約背書（B-1.1）**：舊 `_html` retriever 允許裸搜曾被當成「介面先例」的辯護，但先例只是歷史包袱——判斷依據應是數據（DEV-113）與 envelope，不是「以前就這樣」。
