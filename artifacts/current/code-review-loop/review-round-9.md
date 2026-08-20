# Code Review Round 9 (post-convergence envelope review)

> Reviewer: Claude Fable 5 (`/code-review` high effort, envelope-focused) | Date: 2026-08-20
>
> 本輪不是 code-review-loop 的續行（loop 已於 round 8 收斂），而是使用者指定的獨立
> review pass：「依照 repo document（尤其 `docs/design-envelope.md`）review 目前
> worktree 的 code change 有沒有 over-engineering 的問題」。
> 流程：8 個平行 finder angles（3 correctness + reuse/simplification/efficiency +
> altitude + conventions）產出 27 個 candidates，去重後 13 組逐一由獨立 verifier
> 對照 code 與 envelope 驗證（recall-biased、1-vote）。

## Summary

| Metric | Count |
|--------|-------|
| Total findings | 10 |
| Correctness | 2 |
| Over-engineering (envelope §7 Major) | 3 |
| Under-engineering (§4 zone, 需 gate 決定) | 1 |
| Cleanup (reuse / efficiency / altitude / conventions) | 4 |
| Refuted candidates（驗證後駁回） | 2 |

整體評估：over-engineering 問題**主要集中在測試與 retry 機制**，而非 production
邏輯本身；另有兩個 correctness 問題與一個 §4 tracing 缺口需在 human gate 決定。

## Findings

### F-9.1 — CI 環境變數使新測試紅燈 ⛔ Blocking / Correctness — CONFIRMED（已本地重現）

- **位置**: `backend/tests/ingestion/sec_dense_pipeline/integration/test_search.py:63`（缺 conftest fixture）
- CI 在 `.github/workflows/ci.yml:42` export `SEC_DISABLE_JIT=1`，但新 pipeline 的
  test conftest 缺少 frozen `_html` suite 已有的 `_unset_disable_jit` autouse fixture
  （`backend/tests/ingestion/sec_dense_pipeline_html/integration/conftest.py:19`）。
- 本地重現：`SEC_DISABLE_JIT=1 pytest .../unit/test_retriever.py` → 2 failed
  （`test_ensure_ingested_returns_false_on_marker_miss_after_jit`、
  `test_ensure_ingested_recheck_after_claim_catches_completed_race`，
  `JITDisabledError` at `retriever.py:259`）；3 個 integration cold-path tests 在
  `-m integration` job 下同樣失敗。**PR merge 時 CI 會紅燈。**

### F-9.2 — Cold path embedding 失敗誤分類 🔴 Major / Correctness — CONFIRMED

- **位置**: `backend/ingestion/sec_dense_pipeline/retriever.py:433`
- JIT ingest 中 OpenAI embedding 失敗時，`ingest_filing_with_retry` 只重分類 Qdrant
  例外（`ResponseHandlingException` at `vectorizer.py:285`、`UnexpectedResponse` at
  `:291`），openai SDK 例外原樣傳播到 `search()` 的 generic `except Exception`
  （`retriever.py:432-433`）→ 變成 `CorpusUnavailableError`；同樣失敗在 query-embed
  步驟卻是 `EmbeddingServiceError`（`retriever.py:389-391`）。違反 envelope §4
  failure-taxonomy attribution；內部 bug（AttributeError/TypeError）也會被誤報為
  corpus unavailability。

### F-9.3 — Qdrant retry 的 transient-source taxonomy 超出 §2 🔴 Major / Over-engineering — CONFIRMED

- **位置**: `backend/ingestion/sec_dense_pipeline/vectorizer.py:249`
- ~70 行分類機器（`_TRANSIENT_SOURCE_TYPES` 區分 httpx `RemoteProtocolError` vs
  `LocalProtocolError`、`exc.source` isinstance 檢查、5xx/4xx split）+ 10 個專屬測試。
- Envelope §2 只授予 external APIs（EDGAR、Finnhub、LLM providers）single retry；
  localhost Qdrant 屬 restart-and-rerun。改動前的 docstring 原文即為
  "No retry wrapper here… re-running a failed ingest is the recovery path"。
  5 個測試分別 pin httpx 子類別（其中 3 個走同一 isinstance branch），觸犯 §5 rule 1。
