# Code Review Round 1

> Reviewer: gpt-5.6-sol | Date: 2026-08-19

## Summary

| Metric | Count |
|--------|-------|
| Total issues | 9 |
| Blocking | 1 |
| Major | 6 |
| Minor | 1 |
| Suggestion | 1 |
| Library checks | 1 |

## Issues

### [Blocking] B-1.1: Production search allows unfiltered cross-ticker retrieval
- **File:** `backend/ingestion/sec_dense_pipeline/retriever.py` L205
- **Problem:** `filters` 可省略，而且 L213–214 明確允許裸搜整個 collection；`filters={"fiscal_year": 2024}` 也因 fiscal year 只在 ticker branch 內解析而被靜默忽略。這違反「每次檢索必須套用 ticker 與 resolved fiscal year」的 contract，也違反 design-envelope §4 的 API boundary 要求，會讓不同 ticker／年度資料混入結果。
- **Fix:** 要求 `filters` 必須包含合法 ticker；fiscal year 可省略但必須先 resolve，之後一律將 ticker 與 fiscal year 放入 Qdrant filter。拒絕未知或無效 filter shape。若 eval 需要全 collection search，建立明確隔離的 eval-only entry point，不要放寬 production contract。

### [Major] M-1.1: Cutover ships without any runtime consumer
- **File:** `backend/ingestion/sec_dense_pipeline/retriever.py` L205
- **Problem:** Repo-wide reference 檢查顯示新 `search()` 只被 tests import；現有 retrieval task 仍使用 frozen `_html` retriever，agent runtime 也沒有 consumer。因此本次變更沒有把新 retriever 接到任何真實流量，違反 design-envelope §0 Reachability Rule。更糟的是 batch CLI 已開始寫入新 collection，而目前可執行的 retrieval workflow 仍讀舊 collection。
- **Fix:** 將 retriever 與第一個真實 consumer／routing cutover 放在同一個可獨立運作的 changeset；若 DEV-142／DEV-164 尚未能一起交付，就延後這個 consumer-less module 與 batch cutover，避免 merge 一個無法被產品路徑觸達且會拆斷 operator workflow 的中間狀態。

### [Major] M-1.2: `SEC_DISABLE_JIT` incorrectly blocks hot-cache searches
- **File:** `backend/ingestion/sec_dense_pipeline/retriever.py` L243
- **Problem:** Flag 在 commit marker check 前直接拋出 `JITDisabledError`，所以已完整預載的 ticker/year 也無法搜尋。這與 `JITDisabledError` 自己的 docstring「requested ticker/year is not already ingested」及 cold-query guard contract 相衝突。
- **Fix:** 先解析明確 fiscal year 並檢查 complete marker；只有 marker miss、確實準備進入 JIT 時才檢查 `SEC_DISABLE_JIT`。補一個 flag 開啟但 marker complete 時仍能搜尋的 test。

### [Major] M-1.3: Retry wrapper classifies the wrong failure surface
- **File:** `backend/ingestion/sec_dense_pipeline/vectorizer.py` L218
- **Problem:** `AsyncQdrantClient(url=...)` 使用預設 REST transport；底層 Qdrant request 的 `httpx.ConnectError`／timeouts 會先被包成 `ResponseHandlingException`，所以 L220 的 raw `httpx.*` branch 不可能捕捉 Qdrant failure。它反而可能捕捉 OpenAI embedding 已耗盡自身 retries 後的 raw error，進而 retry 整段 ingest，形成刻意要避免的 stacked retry。同時 L222 將所有 `ResponseHandlingException` 都視為 transient，包括成功 HTTP response 的 Pydantic validation failure，造成永久性 schema 錯誤被錯誤 retry。
- **Fix:** 移除頂層 raw `httpx.*` catch；捕捉 `ResponseHandlingException` 後檢查 `exc.source`，只將指定的 connection/timeout 類型轉成 `TransientError`，其他原因原樣拋出。測試應模擬 Qdrant 實際包裝後的 exception，不應直接讓 mocked `ingest_filing()` 拋 raw `httpx` exception。
- **Context7:** qdrant-client REST `send_inner()` 會將底層 transport exceptions 包成 `ResponseHandlingException`；response validation errors 也使用同一 wrapper。HTTP 5xx 是 `UnexpectedResponse`，429 則是獨立的 `ResourceExhaustedResponse`。

