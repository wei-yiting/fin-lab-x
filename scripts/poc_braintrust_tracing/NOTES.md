# DEV-100 Braintrust Tracing POC — Findings

> PROTOTYPE artifact. The verdicts below are the only thing worth keeping —
> they feed the「observability 平台統一」ADR. Delete this directory once the
> ADR records the outcome.

**Question**: Runtime tracing 能否從 Langfuse 全面遷移到 Braintrust —
per-request `BraintrustCallbackHandler` + LangGraph `astream()` + LlamaIndex
`setup_llamaindex()` 巢狀是否滿足 streaming observability guardrails 的 Gates？

**Answer: 全部 Gates PASS — 但有一個關鍵前提**（見 Finding 1）。

**Run**:

```bash
uv run --extra dev --with 'braintrust==0.30.1' python scripts/poc_braintrust_tracing/run_poc.py
```

（host 執行，讀 `backend/.env` 的 `BRAINTRUST_API_KEY` / `OPENAI_API_KEY`；
trace 進 Braintrust project `poc-braintrust-tracing`。span 樹以 Braintrust
REST API `/v1/project_logs/{id}/fetch` 抓回程式化驗證 parentage，非只靠 UI 目視。）

## Verdicts（2026-07-23，braintrust 0.30.1）

| Gate | 結果 | 證據 |
| --- | --- | --- |
| Gate 1 — single top-level trace | ✅ PASS | `request:gate1-single-trace` trace（8 spans, top-level=1）[trace](https://www.braintrust.dev/app/Dong.wyt%20Personal/object?object_type=project_logs&object_id=9d978f09-ab2c-4bce-88d5-15c7522fd2ff&id=7363608d-dd35-4aee-904e-ad25ef76f7b2) |
| ⚠️ Nesting — LlamaIndex under LangGraph tool span | ✅ PASS | `VectorIndexRetriever → OpenAIEmbedding` dispatcher spans 巢狀在 `poc_retrieve` tool span 下、同一 trace、無 detached [trace](https://www.braintrust.dev/app/Dong.wyt%20Personal/object?object_type=project_logs&object_id=9d978f09-ab2c-4bce-88d5-15c7522fd2ff&id=974f8534-0f1b-44ec-836e-8bd7e64103b0) |
| Streaming integrity | ✅ PASS | token-level astream（44 chunks）+ 兩個 tool spans 完整 name/args/result，無 orphan/duplicate [trace](https://www.braintrust.dev/app/Dong.wyt%20Personal/object?object_type=project_logs&object_id=9d978f09-ab2c-4bce-88d5-15c7522fd2ff&id=ff443a94-fd3b-429b-962c-7e58404f5d61) |
| Concurrency isolation（Rule 12 bypass） | ✅ PASS | conc-A / conc-B 各自獨立 trace，span 內容互不出現（A 只有 retrieve/ACME、B 只有 price/GLBX）[A](https://www.braintrust.dev/app/Dong.wyt%20Personal/object?object_type=project_logs&object_id=9d978f09-ab2c-4bce-88d5-15c7522fd2ff&id=5a72a428-e093-47ff-8299-7fccdd91fd3b) / [B](https://www.braintrust.dev/app/Dong.wyt%20Personal/object?object_type=project_logs&object_id=9d978f09-ab2c-4bce-88d5-15c7522fd2ff&id=f5c051db-c327-4b83-8e5f-96891126c7eb) |
| Rule 13 — handler failure isolation | ✅ PASS | 共存 handler 在 `on_llm_new_token` 拋例外：stream 完成、答案正常、Braintrust trace 完整（LangChain 捕捉並印 warning）[trace](https://www.braintrust.dev/app/Dong.wyt%20Personal/object?object_type=project_logs&object_id=9d978f09-ab2c-4bce-88d5-15c7522fd2ff&id=45594ae5-9d9b-4aa8-bdbd-6e9f69ec365f) |

## Findings（ADR 必讀）

1. **裸 per-request handler 不夠 — 必須包官方 route-handler pattern。**
   第一輪只給 `callbacks=[BraintrustCallbackHandler()]`（無外層 span）時，同
   process 內連續多個 request 被串成一條 56-span 巨型 trace（後一 request 的
   root 巢狀在前一 request 之下；root span 的 current-span context 洩漏）。
   照官方建議每個 request 包 `with braintrust.start_span(name=..., type="task")`
   後，隔離完全正確。→ 未來 `base.py` 的 `_build_langfuse_config` 對應物必須
   在 request 入口建立明確 root span（等價於 Langfuse `propagate_attributes`
   的角色），不能只換 handler。
2. **版本前提：braintrust >= 0.30。** repo 目前鎖 `braintrust==0.11.0` +
   已棄用的 `braintrust-langchain` 套件。`setup_llamaindex` 與
   `braintrust.integrations.langchain` 只存在合併後的新版（POC 用 0.30.1）。
   遷移需升版並移除 `braintrust-langchain` 依賴（import 路徑改
   `braintrust.integrations.langchain`）。
3. **Startup 噪音：** index 建立（SentenceSplitter / corpus embedding）發生在
   request scope 外，會以零散 top-level trace 出現。正式遷移時 ingestion
   pipeline 的 dispatcher spans 需要自己的 root span 包裝，否則 logs 會有
   單-span 孤兒 trace。
4. **Rule 13 由 LangChain 保證：** handler 例外被 LangChain callback manager
   捕捉（stderr warning），不需自建 try/except wrapper。

## Next step

全過 → 開「observability 平台統一」ADR/grilling issue，範圍：

- `base.py`：Langfuse `CallbackHandler` + `propagate_attributes` → Braintrust
  per-request handler + request root span（Finding 1 的 pattern）
- `span_tracing.py`：`@observe` → `@traced`
- 依賴升版 braintrust 0.11 → ≥0.30、移除 `braintrust-langchain`（Finding 2）
- ingestion pipelines 的 root span 包裝（Finding 3）
- annotation 遷移、`bt sync` cron（free tier logs 14 天 retention）