- **建議修法（§7：deletion is a fix）**：刪除 wrapper（commit-marker 語意已讓失敗的
  ingest 等同沒 ingest），或保留一次 blanket retry on
  `ResponseHandlingException`/5xx + §9 一行註記 — 不要 source-type taxonomy，測試縮到 ~2 個。

### F-9.4 — 測試量超出 §5 envelope 🔴 Major / Over-engineering — CONFIRMED

- **位置**: `backend/tests/ingestion/sec_dense_pipeline/unit/test_retriever.py:56`
- 四項驗證屬實：
  1. `test_release_ingest_slot_is_idempotent`（line 82）pin 的是 stdlib `set.discard`
     的 never-raises 語意（§5 rule 1，frozenset case law）。
  2. missing `ingested_at`/`block_heading`/`prelude` 三種 payload 缺鍵狀態在
     `_point_to_chunk`（KeyError, lines 143-166）與 full `search()`
     （CorpusUnavailableError, lines 852-919）兩層重複測，全部走同一個 mapping
     （`retriever.py:404-421`）；§5 標準是 one legible-failure case。
  3. 兩個 ~35 行測試（lines 553-621）assert logger.info 的完整字串，行為已被相鄰
     測試的 parse-called assertions pin 住。
  4. 17 個 `search()` 測試 inline 重建同一組 AsyncQdrantClient/ensure/marker/
     `_embed_texts` patch stack，無 conftest fixture（§5 rule 3，`_good_info()` 先例）。
- Diff 新增 1,680 test lines vs 769 production lines = **2.18×**，超過 §5 rule 5 的
  ~2× 門檻 → PR body 需要一句 justification（或刪掉上述違規測試讓 ratio 回落）。

### F-9.5 — Cutover 後文件互相矛盾、且無 production caller 🔴 Major / Conventions — CONFIRMED

- **位置**: `backend/ingestion/sec_dense_pipeline/README.md:13`
- 新 README 宣稱新 `search()` 是 "the single JIT query entry point"，但 `AGENTS.md`、
  `docs/file_structure.md:64`、`docs/observability.md:43`、
  `docs/agent_architecture.md:192` 仍把 RAG retrieval 與 batch CLI 綁在 frozen `_html`
  pipeline。唯一真實 caller（`backend/evals/eval_tasks.py:153`）仍 import `_html`
  retriever；agent_engine 沒有 RAG tool（`sec_filing_tools.py:91` 標 "planned"）——
  **routing cutover 在 code 中不存在**。
- 併發的 operator trap：`embed_sec_filings.py` 被改指到 `SEC_TEXT_QDRANT_COLLECTION`，
  cutover 前的 shell-history 指令會 exit 0 卻灌錯 collection（A/B eval 讀的是 `_html`
  baseline collection），而 `docs/observability.md` 仍指示 operator 用該 script 餵
  `_html` vectorizer。
- **修法**：本 PR 內 reconcile 四份文件。

### F-9.6 — 新 JIT `search()` 無 tracing（§4 zone）🔴 Major / Under-engineering — CONFIRMED（需 gate 決定）

- **位置**: `backend/ingestion/sec_dense_pipeline/retriever.py:291`
- 整條 user-facing JIT path（EDGAR parse → embed → Qdrant ingest）只有一行
  `logger.info`（line 378）；被替換的 frozen baseline 帶 `@observe(name="sec_retrieval")`。
  §4 要求 user-query-triggered JIT ingestion fully traced；§7 rule 1：§4 zone shortcut = Major。
- Deferral（DEV-161）只記錄在 `backend/scripts/README.md:28` 與 review-loop artifacts
  （後者 pre-PR 會 untrack），無 ADR；也沒有機制保證 DEV-161 先於 agent tool 接線
  （DEV-142）落地。
- 緩和事實：目前尚無 production caller 走到這條 path。
- **依 repo 規則（user-only-waives），此項 deferral 是否成立由作者在 gate 決定** —
  本 review 僅 surface，不代為接受。

### F-9.7 — Sync marker check 無 production caller（§0 reachability）🟡 Minor / Over-engineering — CONFIRMED

- **位置**: `backend/ingestion/sec_dense_pipeline/common.py:57`
- Diff 新增 async 版之後，sync `check_commit_marker_complete` + `_marker_is_complete`
  drift-guard helper 只剩測試 assertion 在用（`__init__.py:14` re-export、
  `unit/test_common.py:24`、integration assertions）；production paths 全是 async
  （`retriever.py:252,277`、`vectorizer.py:117`）。Frozen `_html` 有自己的 copy，
  freeze 不要求保留。