### [Major] M-1.4: Latest-year EDGAR lookup bypasses the retry policy
- **File:** `backend/scripts/embed_sec_filings.py` L38
- **Problem:** `_resolve_latest_fiscal_year` 是 EDGAR network call，卻在 batch CLI 以及 `retriever.py` L255 直接執行，未經 `retry_transient`。因此省略 fiscal year 時遇到 `TransientError` 會零 retry，違反 design-envelope §2 的「external API failure single retry」要求；文件宣稱 cold path 有 single retry 也不完整。
- **Fix:** 提供一個由 `retry_transient` 包裝的 latest-year resolver，讓 JIT 與 batch 共用，並測試 transient-then-success 以及 permanent-error-no-retry。

### [Major] M-1.5: Concurrent JIT has a stale-marker race
- **File:** `backend/ingestion/sec_dense_pipeline/retriever.py` L183
- **Problem:** Marker miss 發生在 claim registry 之前。第二個 request 可能收到較舊的 miss 結果，但直到第一個 ingest 已完成並 release slot 後才恢復執行；它會成功 claim 並重做整個 ingest。沒有 `await` 介於 set membership check 與 insert，只能保證 registry 操作本身原子化，不能保證先前的 Qdrant cache observation 仍有效。這違反 design-envelope §1 對 same-key concurrent JIT 必須明確 resolve 的要求。
- **Fix:** 保留初次 fast marker check，但在成功 claim slot 後再次檢查 complete marker；若第一個 request 已完成就直接回報 cache hit，否則才 parse/ingest。新增能延遲第二個 marker response、讓它在第一個 release 後才繼續的 race test。

### [Major] M-1.6: User-facing JIT path has no required trace root
- **File:** `backend/ingestion/sec_dense_pipeline/retriever.py` L205
- **Problem:** 新 `search()` 只有一筆 `logger.info`，沒有 trace root、step spans 或 failure taxonomy attribution。Design-envelope §4 明定 user-facing JIT ingestion 必須完整 traced，並能從 trace 單獨判定 failure category。將 observability 拆到 DEV-161 不會讓目前這個「production routing cutover」符合 merge-time contract；`backend/scripts/README.md` L28 所稱 observability 已存在也不正確。
- **Fix:** 在 routing 生效前交付最低必要的 search trace root 與 fetch/parse/ingest/query attribution；若 DEV-161 必須維持獨立 PR，則先不要切 production routing，並讓兩者以不暴露未 traced path 的順序合併。

### [Minor] m-1.1: Session issue ID leaked into durable documentation
- **File:** `backend/ingestion/sec_dense_pipeline_html/README.md` L18
- **Problem:** `DEV-160` 對未參與該 ticket 的後續讀者沒有額外價值；描述性文字已足以說明 cutover。依 review contract，issue IDs 應留在 commit／PR metadata。
- **Fix:** 移除 `DEV-160`，保留「batch script now targets the structured-contract pipeline」的長期有效理由。

### [Suggestion] S-1.1: `_build_query_filter` returns unused speculative metadata
- **File:** `backend/ingestion/sec_dense_pipeline/retriever.py` L118
- **Suggestion:** `applied` 只被 tests assertion 使用；production caller 將 `applied_filters` 解構後完全不使用。這是 possible Speculative Generality，且 observability 已明確延後。現階段讓 helper 只回傳 `models.Filter`；等 tracing 真正需要 metadata 時再加入實際 consumer。

## Documentation Gaps

