# Code Review Improvement Report

> **Task:** DEV-135 — sec_dense_pipeline 新 contract:結構化 ingest + Qdrant payload schema + commit marker
> **Date:** 2026-08-11
> **Rounds:** 2
> **Reviewer model:** Round 1 quality 軸 gpt-5.6-sol(Codex)+ spec 軸 claude;Round 2 claude-sonnet-5(Codex 連續兩次 dispatch hang,依 skill fallback 規則改用 Claude read-only subagent;round 1 的 cross-model review 成果不受影響)
> **Fixer model:** claude-sonnet-5(isolated subagent)

## 架構影響摘要

- **`ingest_filing` 入口新增 zero-chunk guard(B-1.3)**:chunk 產出為零的 filing 現在在**任何 Qdrant mutation 之前**拋出 `EmptyIngestError`(`SECError` 子類、已 export 至 package 公開面)— collection 不會被建立、marker 不會被寫入。DEV-137 接 JIT 時必須 catch 它來渲染 legible failure(envelope §4)。
- **`item` payload 欄位在 contract boundary 正規化(B-1.2)**:`build_chunk_payloads` 對每個 Item 做一次 `strip().lower()`,payload/index 用正規化 key(`"7a"`)、`header_path` 顯示層用大寫(`Item 7A.`)— 公開 contract 不再依賴 parser 恰好輸出小寫。
- **payload 型別化(m-1.2)**:`ChunkPayload(TypedDict)` 取代 `dict[str, Any]`,成為 chunking → vectorizer → 未來 retriever 的 typed contract。
- 四項 review 發現由 user 裁決為明文例外/延後(B-1.1、M-1.1、M-1.2、M-1.3),裁決全文在 DEV-135 description「Review round 1 裁決紀錄」;其中兩項已登錄為 DEV-137 agent todo。

## Summary

| 指標 | 數值 |
| --- | --- |
| 總輪數 | 2 |
| 發現 issues 總數 | 14(round 1: 12,round 2: 2) |
| Blocking | 2/3 fixed(B-1.1 user-ratified 延至 DEV-137) |
| Major | 0/3 fixed(三項全數 user-ratified:先例例外/上游已解/延至 DEV-137) |
| Minor | 6/6 fixed |
| Suggestion | 1/2 adopted(s-2.1 依 reviewer 自評 optional polish 不採) |
| Spec findings (SP-) | 0/0 — 無 findings |
| 文件修正 | 5 檔(module README、docs/file_structure.md、backend/README.md、root README.md、CONTEXT.md glossary) |

## Spec Conformance(Spec 軸)

Spec 軸無 findings — 需求覆蓋完整、無 scope creep。DEV-135 四條 AC、三項實作裁決(no retry / helpers 複製 / fiscal_year)經逐行核對全數通過;`marker_status_condition()` helper 被評估為 plumbing 而非 scope creep(服務 AC「檢索 query 排除 marker point」的單一定義點)。

## Reading Guide

| 順序 | 檔案 | 在本次變更中的角色 | 風險 |
| --- | --- | --- | --- |
| 1 | `backend/ingestion/sec_dense_pipeline/chunking.py` | `ChunkPayload` typed contract + per-block chunking + item 正規化 — 整個新 collection 的 payload schema 定義點 | ⚠️ |
| 2 | `backend/ingestion/sec_dense_pipeline/common.py` | marker 生命週期 primitives(`commit_marker_id` / `check_commit_marker_complete` / `marker_status_condition`)— ingest 與未來 retriever 共用的 contract | ⚠️ |
| 3 | `backend/ingestion/sec_dense_pipeline/vectorizer.py` | `ingest_filing` 主流程:empty guard → marker pending → wipe → embed → upsert → complete | ⚠️ |
| 4 | `backend/ingestion/sec_dense_pipeline/collection_schema.py` | race-safe collection + payload index bootstrap(ticker tenant / fiscal_year / item) | |
| 5 | `backend/ingestion/sec_dense_pipeline/__init__.py` | package 公開面(`ingest_filing`、`EmptyIngestError`、marker helpers) | |
| 6 | `backend/tests/ingestion/sec_dense_pipeline/unit/test_chunking.py` | Seam-2 pure 斷言:payload 欄位、邊界、overlap、正規化 | |
| 7 | `backend/tests/ingestion/sec_dense_pipeline/integration/test_ingest.py` | Seam-2 Qdrant 可觀察狀態:marker 生命週期、committed-or-absent、marker 排除 | |
| 8 | `backend/ingestion/sec_dense_pipeline/README.md` + docs 三檔 + `CONTEXT.md` | env-var contract、structure maps、glossary 同步 | |

