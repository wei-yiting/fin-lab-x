# Code Review Round 1

> Reviewer: gpt-5.6-sol | Date: 2026-08-11

## Summary

| Metric | Count |
|--------|-------|
| Total issues | 12 |
| Blocking | 3 |
| Major | 3 |
| Minor | 5 |
| Suggestion | 1 |
| Library checks | 3 |

## Issues

### [Blocking] B-1.1: 並行 ingest 會留下缺漏或混合的 committed 資料
- **File:** `backend/ingestion/sec_dense_pipeline/vectorizer.py` L86
- **Problem:** Marker 沒有 ingest attempt identity，也沒有序列化相同 `(ticker, fiscal_year)` 的操作。可能發生 A upsert 第一批、B 寫入 `pending` 並 wipe、A 寫入剩餘批次與 `complete`、B 隨後失敗；此時 retrieval 看到 `complete`，但 A 的第一批已遺失。不同 filing 輸入也可能形成 stale-mixed chunks。這直接違反 committed-or-absent invariant 與 `docs/design-envelope.md` §1 的同 ticker concurrency 要求。
- **Fix:** 在任何 Qdrant mutation 前，針對相同 `(ticker, fiscal_year)` coalesce 或明確拒絕並行 ingest。新增可控制 interleaving 的測試，涵蓋一個 attempt 在另一個分批 upsert 期間 wipe 或失敗的情況。

### [Blocking] B-1.2: Payload 的 `item` 未在 contract boundary 正規化
- **File:** `backend/ingestion/sec_dense_pipeline/chunking.py` L87
- **Problem:** 程式直接寫入 `"item": item.item`。`StructuredItem.item` 與 `FlatItem.item` 都只是未受限制的 `str`，因此 `"7A"`、`" 7a "` 等 schema-valid 輸入會產生非 normalized payload，破壞 `item` index/filter contract。現行 parser 剛好輸出小寫，並不足以保證公開的 `ingest_filing(ParsedFiling)` contract。
- **Fix:** 每個 Item 只正規化一次，優先重用 `sec_core.parse_item_number()`，並將結果同時用於 payload 與 `header_path`。新增 mixed-case、前後空白的 schema-valid 測試。

### [Blocking] B-1.3: 零 chunks 的 filing 仍可能被標記為 `complete`
- **File:** `backend/ingestion/sec_dense_pipeline/vectorizer.py` L125
- **Problem:** Frozen schema 允許 `ParsedFiling(items=[])`、空的 `FlatItem.text` 或空的 `Block.text`。這些輸入可產生空 `payloads`；pinned embedding implementation 對空 batch 回傳空 list，之後沒有 content upsert，但程式仍在 L141–154 寫入 `complete` marker。Retrieval 會把空 corpus 當成成功 ingest，形成 silent empty answer，而非 committed-or-absent。
- **Fix:** 在任何 marker/wipe mutation 前先建立並驗證 payloads；零 chunks 時拋出可由 caller 映射為 legible failure 的 SEC-domain error。新增空 items、空白 text 與 rerun 時空輸入的測試，確認不會產生 `complete` marker。

### [Major] M-1.1: Prelude denormalization 違反 repository evidence gate
- **File:** `backend/ingestion/sec_dense_pipeline/chunking.py` L68
- **Problem:** `prelude = item.prelude or None` 隨後在 L70/L89 原封不動複製到每個 chunk，沒有 size cap 或 per-item quality gate。現行 `docs/design-envelope.md` §0 明確把這個 always-on prelude payload 設計列為失敗 precedent。這會把可能有雜訊或無界的文字放大寫入 Qdrant，並暴露為 retrieval context。
- **Fix:** 在 producer/detection 層落實 authoritative evidence guards，並以 contract tests 證明只有有效 prelude 能到達 ingest；否則暫停寫入 `prelude`。若較新的 research 已推翻現行 §0 規則，必須先透過明確 PR 更新 design envelope，不能由本 implementation 默默繞過。