- **修法**：合併為單一 async function（predicate inline）；integration tests 改用
  手上已有的 raw qdrant client `retrieve()` 斷言。

### F-9.8 — 每次 query 4 個 ensure-collection round-trips 🟡 Minor / Efficiency — CONFIRMED

- **位置**: `backend/ingestion/sec_dense_pipeline/retriever.py:364`
- `async_ensure_collection_and_indexes`（`collection_schema.py:50-77`）無 early return：
  collection 已存在時仍是 1 次 `collection_exists` + 3 次無條件 `create_payload_index`
  （吞掉 "already exists" 400 當 flow control）——每個 hot query 都付 4 round-trips；
  cold path 在 `ingest_filing`（`vectorizer.py:117-121`）再 ensure 第二次。
  Read-only query 會 mutate store（建立空 collection），bootstrap ownership 模糊。
- **修法注意**：ensure 目前在 fresh deployment 上是 load-bearing（marker retrieve 會
  404 → `CorpusUnavailableError` 而非觸發 JIT，`retriever.py:425-430`），移除時必須
  同時把 marker-check 404 視為 cache miss。淨效果是刪碼 + 一個 except clause。

### F-9.9 — Payload 欄位三重列舉 🟡 Minor / Reuse — CONFIRMED

- **位置**: `backend/ingestion/sec_dense_pipeline/retriever.py:220`
- 14 個 chunk payload 欄位在 `chunking.ChunkPayload`、`Chunk` model、
  `_point_to_chunk` 手寫 `payload[...]` 三處列舉。已驗證
  `Chunk(**payload, score=point.score)` 是 drop-in：欄位名完全一致、pydantic v2
  extra keys ignored、marker points 已被 `must_not` 過濾（`retriever.py:201`）、
  caller 已把 ValueError+KeyError 一起 map 到 `CorpusUnavailableError`
  （`retriever.py:407-421`，pydantic `ValidationError` 是 `ValueError` 子類）。
  只需同步更新兩個 pin raw KeyError 的 unit tests（`test_retriever.py:143,156`）。

### F-9.10 — EDGAR retry wrappers 放錯 altitude 🟡 Minor / Altitude — CONFIRMED

- **位置**: `backend/ingestion/sec_dense_pipeline/vectorizer.py:210`
- `resolve_latest_fiscal_year_with_retry` 包私有 `sec_core._resolve_latest_fiscal_year`、
  `parse_filing_with_retry` 包 parser，都放在 vectorizer（ingest）模組 —
  `retriever.py:40-41` 與 `embed_sec_filings.py:30-31` 因此從 vectorizer import
  EDGAR-parse retry（依賴方向錯誤）。同時 `sec_filing_tools.py:128,237` 直接呼叫
  無 retry 的私有函式：同一個 EDGAR call 在 JIT path 有 §2 retry、在 agent-tool path
  沒有，且無任何 ADR 記載此不對稱（tool path 為 pre-existing，非本 diff regression）。
- **修法**（AGENTS.md freeze 明文允許 "new capabilities are added as new functions"）：
  在 `backend/common/sec_core.py` 加 public 帶 retry 的 `resolve_latest_fiscal_year`；
  `parse_filing_with_retry` 放到 `sec_text_pipeline/parser.py`（該 tree 只凍結
  `ParsedFiling` schema）。所有 caller 共用一個 §2 policy point。

## Refuted Candidates（驗證後駁回，記錄以免重複提出）

| Candidate | 駁回理由 |
|-----------|----------|
| `_validate_filters` 驗證階梯是 over-engineering | Envelope §3 明文：「basic type/shape/size validation at any boundary belongs to §4 and is never excluded」；`search()` 的預期 caller 是 LLM tool call（untrusted runtime dict）。legacy `year` key rejection 防的是 `_html` contract（`filters.get("year")`）遷移時 silent wrong-year 的真實 hazard，非 speculative generality。mandatory-ticker 有 A/B eval 數據背書（naive ticker_precision@10 = 0.00）。 |
| `check_commit_marker_complete` contract narrowing（missing collection 從 return False 改為 raise）是意外行為變更 | 新 docstring（`common.py:60-68`）明文記載 propagation 是刻意設計；刪除的 integration assertion 被 comment + 新 unit tests（`unit/test_common.py:20-32`）取代，coverage 是搬移非流失；repo 內無 non-test caller 會在 fresh Qdrant 上踩到。 |