## 所有修正問題詳解

### B-1.2(Blocking)
- **問題:** payload 的 `item` 直接寫入 `item.item`,schema 允許 `"7A"`、`" 7a "` 等輸入,會破壞 `item` index/filter contract;現行 parser 恰好輸出小寫不構成公開 contract 的保證。
- **修法:** `build_chunk_payloads` 內每 Item 正規化一次(`strip().lower()`),payload 用正規化 key、`header_path` 用 `upper()` 顯示。`sec_core.parse_item_number()` 經評估不重用(它是 agent-facing whitelist,對 schema-valid 但非標準的 key 會 raise)。
- **影響:** `ingest_filing(ParsedFiling)` 的 index/filter/citation-ID contract 不再依賴上游輸出形狀。
- **驗證:** 新 parametrized unit test `test_item_is_normalized_at_the_contract_boundary`("7A" / " 7a " / " 7A ");round 2 reviewer 逐行核對 ✅。

### B-1.3(Blocking)
- **問題:** 空 items 或全空白 text 的 filing 會產生零 chunks,但 marker 仍被寫成 `complete` — retrieval 端看到「已 ingest 的空語料」,violate committed-or-absent(envelope §2「silent empty answers are bugs」)。
- **修法:** `build_chunk_payloads` 移到 `ingest_filing` 開頭、任何 Qdrant client 建立之前;零 payload → 拋 `EmptyIngestError(SECError)`(定義在 `vectorizer.py`,`sec_core` only-add 未動)。
- **影響:** 空 filing 對檢索端完全不可見(連 collection 都不會建立),失敗 legible 且可被 DEV-137 映射為使用者可見的錯誤。
- **驗證:** 新 integration test `test_empty_filing_raises_and_leaves_no_trace` 斷言 `collection_exists() is False`;round 2 reviewer 評為「the strongest possible no-mutation assertion」✅。

### m-1.1(Minor)
- **問題:** embedding cleanup 讀取 `OpenAIEmbedding._aclient`(pinned package 的 `PrivateAttr`,非公開 API)— 從凍結 baseline 複製來的繼承技術債。
- **修法:** 改為 caller 自建 `httpx.AsyncClient()` 經公開參數 `async_http_client=` 注入(以 `inspect.signature` 驗證 pinned 0.6.0 支援),`finally` 中 `await aclose()`。
- **影響:** 不再依賴 vendor private state,升版安全。
- **驗證:** round 2 reviewer 獨立重跑 `inspect.signature` 確認 ✅;19 tests pass。

### m-1.2(Minor)
- **問題:** `build_chunk_payloads -> list[dict[str, Any]]` 把 payload schema 抹平成 untyped bag,違反 repo strict typing。
- **修法:** `ChunkPayload(TypedDict)` 全 13 欄 + `ingested_at: NotRequired[str]`(vectorizer 補上時機正確表達)。
- **影響:** 缺欄/改名/型別錯誤進入 static checking 視野;retriever(DEV-137)直接拿到 typed contract。
- **驗證:** ruff + 全 suite 綠;round 2 reviewer 核對 ✅。

### m-1.3(Minor)
- **問題:** integration tests 每測試自建 `QdrantClient` 不關閉,transports 洩漏。
- **修法:** yielding `qdrant_client` fixture(`finally: close()`),`clean_collection` 依賴它共用同一 client。
- **驗證:** teardown 順序正確(cleanup 先於 close);round 2 reviewer 核對 ✅。

### m-1.4(Minor)
- **問題:** `docs/file_structure.md`、`backend/README.md`、root `README.md` 未列出 `sec_text_pipeline` 與新 `sec_dense_pipeline`,contributor 無法從 authoritative docs 理解 coexistence boundary。
- **修法:** 三處 structure map 補列新 pipelines 與對應 tests,`_html` 兩樹標注 "Frozen A/B baseline (deleted whole at sunset)"。
- **驗證:** round 2 reviewer 逐行核對三檔一致 ✅。