### [Major] M-1.2: 新 production pipeline 在 merge 時不可達
- **File:** `backend/ingestion/sec_dense_pipeline/vectorizer.py` L66
- **Problem:** `ingest_filing` 沒有任何 non-test caller。Batch script、JIT retriever 與 eval path 仍使用 `sec_dense_pipeline_html`；新 package 只有自身 tests 與 re-export 引用。`check_commit_marker_complete` 同樣只有測試 consumer。這違反 `docs/design-envelope.md` §0 reachability rule，也符合 unused production code 的 Major maintenance smell。
- **Fix:** 在本 changeset 加入實際的 non-frozen batch 或 JIT consumer，連同 error、trace 與 marker contract 一起 wiring；否則延後加入整個 package。若只 wiring ingest，仍應移除尚無 retrieval consumer 的 public helpers。

### [Major] M-1.3: JIT ingestion 缺少必要 tracing
- **File:** `backend/ingestion/sec_dense_pipeline/vectorizer.py` L66
- **Problem:** `ingest_filing` 執行 collection bootstrap、marker mutation、wipe、chunking、embedding 與 batch upsert，但整個新 module 沒有 `traced_span()`。`docs/design-envelope.md` §4 要求 user-facing JIT ingestion fully traced，且 failure 必須能只靠 trace 歸因。Frozen baseline 已針對 chunking、embedding、upsert 建立 spans；新路徑失去這項 production-grade 能力。
- **Fix:** 在未來 outer JIT trace 下，為 chunking、embedding 與 Qdrant mutation 加入最小必要的 nested spans，記錄 failure category 與有界摘要。不要加入 §3 禁止的 per-retry event stream 或 throughput ceremony。

### [Minor] m-1.1: Embedding cleanup 依賴 private vendor attribute
- **File:** `backend/ingestion/sec_dense_pipeline/vectorizer.py` L61
- **Problem:** `embed_model._aclient` 是 pinned package 的 `PrivateAttr`，不屬於 documented `OpenAIEmbedding` API。相容性升級只要重新命名或移除此欄位，就會使每次 embedding request 在 cleanup 階段失敗。
- **Fix:** 透過 public `async_http_client=` constructor parameter 注入 caller-owned async HTTP client，再由 caller 明確關閉；或採用官方 documented lifecycle。不要直接讀取 `_aclient`。

### [Minor] m-1.2: 核心 payload contract 被抹平成 `dict[str, Any]`
- **File:** `backend/ingestion/sec_dense_pipeline/chunking.py` L46
- **Problem:** Possible Primitive Obsession/Data Clump：`build_chunk_payloads(...) -> list[dict[str, Any]]` 把本 module 宣告的完整 payload schema 表達成 untyped bag，之後 `vectorizer.py` 再用 string keys mutation/index。這讓缺欄位、改名或錯誤型別逃過 static checking，違反 repository 的 strict typing 規則。
- **Fix:** 為 payload 定義 `TypedDict`。可用 `NotRequired` 表達 vectorizer 才加入的 `ingested_at`，或區分 draft/final payload types，並讓 fixtures 與 helper returns 使用相同型別。

### [Minor] m-1.3: Integration tests 未關閉 Qdrant clients
- **File:** `backend/tests/ingestion/sec_dense_pipeline/integration/test_ingest.py` L30
- **Problem:** `_client()` 在各 test 建立新的 `QdrantClient`，但從未關閉；`integration/conftest.py` L42 的 cleanup client 也相同。刪除 collection 不會關閉 HTTP/gRPC transports，重複執行可能累積資源並產生 teardown warnings。
- **Fix:** 建立 yielding `QdrantClient` fixture，以 `try/finally: client.close()` 管理生命週期，並讓 setup、assertions 與 cleanup 共用它；或使用 client context manager。

