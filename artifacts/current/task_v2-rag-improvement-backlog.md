# V2 RAG Improvement Backlog — Hooks & Function Contracts

> 本檔案是 V2 RAG baseline 後續所有 retrieval 改進的對接 reference。Section 1-2 來自 V2 baseline (PR #11) `design_v2-rag-pipeline.md` 的 Design 哲學 + Locked Decisions;Section 3-5 是 A/B Switch Points 預留(原 design Section 7),補入此 PR 是因為原 worktree(`rag-search-tool-pipeline`)post-squash-merge 即將清掉,但這份 hook 契約對未來進階(commit-scope 5 項中的 4 項)有 forward-looking 價值。
>
> Active commit scope 對應(per FinLab-X Dev Timeline 2026-04-29 重排版):
>
> | 進階 | T-code | 對應 Hook |
> | --- | --- | --- |
> | Chunk enrichment | T3 | Hook 3 `_prepare_chunk_text()` |
> | Hybrid retrieval (BM25 + dense) | T2a/T2b | Hook 2 env var |
> | Query rewriting | T6-related | Hook 5 `_preprocess_query()` |
> | HyDE | T6 | Hook 5 同上(可二選一或 chain) |
> | Reranker | T5 | Hook 4 `_rerank()` |
>
> Stretch(不在 commit scope):T1 metadata filter、T4 chunk size sensitivity、T7 `fetch_section`、T8 embedding model swap、T9 summary-index hierarchical、T10 小 table preservation。
>
> ⚠️ Hook 對接位置以本 PR(V2 Path2 / `refactor/improve-rag-ingestion`)merge 後的 code 結構為準。原 V2 baseline 設計指向 `backend/app/rag/*`,實際 PR #11 merge 後位於 `backend/ingestion/sec_dense_pipeline/{retriever,vectorizer}.py`,Path2 可能再次調整 — 函式 signature / 契約不變,只是 import 路徑跟著走。

---

## 1. Eval-Driven Baseline 哲學

**Eval-driven baseline, not quality-first baseline**:

- Baseline 的 retrieval 數字不追求好看
- 目標是成為三版本 baseline eval 的 V2 基準值
- 所有 retrieval 優化作為 A/B factor 引入,每個 improvement 的 delta 是 eval 素材
- **沒有公開 benchmark 可直接對照**(FinanceBench 量 end-to-end answer correctness,我們量 retrieval metrics,屬於不同 metric family)

任何後續進階(Section 3-5)只能在 baseline 之上以 A/B 形式比對,**不取代 baseline**。

## 2. Locked Baseline Decisions

| 項目 | 選擇 | 備註 |
| --- | --- | --- |
| Framework 分工 | LangGraph (agent) + LlamaIndex (RAG) + Qdrant (store) + OpenAI (embed) | |
| Text splitter | LangChain `RecursiveCharacterTextSplitter` via LlamaIndex `LangchainNodeParser` wrapper | LangChain 只作為 text splitter utility,LlamaIndex 仍是 RAG 主 framework |
| Embedding model | OpenAI `text-embedding-3-large` (3072-dim) | JIT cold-start 友善;BGE-M3 local 因速度問題(MacBook CPU 5-10 分鐘 per filing)不採用 |
| Chunk size | 512 tokens | SEC narrative 較長;reranker (T5) 相容 |
| Chunk overlap | 50 tokens | |
| Token counter | `tiktoken` `cl100k_base` | 精準對齊 OpenAI tokenizer(GPT-3.5/4 + embedding 系列共用 BPE encoding) |
| Top-k | 10 | |
| Vector store | Qdrant single collection with dense vectors only | |
| Ingest 觸發 | **Batch pre-load + JIT cold-start 都做** | JIT 只在 `filters["ticker"]` 明確指定時觸發 |
| Metadata filter | ❌ baseline signature 保留,body 忽略 | T1 啟用 |
| Contextual prefix | ❌ baseline 為原文 | T3 |
| Reranker | ❌ baseline 為 pass-through | T5 |
| Eval scorers | recall@5 + recall@10 + MRR + MAP 四個 | |
| Eval dataset | Hybrid:auto-generate 30 → 人工 curate 8 題 + 手寫 2-3 題 cross-company | |

進階做 ablation 時必須回到這份基準參數,只動目標 factor,其餘維持 default。

---

## 3. A/B Switch Points 預留 — 概念

Baseline 必須讓後續 T-tasks 只需要改 hook 內容,不需重構 baseline。本設計區分兩種預留方式:

- **Code-reserved**(已寫進 baseline):hook 的 placeholder code 已存在,T-task 直接 swap function body 即可上線
- **Doc-only**(本檔記錄,baseline 不寫):placeholder code 不在 baseline 內,但**對接位置 / 函式契約 / 期待行為**有明文記錄。T-task 啟動時依本檔規格在指定位置新增 function

採用 doc-only 而非 code-reserved 的判斷標準:

- **加入 placeholder 不會減少 T-task 工作量**(pass-through 函式 5 行 LOC,T-task 寫的時候等於從零寫)
- **加入 placeholder 會讓 baseline 看起來有不存在的功能**(dead code 對 reviewer 是負擔)

## 4. Hook 總覽

| Hook | 位置(post-PR #11 main) | Baseline 行為 | 預留方式 | 為誰預留 |
| --- | --- | --- | --- | --- |
| `filters` 參數 | `retriever.py::search()` signature | Vector search 忽略(JIT 會讀) | **Code-reserved** | T1 metadata filter |
| Env var config | `retriever.py` / `vectorizer.py` module top | 讀 default 值 | **Code-reserved** | T2a / T2b / T4 / T8 |
| `_prepare_chunk_text()` | `vectorizer.py::ingest_filing()` 內,chunk 餵 embed 前 | 不存在 | **Doc-only** | T3 contextual prefix(chunk enrichment) |
| `_rerank()` | `retriever.py::search()` 內,retrieve 完 top_k 之後 | 不存在 | **Doc-only** | T5 reranker |
| `_preprocess_query()` | `retriever.py::search()` 內,embed query 之前 | 不存在 | **Doc-only** | T6 HyDE / Query rewrite |

**Baseline 真正要寫的 hook code 只有兩個**:`search()` signature 中的 `filters` 參數 + module-level env var 讀取。其他三個是文件契約,T3/T5/T6 啟動時依下方規格**新增** function 跟 call site。

---

## 5. Hooks Detail

### 5.1 Hook 1:`filters` 參數(Code-reserved,baseline 已具備)

- `search(query, filters=None, top_k=10)` — signature 保留,vector search body 忽略
- **JIT 仍讀 `filters["ticker"]`** 決定是否觸發 ingest
- T1 task:加 body 邏輯轉換 filters dict → Qdrant `FieldCondition`

### 5.2 Hook 2:Env var config(Code-reserved,baseline 已讀 default)

| Env var | Default | 目的 |
| --- | --- | --- |
| `SEC_QDRANT_COLLECTION` | `sec_filings_openai_large_dense_baseline` | T2a / T2b / T4 / T8 建新 collection |
| `SEC_EMBED_MODEL` | `text-embedding-3-large` | T8 swap embedding model |
| `SEC_EMBED_DIM` | `3072` | 與 model 對齊 |
| `SEC_CHUNK_SIZE` | `512` | T4 chunk size sensitivity |
| `SEC_CHUNK_OVERLAP` | `50` | T4 相關 |

Experiment 切換方式:

```bash
# Run baseline
python -m backend.evals.eval_runner sec_retrieval

# Run T2a hybrid retrieval
SEC_QDRANT_COLLECTION=sec_filings_openai_large_hybrid_bm25 \
  python -m backend.evals.eval_runner sec_retrieval
```

⚠️ Ingest script 跟 eval runner 必須讀到同個 collection(ingest 到 A,eval 也查 A)— run experiment 時的紀律,code 不強制。

### 5.3 Hook 3:`_prepare_chunk_text()` — Doc-only,T3 chunk enrichment 用

**Baseline 不實作**。T3 task 啟動時新增。

**對接位置**:`backend/ingestion/sec_dense_pipeline/vectorizer.py`,`ingest_filing()` 內,chunk text 餵給 embedding 之前

**契約**:

```python
def _prepare_chunk_text(raw_text: str, metadata: dict) -> str:
    """
    Prepare chunk text right before embedding.

    T3 implementation:
        Prepend metadata to chunk text:
        return f"{metadata['ticker']} {metadata['year']} 10-K — {metadata['header_path']}\n\n{raw_text}"
    """
```

**對接需要的 baseline 改動**(T3 task 啟動時):在 `ingest_filing()` 內部,原本 `chunk.text = raw_text` 的位置改成 `chunk.text = _prepare_chunk_text(raw_text, chunk.metadata)`。

T3 ablation 比的是「chunk 是否有 contextual prefix」,所以 collection 必須另開(`SEC_QDRANT_COLLECTION=...contextual`),baseline collection 保留作為對照組。

### 5.4 Hook 4:`_rerank()` — Doc-only,T5 reranker 用

**Baseline 不實作**。T5 task 啟動時新增。

**對接位置**:`backend/ingestion/sec_dense_pipeline/retriever.py`,`search()` retrieve 完 top_k 之後、return 之前

**契約**:

```python
async def _rerank(query: str, chunks: list[Chunk], top_k: int) -> list[Chunk]:
    """
    Cross-encoder rerank.

    T5 implementation:
        Use BGE-reranker-v2-m3 (or Cohere Rerank API) to rerank `chunks`
        based on query relevance, return top `top_k`.
        Baseline retrieves 20 → rerank to 10.
    """
```

**對接需要的 baseline 改動**:

- 把 retriever 端的 `similarity_top_k` 從 10 調成 20(或透過新 env var `SEC_RETRIEVE_TOP_K`)
- `search()` 的 retrieve 後加 `chunks = await _rerank(query, chunks, top_k)` call

T5 ablation 比的是「retrieve 20 後 rerank 到 10」 vs 「retrieve 10」,collection 不變(同一份 dense vectors),改變的是 retrieve + rerank pipeline 行為。可不另開 collection,只在 eval runtime swap。

### 5.5 Hook 5:`_preprocess_query()` — Doc-only,T6 HyDE / Query rewrite 用

**Baseline 不實作**。T6 task 啟動時新增。

**對接位置**:`backend/ingestion/sec_dense_pipeline/retriever.py`,`search()` 內部把 query 餵給 retriever 之前

**契約**:

```python
async def _preprocess_query(query: str) -> str:
    """
    Query transformation before embedding.

    T6 implementations (兩種互斥變體,each 一個 experiment):

        HyDE:
            Ask LLM to draft a hypothetical SEC 10-K paragraph that would
            answer the query, return the hypothetical paragraph as the
            new query string.

        Query Rewriting (multi-query):
            Ask LLM to rewrite the query into N domain-specific search
            queries, retrieve each, then RRF / max-pool merge results.
            Return type extended to list[str] in this variant; caller
            handles fan-out.
    """
```

**對接需要的 baseline 改動**:在 `search()` 內部,把原本 `nodes = retriever.retrieve(query)` 改成 `nodes = retriever.retrieve(await _preprocess_query(query))`。

T6 兩個 variant(HyDE / Query rewriting)都用同一 hook 點;若兩者要 chain(rewrite → 各自 HyDE → merge),signature 在 chain variant 啟動時再延伸。

### 5.6 不預留 hook 的 T-tasks

| T-task | 為何不預留 |
| --- | --- |
| T7 `fetch_section` tool | 新 tool function 直接新增即可,不影響既有 `search()` |
| T9 Summary-index hierarchical | 獨立子系統(新 ingest + 新 collection + query routing),無法用簡單 hook 容納 |
| T10 小 table 保留 | 是 HTMLPreprocessor 上游改動 |

**總 hook 成本 ~25 行 baseline code**,涵蓋本 commit scope 4 項進階(T2a/T2b、T3、T5、T6)的對接路徑。

---

## 6. 與 V2 Path2 (本 PR) 的關係

本 PR 重寫 ingestion(改用 edgartools 原生 API + section.text() + 直接 sub-heading 偵測 + manual metadata),對 hook 的影響:

- **Hook 2 env var**:不變,Path2 後仍從 module top 讀 default
- **Hook 3 `_prepare_chunk_text()`**:對接位置從 `ingest_filing()` 改成 Path2 後的等價函式(章節 → chunk 的轉換點)。契約不變
- **Hook 4 `_rerank()`** + **Hook 5 `_preprocess_query()`**:位於 retriever 端,Path2 主要動 ingestion,retriever 變動較少。位置 / 契約理論上不變

T-task 真正啟動時,最後檢查 hook 對接位置是否還對齊 Path2 後的實際 code。

---

## 7. References

- 原 V2 baseline 設計:`rag-search-tool-pipeline` worktree `artifacts/current/design_v2-rag-pipeline.md`(post-squash-merge 將清掉)
- PR #11(V2 baseline merged):`feat(sec-pipeline): v2 RAG pipeline — dense vector ingest, search, eval`
- 上游 dependency 設計:本 worktree `design_master.md`(SEC Filing Pipeline 簡化 — edgartools 原生 API)
- Improvement priority(commit scope vs stretch):見 FinLab-X Dev Timeline 2026-04-29 重排版 Stream 6