### m-1.5(Minor)
- **問題:** test 檔數處 lazy import 不符 CLAUDE.md Python Import Style 四例外。
- **修法:** 全部上移 module top(patch string target 不受影響)。
- **驗證:** round 2 reviewer 確認兩檔已無 function-body import ✅。

### S-1.1(Suggestion,adopted)
- **問題:** module README 缺 env-var contract 與 extension 指引。
- **修法:** Environment Variables table(六變數含 default)+ payload filter 欄位變更的 lockstep note(payload construction / index bootstrap / marker exclusion / retrieval 四處同步)。
- **驗證:** round 2 reviewer 交叉核對 table 與 code defaults 一致 ✅。

### m-2.1(Minor,round 2 發現)
- **問題:** B-1.3 讓 `EmptyIngestError` 成為入口的可觀察 contract,但 package `__init__` 未 export — DEV-137 caller 得繞進 submodule 才拿得到。
- **修法:** `__init__` import + `__all__` + docstring 公開面句子補上。
- **影響:** DEV-137 的 legible-failure handling 可直接 `from backend.ingestion.sec_dense_pipeline import EmptyIngestError`。
- **驗證:** orchestrator 直接核對最終檔案(一行級修正,不另開第三輪);ruff + 19 tests 綠。

## 文件修正

| 目錄 | 修正內容 |
| --- | --- |
| `backend/ingestion/sec_dense_pipeline/README.md` | env-var table、extension note、`EmptyIngestError` 語意 |
| `docs/file_structure.md` | §2.4 ingestion map + §2.8 test map 補新 pipelines、標注 frozen baselines |
| `backend/README.md`、`README.md` | ingestion 段同步 |
| `CONTEXT.md` | glossary:Filing store(JSON ParsedFiling)、header_path(new contract 無 Part) |

## 未處理項目

| 類型 | 內容 | 原因 | 建議後續 |
| --- | --- | --- | --- |
| User-ratified(B-1.1) | 同 ticker 並行 ingest 序列化 | 本票零 caller,並行呼叫路徑不存在;envelope §1 禁 lock/queue,機制屬接線 slice 的設計 | 已登錄 DEV-137 agent todo(coalesce 或 "ingestion in progress" 回應) |
| User-ratified(M-1.1) | prelude size cap / quality gate | Gate 已在上游 DEV-133 detection 層(3,000-char threshold,72-probe 校準);ingest 信任 producer contract,單一定義點 | DEV-133 merge 後 contract 自動閉合;無後續動作 |
| User-ratified(M-1.2) | `ingest_filing` 零 production caller | envelope §0 reachability 明文例外,比照 DEV-132/141 先例;首發 caller 為 DEV-137 | 例外已記入 issue description;PR body 同步記載 |
| User-ratified(M-1.3) | ingest 內部 tracing spans | `traced_span` 需外層 active trace,由 DEV-137 JIT 鏈建立 | 已登錄 DEV-137 agent todo |
| Suggestion(s-2.1) | env-read timing 不一致(import-time vs call-time) | reviewer 自評 optional polish(envelope §7.4),鏡像凍結 baseline 模式、無受影響 consumer | 不處理;若未來動到該檔可順手統一 |

## Final Verification Results

### Code Level

- [x] Unit + Integration Tests(new pipeline):`uv run pytest backend/tests/ingestion/sec_dense_pipeline/ -q -m "integration or not integration"` → **19 passed**
- [x] Full backend suite:`uv run pytest backend/tests/ -q` → **994 passed, 55 deselected**
- [x] Lint:`uv run ruff check backend/` → All checks passed
- [x] Format:`uv run ruff format --check backend/` → 187 files already formatted

### Behavior Level

- [x] 兩條 dense pipeline(新 + 凍結 baseline)含 integration:**100 passed** — 凍結 baseline 零影響
- [x] AC 四條全數由 Seam-2 tests 證明(payload 全欄位含 citation 三欄 / chunk 邊界與 overlap / marker 生命週期 / 中斷模擬 committed-or-absent)

### Runtime / Observable Level

- [x] Qdrant 可觀察狀態斷言(真實 local Qdrant):marker pending→complete、wipe 含 marker 重置、空 filing 零 mutation、content query 排除 marker point

## All Changed Files