### [Minor] m-1.4: Authoritative repository structure maps 已過期
- **File:** `docs/file_structure.md` L59
- **Problem:** Repository layout SSOT 在 L63–65 未列出 `sec_text_pipeline` 與新增的 `sec_dense_pipeline`，L89 的 test map 也漏掉兩者。`backend/README.md` L13 與 root `README.md` L238–241 同樣只描述 frozen HTML paths，使 contributor 無法從 authoritative docs 理解 coexistence boundary。
- **Fix:** 更新 `docs/file_structure.md` 的 ingestion 與 test maps，再同步 root/backend 的簡版 map，並明確標示 `_html` modules 是 frozen baselines。

### [Minor] m-1.5: Test modules 使用沒有正當理由的 lazy imports
- **File:** `backend/tests/ingestion/sec_dense_pipeline/integration/conftest.py` L22
- **Problem:** `_EMBED_DIM`、L40 的 `QdrantClient`，以及 `test_ingest.py` L157 的 `_EMBED_DIM` 都放在 function 內 import，但不符合 circular import、optional dependency、昂貴 module side effect 或 documented test-patching seam 的任何例外。
- **Fix:** 將這些 imports 移到 module scope。`patch(...)` 的 string target 本身已提供 runtime symbol resolution，不需要 lazy import。

### [Suggestion] S-1.1: Module README 未說明實際 configuration 與 extension contract
- **File:** `backend/ingestion/sec_dense_pipeline/README.md` L9
- **Suggestion:** 增加 Environment Variables table，涵蓋 `SEC_TEXT_QDRANT_COLLECTION`、`SEC_CHUNK_SIZE`、`SEC_CHUNK_OVERLAP`、`SEC_EMBED_MODEL`、`SEC_EMBED_DIM` 與 `QDRANT_URL`。目前 README 把 512/50 呈現為固定 contract，但 runtime 可以 override。另補充 payload filter field 變更必須同步調整 payload construction、index bootstrap、marker exclusion 與 retrieval。

## Documentation Gaps

| Folder | Missing |
|--------|---------|
| `backend/ingestion/sec_dense_pipeline/` | Environment-variable contract，以及 payload/index/retrieval extension guidelines |
| `docs/` | Authoritative structure map 未列出新的 text/dense pipelines 與對應 tests |

## Official Standards Check

| Library | Version | API Used | Status | Notes |
|---------|---------|----------|--------|-------|
| qdrant-client | 1.17.1 | `collection_exists`, `create_collection`, `create_payload_index` | ✅ Current | 使用 current APIs；library 沒有 ensure-index helper，因此 application-level already-exists handling 合理。未使用 deprecated `recreate_collection`。 |
| llama-index-embeddings-openai | 0.6.0 | `OpenAIEmbedding(..., dimensions=...)`, `aget_text_embedding_batch`, private `_aclient` | ❌ Wrong | Constructor 與 async batch APIs 是 current，且已內建 retry；但 `_aclient` 是 unsupported private state。 |
| langchain-text-splitters | 1.1.2 | `RecursiveCharacterTextSplitter.from_tiktoken_encoder` | ✅ Current | 正確使用 documented token-counting factory 實作 512/50 token chunking。 |

---

# Spec Conformance Round 1

> Reviewer: claude (model unknown) | Date: 2026-08-11

## Summary

| Metric | Count |
|--------|-------|
| Total findings | 0 |
| Missing | 0 |
| Scope creep | 0 |
| Misimplemented | 0 |

## Findings

None. The changeset was cross-checked line-by-line against DEV-135's "## What to build," all four "## Acceptance criteria" checkboxes, and the three "## 實作裁決紀錄" decisions (verified against DEV-127 for the field-list rationale and DEV-132 for the frozen `ParsedFiling` schema). No missing requirement, no misimplementation, and no unrequested behaviour was found.

Notable things specifically checked and cleared:

- `grep -rn "sec_dense_pipeline_html\|_html\b"` inside `backend/ingestion/sec_dense_pipeline/` returns only comment/docstring mentions explaining *why* it does not import the frozen tree — no actual `import` statement touches `sec_dense_pipeline_html`.
- `grep -rn "retry_transient"` across the new module and its tests returns nothing; `vectorizer.py`'s docstring explicitly states the rationale (embedding client's internal tenacity retry), matching decision (a) verbatim.
- `grep -rn '"year"'` returns nothing in the new tree; `fiscal_year` is used consistently in `chunking.py` (payload field), `vectorizer.py` (marker payload + function params), `collection_schema.py` (payload index), and `common.py` (marker ID composition) — decision (c) honored end-to-end with zero drift.
- The one helper not literally present in the frozen baseline (`marker_status_condition()` in `backend/ingestion/sec_dense_pipeline/common.py`) was evaluated as possible scope creep against decision (b)'s explicit helper list (`commit_marker_id` / `check_commit_marker_complete` / `canonicalize_ticker` / ensure-collection). It was judged plumbing, not creep: it exists to satisfy the AC line "檢索 query 排除 marker point" by giving ingest-side wipe and future retrieval-side queries a single shared definition of "what a marker point looks like," directly serving the stated purpose ("the marker helpers consumed by the retrieval side" per `__init__.py`'s docstring) rather than adding an unrequested capability.

## Covered Requirements

- ✅ `ingest_filing(filing: ParsedFiling)` consumes the structure directly, no markdown intermediate — `backend/ingestion/sec_dense_pipeline/vectorizer.py` L66
- ✅ Per-block chunking, RecursiveCharacterTextSplitter token-based 512/50, overlap never crosses block boundary — `backend/ingestion/sec_dense_pipeline/chunking.py` L33-38, L73-95; proven by `backend/tests/ingestion/sec_dense_pipeline/unit/test_chunking.py::test_chunk_boundaries_never_cross_blocks` and `::test_adjacent_chunks_within_a_block_overlap`
- ✅ FlatItem and reclassified leading block enter the chunk flow like any other block — `chunking.py` L64-71 (`units` list construction); proven by `test_block_heading_is_none_for_flat_and_reclassified_leading_block`
- ✅ New Qdrant collection with full payload schema + payload indexes — `backend/ingestion/sec_dense_pipeline/collection_schema.py` L18-29
- ✅ Normalized `item`, `block_heading`, `prelude`, `header_path` (drop Part) — `chunking.py` L60-91; proven by `test_header_path_format_without_part_level`
- ✅ Filing-wide `chunk_index` — `chunking.py` L58, L91-95; proven by `test_chunk_index_is_filing_wide_and_gapless`
- ✅ Citation triple `accession_number` / `cik` / `primary_document` denormalized per chunk, no URL stored — `chunking.py` L84-86; proven by `test_every_payload_has_full_field_set_including_citation` and `integration/test_ingest.py::test_ingest_writes_full_payload_and_completes_marker`
- ✅ `prelude = None` correctly expressed for FlatItem / reclassified leading block — `chunking.py` L66-71; proven by `test_prelude_is_none_for_flat_and_reclassified_items` and the integration equivalent
- ✅ Commit marker lifecycle `pending` → `complete`, wipe resets the marker, retrieval excludes marker points — `vectorizer.py` L86-154, `common.py` L36-47; proven by `test_wipe_before_rerun_clears_chunks_and_resets_marker` and `test_content_queries_exclude_the_marker_point`
- ✅ Mid-ingest failure ⇒ committed-or-absent from the retrieval side — `vectorizer.py` (no exception swallowing around `_embed_texts`); proven by `test_mid_ingest_failure_is_absent_to_readers`
- ✅ Decision (a): no `retry_transient` wrapper inside `ingest_filing` — confirmed absent via grep; rationale documented in `vectorizer.py` module docstring
- ✅ Decision (b): marker/ticker/collection-bootstrap helpers duplicated into `sec_dense_pipeline/`, not imported from `_html`, not promoted to `backend/common/` — `common.py`, `collection_schema.py`; confirmed via grep for `_html` imports
- ✅ Decision (c): payload field `fiscal_year` (not `year`), consistent across payload/index/marker — `chunking.py`, `vectorizer.py`, `collection_schema.py`, `common.py`; confirmed via grep for stray `"year"`
- ✅ CONTEXT.md glossary sync (Filing store, header_path) — `CONTEXT.md` diff