| Folder | Missing |
|--------|---------|
| `backend/ingestion/sec_dense_pipeline/` | 現有 README 的 Structure Map 未列出新的 `retriever.py`，也未說明 production search contract、cold/hot JIT flow、concurrency resolution、error mapping 與 retry boundaries。 |
| `backend/evals/scenarios/sec_retrieval/` | Setup instructions 仍要求用 `embed_sec_filings.py` 預載資料，但該 CLI 現在寫入新 collection，而現有 eval task 仍讀 frozen collection；需要可實際執行的 baseline/new-pipeline setup 說明或原子化 cutover。 |

## Official Standards Check

| Library | Version | API Used | Status | Notes |
|---------|---------|----------|--------|-------|
| qdrant-client | 1.17.1 | `AsyncQdrantClient.query_points`, `collection_exists`, `retrieve`; REST exception handling | ❌ Wrong | 三個 public method 的 signature 與用法皆為 current、非 deprecated；錯誤在 exception handling。預設 REST transport 會把 raw `httpx` request errors 包成 `ResponseHandlingException`，而目前 code 同時留下不可達的 Qdrant raw-error branch，並把 response validation failure 誤判成 transient。429 的 `ResourceExhaustedResponse` 不屬於 `UnexpectedResponse` 或 `ResponseHandlingException`。 |

---

# Spec Conformance Round 1

> Reviewer: gpt-5.6-sol | Date: 2026-08-19
> (Copy `gpt-5.6-sol` and `2026-08-19` verbatim — do not self-identify.)

## Summary

| Metric | Count |
|--------|-------|
| Total findings | 6 |
| Missing | 3 |
| Scope creep | 0 |
| Misimplemented | 3 |

## Findings

### [Blocking] SP-1.1: Public search path permits unfiltered collection-wide retrieval
- **Type:** Misimplemented
- **Spec:** "檢索必須帶 `ticker` + `fiscal_year` filter 條件（`query_filter=Filter(must=[FieldCondition(key="ticker", ...), FieldCondition(key="fiscal_year", ...)])`），不能是裸 vector search 打整個 collection。" (Acceptance criteria)
- **File:** `backend/ingestion/sec_dense_pipeline/retriever.py` L205
- **Problem:** `filters` is optional, calls without `ticker` proceed to `_build_query_filter(None, None)`, and `fiscal_year` supplied without `ticker` is silently ignored. The resulting query has no `must` conditions. Tests at `test_retriever.py` L54 and L222 explicitly preserve this forbidden behavior. The valid-path unit test does assert both conditions, but it does not prevent public calls from bypassing them.
- **Fix:** Require `ticker` for every `search()` call, resolve `fiscal_year` when omitted, and always construct exactly both mandatory conditions. Reject missing/invalid filter combinations and add unit tests against the actual `query_points(query_filter=...)` call, including rejection of unfiltered and fiscal-year-only calls.

### [Blocking] SP-1.2: GE-style individual source Item absence remains silently partial
- **Type:** Missing
- **Spec:** "Source-level missing Item → 結構化 legible error（非 silent empty）" (Acceptance criteria)
- **File:** `backend/ingestion/sec_dense_pipeline/retriever.py` L195
- **Problem:** The implementation only propagates `EmptyFilingError` when the entire filing has zero substantive Items. A GE-style filing where Item 1 is absent but other Items exist is still ingested, committed, and searched, potentially returning unrelated matches. The test at `test_retriever.py` L479 mocks a whole-filing zero-item error and therefore does not exercise the required failure shape. This is under-engineering in the envelope §4 JIT failure-legibility zone and conflicts with §2's committed-or-absent requirement.
- **Fix:** Detect the agreed source-level-missing condition before committing ingestion and raise a typed, actionable `FinLabError` identifying ticker, fiscal year, and missing Item(s). Add a GE-shaped test where other Items exist but Item 1 is absent, asserting no commit marker completion and no retrieval.