| 檔案 | Review 修正摘要 |
| --- | --- |
| `backend/ingestion/sec_dense_pipeline/chunking.py` | B-1.2 item 正規化、m-1.2 `ChunkPayload` TypedDict |
| `backend/ingestion/sec_dense_pipeline/vectorizer.py` | B-1.3 empty guard + `EmptyIngestError`、m-1.1 public client injection |
| `backend/ingestion/sec_dense_pipeline/__init__.py` | m-2.1 export `EmptyIngestError` |
| `backend/ingestion/sec_dense_pipeline/collection_schema.py` | 無 review 修正(round 1 即通過) |
| `backend/ingestion/sec_dense_pipeline/common.py` | 無 review 修正(spec 軸認定 `marker_status_condition` 為合理 plumbing) |
| `backend/ingestion/sec_dense_pipeline/README.md` | S-1.1 env-var table + extension note |
| `backend/tests/ingestion/sec_dense_pipeline/unit/test_chunking.py` | B-1.2 正規化測試、m-1.2 型別 |
| `backend/tests/ingestion/sec_dense_pipeline/integration/conftest.py` | m-1.3 client fixture、m-1.5 imports |
| `backend/tests/ingestion/sec_dense_pipeline/integration/test_ingest.py` | B-1.3 empty-filing test、m-1.3、m-1.5 |
| `docs/file_structure.md`、`backend/README.md`、`README.md` | m-1.4 structure maps |
| `CONTEXT.md` | glossary 同步(實作階段完成,review 兩輪未再修正) |

## Learning Notes

### 採用的工程策略

- **「guard 放在 mutation 之前」的失敗語意設計**(B-1.3):committed-or-absent 不只靠 marker 的寫入順序,更靠把 validation 提到第一個 side effect 之前 — 最終版連 collection 都不會建立,讓「absent」是字面意義的 absent。
- **Contract boundary 正規化一次、內部信任**(B-1.2 vs M-1.1 的對照):同一輪 review 裡,`item` 正規化被裁定「該做」(輸入形狀是本模組公開 contract 的責任)而 prelude size cap 被裁定「不該做」(invariant 由上游 producer 保證)。分界線:**這個保證的單一定義點在誰家** — 在自己家門口的(輸入正規化)要做,在上游已有 gate 的(prelude validity)不重複。
- **Reachability 例外的先例鏈**(M-1.2):DEV-132(schema 分支無 producer)→ DEV-141(helper 無 caller)→ 本票(ingest 無 caller),同一模式第三次出現 — tracer-bullet 分片下「infra 先行、明文 ratify、指名首發 caller」已成 repo 的 case law。

### 權衡取捨

- **預期 vs 實際 — Codex cross-model review 的價值與成本**:round 1 的 3 個 Blocking 中 2 個(B-1.2/B-1.3)是真 bug、被同 model 的實作+spec 軸都漏掉,cross-model isolation 確實抓到不同盲點;成本是 round 2 連續兩次 Codex dispatch hang(各 20-30 分鐘零活動),最終依 skill fallback 規則改用 Claude 確認輪 — cross-model 用在「找問題」的輪次,確認輪用 same-model 是可接受的 degraded mode。
- **Review 視野邊界**(M-1.1):reviewer 只看得到 main + 本 diff,看不到還沒 merge 的上游票(DEV-133 的 gate),因此把上游已解的問題歸咎到下游。教訓:coexistence/平行開發期間,round 2+ 的 reviewer prompt 要主動餵入「在途上游 PR」的 contract 證據。

### 關鍵收穫

- **Schema-valid ≠ 實際會發生**:B-1.2/B-1.3 都源自「frozen schema 允許、現行 producer 不會產生」的輸入。公開 contract 的防禦以 schema 允許的空間為準,不以現任 producer 的行為為準 — 但防到 schema 邊界為止(M-1.1:schema 之上的語意 invariant 屬 producer)。
- **例外要付「明文化税」**:M-1.2 的裁決不是「規則不適用」而是「適用、且照先例繳明文 ratify 的税」— issue description + PR body 記載,讓下一輪 reviewer(人或 model)能核對而非重新論證。
- **新增公開行為時同步 audit 公開面**(m-2.1):B-1.3 在 submodule 加了 `EmptyIngestError` 但 package `__init__` 沒跟上 — fix round 改了 contract 的可觀察行為時,export surface 是 checklist 的一項,不是事後發現的驚喜。