另有低優先 mention-once 項（§7.4，不列入 findings）：cold-path 兩行序列在
`embed_sec_filings.py:52-55` 與 `retriever.py:282-285` 逐字重複、
`SEC_DISABLE_JIT` 判斷在 `retriever.py:258/355` 兩處各自 hand-rolled、
`_embed_texts` 每次呼叫新建 OpenAI client（frozen baseline 同 pattern，非本 diff 新增）、
新測試函式 43 個皆無 type annotations（AGENTS.md §3.1）。

## Verification Method

- Diff 範圍：`main...HEAD`（排除 `artifacts/`），2,918 行。
- Phase 1：8 個平行 finder subagents（每角度上限 6 candidates），全部先讀
  `docs/design-envelope.md` 並以 § 編號引用。
- Phase 2：13 組去重後 candidates 各派 1 個獨立 verifier subagent
  （CONFIRMED / PLAUSIBLE / REFUTED，recall-biased）；F-9.1 由 reviewer 本人以
  `SEC_DISABLE_JIT=1 pytest` 直接重現。
- 存活的 10 項 findings 全數 CONFIRMED；2 項 REFUTED 如上表。

---

## Discussion Gate Outcome (Round 9)

Orchestrator independently verified the key claims before this gate (reproduced F-9.1
locally with `SEC_DISABLE_JIT=1 pytest` → 2 failed; grep-confirmed F-9.7's sync
marker-check has no production caller; verified against installed packages for the F-9.3
question: LlamaIndex `OpenAIEmbedding` has built-in tenacity retry (`max_retries=10`
default) while qdrant-client's transport has **zero** retry logic — it only reads the
429 `Retry-After` header into an exception message without acting on it).

Resolutions, discussed with the user:

| Finding | Resolution |
|---|---|
| F-9.1 (CI env breaks tests) | **Fix** — Blocking, reproduced firsthand. |
| F-9.2 (cold-path embedding misclassification) | **Fix** — taxonomy inconsistency confirmed. |
| F-9.3 (retry taxonomy over-engineering) | **Fix, option B (user decision)** — keep the wrapper (the ticket's ratified AC explicitly assigns Qdrant-boundary retry to this ticket, and qdrant-client has no built-in retry), but replace the ~70-line source-type taxonomy with a blanket single retry on `ResponseHandlingException` + `UnexpectedResponse` 5xx; tests reduced accordingly. Option A (delete entirely) rejected: it would silently waive a ratified AC. Embedding stays unwrapped — the framework already retries it (SP-1.5 embedding-half dismissal stands). |
| F-9.4 (test volume) | **Fix as reported** — delete the stdlib-pinning test, dedupe the two-layer missing-key coverage, trim full-string log assertions to key fields (the log channel itself is AC-mandated and stays), extract a shared patch-stack fixture. |
| F-9.5 (docs) | **Split**: the "no production caller / routing cutover 不存在" half re-litigates round 1's M-1.1, already dismissed by user decision — stands dismissed. The documentation half is new and valid: fix `docs/observability.md`'s now-wrong operator instructions, reconcile `docs/file_structure.md`/`docs/agent_architecture.md` statements this PR invalidated, and soften the new README's premature "single JIT query entry point" claim. |
| F-9.6 (tracing) | **Dismissed (standing user decision)** — re-raises round 1's M-1.6; the deferral is recorded in Linear (the repo's SSOT for work state), DEV-161 blocked-by DEV-160. |
| F-9.7 (sync marker check unreachable) | **Fix** — merge to async-only. |
| F-9.8 (4 round-trips) | **Deferred / mention-once** — envelope §1 (<1 QPS) makes the cost a non-issue; the proposed fix also partially conflicts with M-2.4's propagate-don't-swallow decision (would require re-treating missing-collection 404 as a cache miss). Not actioned in this PR. |
| F-9.9 (`Chunk(**payload)`) | **Fix** — verified drop-in; strictly better than the field-by-field bracket-access approach rounds 4–6 iterated into. |
| F-9.10 (retry wrappers' module placement) | **Fix** — move to the modules that own the wrapped concerns; the agent-tool path's missing retry is pre-existing and stays out of scope. |