### [Blocking] SP-1.3: SEC_DISABLE_JIT rejects hot cache hits
- **Type:** Misimplemented
- **Spec:** "冷查詢（未 ingest ticker）端到端：fetch → parse → ingest → retrieve 回答；熱查詢直接命中。" (Acceptance criteria)
- **File:** `backend/ingestion/sec_dense_pipeline/retriever.py` L243
- **Problem:** The environment guard raises before checking the commit marker. Consequently, `SEC_DISABLE_JIT=1` rejects an explicitly identified `(ticker, fiscal_year)` even when it is already completely ingested, rather than allowing the required hot retrieval. Existing tests cover only a cold miss.
- **Fix:** Apply the guard only when a marker miss would trigger EDGAR/JIT work. Permit explicit-year complete-marker hits to retrieve normally, while ensuring omitted-year requests never call EDGAR when the flag is enabled. Add hot-hit-with-flag coverage.

### [Major] SP-1.4: Latest-year EDGAR resolution bypasses retry_transient
- **Type:** Missing
- **Spec:** "本票的 JIT fetch 路徑是 `retry_transient` 的首發預定使用者——不要另建第四套 retry。" (前置資產)
- **File:** `backend/ingestion/sec_dense_pipeline/retriever.py` L255
- **Problem:** Both `search()` and the batch script invoke `_resolve_latest_fiscal_year` directly. That resolver performs EDGAR metadata I/O and can raise `TransientError`, but these calls receive no single retry. Wrapping only `parse_filing` leaves the omitted-year fetch path partial, contrary to envelope §2's single-retry rule.
- **Fix:** Add one shared `retry_transient`-decorated latest-year resolver and use it from both retriever and batch paths. Test transient-then-success and permanent-error-no-retry behavior.

### [Major] SP-1.5: Embedding and Qdrant retry classification is incomplete
- **Type:** Missing
- **Spec:** "改寫 batch script 時，依 envelope §2 在 embedding/Qdrant client 邊界把可重試失敗分類為 `TransientError` 並納入 retry（DEV-141 review 記錄的已知 gap：舊外層 loop 移除後，embed/Qdrant 步驟暫以 manual retry 承接，正式解法歸本票）。" (前置資產)
- **File:** `backend/ingestion/sec_dense_pipeline/vectorizer.py` L204
- **Problem:** `ingest_filing_with_retry` classifies selected transport exceptions, but exhausted embedding failures are not classified as `TransientError`, and retryable Qdrant HTTP failures such as 5xx `UnexpectedResponse` are not covered. The implementation instead states that the embedding SDK's internal retry is relied upon, so `retry_transient` is not the complete boundary policy requested by the spec.
- **Fix:** Classify retryable embedding and Qdrant boundary failures as `TransientError`, including Qdrant 5xx responses, and route them through `retry_transient` as the single repo-owned retry policy. Configure underlying clients as necessary to avoid stacked retries and add boundary-specific tests.

### [Blocking] SP-1.6: Batch summary loses a successfully resolved year after later failure
- **Type:** Misimplemented
- **Spec:** "未指定年度時（caller 省略 `fiscal_year` / batch script 省略 `--fiscal-year`），latest-year 解析正確運作並回報 resolved year（見下方裁決紀錄）" (Acceptance criteria)
- **File:** `backend/scripts/embed_sec_filings.py` L77
- **Problem:** `_embed_one()` returns the resolved year only after parsing and ingestion both succeed. If latest-year resolution succeeds but parse or ingest then fails, `main()` records the original `args.fiscal_year` (`None`) and prints `?`, discarding the known resolved year from that ticker's summary.
- **Fix:** Preserve the resolved year independently of later parse/ingest success and include it in failed summary rows whenever resolution completed. Add a test for omitted `--fiscal-year`, successful resolution, and subsequent ingest failure.

## Covered Requirements

✅ Cold queries perform parse → ingest → retrieve in one call — `backend/ingestion/sec_dense_pipeline/retriever.py`

✅ Complete commit markers produce hot hits without parse or ingest when JIT is enabled — `backend/tests/ingestion/sec_dense_pipeline/integration/test_search.py`

✅ Filing-store cache and Qdrant commit marker jointly support the cold/hot path — `backend/ingestion/sec_text_pipeline/parser.py`

✅ `cache_hit` is observable and tested independently of tracing — `backend/tests/ingestion/sec_dense_pipeline/unit/test_retriever.py`

✅ Cold queries are prevented from reaching EDGAR when `SEC_DISABLE_JIT=1` — `backend/tests/ingestion/sec_dense_pipeline/integration/test_search.py`

✅ Omitted `fiscal_year` is resolved and applied to retrieval filters — `backend/ingestion/sec_dense_pipeline/retriever.py`

✅ Valid search calls construct and unit-test both `ticker` and `fiscal_year` conditions — `backend/tests/ingestion/sec_dense_pipeline/unit/test_retriever.py`

✅ Batch ingestion targets the new structured contract and uses `--fiscal-year` — `backend/scripts/embed_sec_filings.py`

✅ Successful batch rows report the resolved fiscal year — `backend/tests/scripts/test_embed_sec_filings.py`

✅ Production retriever and ingestion use `SEC_TEXT_QDRANT_COLLECTION` through the existing collection resolver — `backend/ingestion/sec_dense_pipeline/vectorizer.py`

✅ The in-process set registry performs check-and-insert without `await`, rejects immediately, and releases in `finally` — `backend/ingestion/sec_dense_pipeline/retriever.py`

✅ Embedding and Qdrant clients remain function-local — `backend/ingestion/sec_dense_pipeline/vectorizer.py`

✅ The frozen `_html` fetch/parse/embedding behavior is unchanged; its README update and obsolete batch-CLI test deletion are peripheral — `backend/ingestion/sec_dense_pipeline_html/README.md`

✅ Braintrust spans, `setup_llamaindex()`, and internal ingest spans remain correctly deferred to DEV-161 — `backend/ingestion/sec_dense_pipeline/retriever.py`

✅ DEV-142's SEC agent tool was correctly left untouched for its own later import/filter/citation switch — `backend/agent_engine/tools/`

---

## Discussion Gate Outcome (Round 1)

Orchestrator vetted every finding against the actual code, git precedent (frozen `_html` baseline), and related Linear issues (DEV-113, DEV-127, DEV-132, DEV-136, DEV-137) before this gate. Resolved conversationally with the user, one item at a time — no items were waived by the orchestrator or the fixer.

### Undisputed — fix as reported

| Issue ID | Resolution |
|---|---|
| M-1.2 / SP-1.3 | Fix. `SEC_DISABLE_JIT` guard fires unconditionally before the marker check — confirmed real bug. |
| M-1.3 | Fix. Confirmed via qdrant-client source (`api_client.py::send_inner`) that the raw `httpx.*` except-clause is unreachable dead code; `ResponseHandlingException` also wrongly catches permanent validation errors as transient. |
| M-1.4 / SP-1.4 | Fix. `_resolve_latest_fiscal_year` bypasses `retry_transient` in both call sites — confirmed. |
| SP-1.6 | Fix. Confirmed: `_embed_one()` only returns the resolved year on full success; `main()`'s except-branch falls back to `args.fiscal_year` (often `None`). |
| m-1.1 | Fix. Remove `DEV-160` from `sec_dense_pipeline_html/README.md`. |
| S-1.1 | Fix. `_build_query_filter`'s `applied` dict confirmed unused outside tests. |

### Disputed — resolved with user

1. **B-1.1 / SP-1.1 (bare `search()` allowed)** — User decision: **fix, with a twist**. Orchestrator initially found precedent in the frozen `_html` retriever (identical `if filters and "ticker" in filters` shape) and a same-PR test (`test_search_without_ticker_filter_skips_jit_entirely`) that names this as intentional — suggesting it might be inherited baseline behavior, not a new bug. User then pointed to **DEV-113** (the naive-vs-filtered A/B eval, already merged): naive/unfiltered search measured `ticker_precision@10` mean 0.62, worst case 0.00 (AMD), and DEV-113's own ratified conclusion is "naive collection 是人造 ablation，production 沒有對應物" — i.e. bare search is a proven-harmful mode with no legitimate production caller. **Decision: `ticker` becomes required in `search()`'s `filters`; missing/absent `ticker` raises instead of falling through to an unfiltered query.** The `fiscal_year`-without-`ticker` silent-drop case is resolved as a side effect (no longer reachable once ticker is mandatory before fiscal-year resolution runs). The two tests that lock in bare-search-as-intended are replaced with reject-on-missing-ticker tests. (Sole existing bare-search caller, `eval_tasks.py::run_sec_retrieval`, targets the *old* `_html` retriever and is out of this diff's scope — DEV-164 will need to pass `ticker` from its dataset's `expected_tickers` column when it switches; noted for that ticket, not actioned here.)

2. **M-1.1 (no runtime consumer)** — User decision: **dismiss the reachability complaint** (DEV-142/DEV-161/DEV-164 are the ratified, already-scheduled consumers — ticket-split precedent, not a gap). **But a real consequence survives**: once the batch script stops writing the frozen `_html` collection, the operator loses a path to backfill it — and the user confirmed this is needed (DEV-162 is curating a new eval dataset with tickers not yet present in the old collection, and DEV-138's A/B eval needs both arms populated). Considered two fixes — (1) add a `--pipeline {text,html}` flag to the surviving `embed_sec_filings.py`, or (2) a standalone `embed_sec_filings_html.py` script carrying the logic this diff removed. **User chose (2)**: matches the repo's established `_html` sunset convention (whole files deleted together, not surgically un-merged from a shared script) — see AGENTS.md "this entire subsection is deleted in the sunset PR together with the frozen pipeline."

3. **M-1.5 (concurrent JIT stale-marker race)** — User asked what concretely breaks. Orchestrator traced the consequence through `ingest_filing`'s actual delete-then-reinsert sequence: worst case is a second caller wiping and re-embedding an already-complete filing (wasted EDGAR/embedding cost, self-healing), with a narrow window where a *concurrent reader* (not the racing writer) could observe a transiently-empty result — an envelope §2 "committed or absent" violation, low-probability but real. **User decision: fix** — cheap (one extra marker check after claiming the slot), the request that surfaced it ("重複ingest會出什麼事呢?") having confirmed the cost of *not* fixing was non-trivial enough to be worth the low-cost fix.

4. **M-1.6 (no trace root)** — User asked what "trace root" meant and whether tracing is next-ticket work. Confirmed yes: DEV-161 (sibling ticket, blocked by this one) owns all three Braintrust spans; this PR does not move any user-facing query traffic (the agent tool switch is DEV-142, not yet merged), so no untraced user-facing path exists at merge time. **Decision: dismiss** the tracing-gap complaint entirely. Only the stale doc claim survives as a fix: `backend/scripts/README.md`'s "observability lives in the `search()` JIT path only" line was copied from the old retriever (which has `@observe`) and doesn't hold for the new one yet.

5. **SP-1.2 (GE-style source-level missing Item)** — Orchestrator traced the AC to its origin: DEV-127 (parent spec) Known Limitation #3, "Source-level missing... ParsedFiling 缺項 + legible failure" — confirmed only the "缺項" (dropped from `items`) half exists; no missing-Item signal exists anywhere in the codebase. Orchestrator argued this can't be fixed at the `retriever.py` layer (`search()` takes free-text queries with no notion of "which Item" the caller wants — legibility requires a schema/tool-layer design, not a retriever patch). **User decision: split into a new ticket, not nested under DEV-142.** Filed as [DEV-171](https://linear.app/dongwyt-dev-projects/issue/DEV-171), blocked by DEV-160; DEV-160's AC line struck through and marked re-scoped in Linear.

6. **SP-1.5 (embedding/Qdrant retry classification)** — Split in two. **(a) Qdrant 5xx not retried**: fix, folded into M-1.3's fix (classify `UnexpectedResponse` with a 5xx status as `TransientError` too). **(b) Embedding failures should also route through `retry_transient`**: dismiss — the diff's own docstring already documents the reason (the embedding SDK's internal retry + `retry_transient` wrapping the whole call would double up, which is exactly the stacked-retry anti-pattern ADR-0013 rules out); forcing a single formal policy by disabling a working SDK-internal retry isn't worth it in this envelope.

---

