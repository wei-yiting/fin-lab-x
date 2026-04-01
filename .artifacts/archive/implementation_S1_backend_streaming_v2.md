# Implementation Plan: S1 Backend Streaming

> Design Reference: [`design_S1_backend_streaming_v2.md`](./design_S1_backend_streaming_v2.md)

**Goal:** 實作 backend streaming 能力——從 LangGraph agent 取得即時 chunks，翻譯為 AI SDK UIMessage Stream Protocol v1 的 SSE events，透過 FastAPI endpoint 送出。

**Architecture / Key Decisions:** 採用三層架構：`Orchestrator.astream_run()` → `StreamEventMapper`（LangGraph chunks → domain events）→ SSE Serializer（domain events → `data: {json}\n\n`）。使用 `InMemorySaver` checkpointer 管理 conversation state，`functools.singledispatch` 作為 serializer pattern。Tool error 使用 `data-tool-error` custom event（偏離 master DR-07，因 AI SDK v5 無標準 `tool-error` SSE type）。

**Tech Stack:** Python 3.13, FastAPI, LangGraph (`astream` + `stream_mode=["messages", "updates", "custom"]` + `version="v2"`), LangChain `create_agent`, Langfuse v4 (`CallbackHandler` + `propagate_attributes`)

---

## Dependencies Verification

| Dependency | Version | Source | What Was Verified | Notes |
|---|---|---|---|---|
| LangGraph | ≥1.0 | Context7 `/websites/langchain_oss_python_langgraph` | `astream()` 支援 `stream_mode=["messages", "updates", "custom"]` + `version="v2"`；v2 chunk format 為 `{"type": str, "data": Any}`；`get_stream_writer()` 從 `langgraph.config` import；`InMemorySaver` 從 `langgraph.checkpoint.memory` import | `messages` mode 的 `data` 是 `(AIMessageChunk, metadata)` tuple |
| LangChain | ≥1.2.10 | Context7 `/websites/langchain_oss_python_langchain` | `create_agent()` 支援 `checkpointer` 參數，可直接傳入 `InMemorySaver()` | 與 `thread_id` configurable 搭配使用 |
| Langfuse | ≥4.0.0 | pyproject.toml 現有依賴 | `CallbackHandler` + `propagate_attributes` 已在 codebase 使用 | POC 驗證 streaming 下行為 |

## Constraints

- 不可修改現有 `POST /api/v1/chat` endpoint（既有測試必須全數通過）
- 不可在 streaming path 上使用 `@observe()`（遵循 `streaming_observability_guardrails.md`）
- POC Gates 1-6 必須全部通過後才能開始正式 implementation（Task 2+）
- V1 不支援 `tool-call-delta`（tool input streaming）
- V1 只支援 regenerate 最後一條 assistant message

---

## File Plan

| Operation | Path | Purpose |
|---|---|---|
| Create | `backend/agent_engine/streaming/__init__.py` | Streaming package init，re-export public API |
| Create | `backend/agent_engine/streaming/events.py` | Domain event frozen dataclasses（11 event types） |
| Create | `backend/agent_engine/streaming/mapper.py` | `StreamEventMapper`：LangGraph chunks → domain events |
| Create | `backend/agent_engine/streaming/serializer.py` | SSE serializer（`singledispatch`）：domain events → `data: {json}\n\n` |
| Update | `backend/agent_engine/agents/base.py` | 新增 `astream_run()` method、`InMemorySaver` checkpointer、`run()`/`arun()` 加 `thread_id` |
| Update | `backend/agent_engine/tools/financial.py` | 移除 `@observe()`、加入 `get_stream_writer()` progress |
| Update | `backend/agent_engine/tools/sec.py` | 移除 `@observe()`、加入 `get_stream_writer()` progress |
| Update | `backend/api/routers/chat.py` | 新增 `POST /api/v1/chat/stream` endpoint（含 regenerate） |
| Update | `backend/agent_engine/docs/streaming_observability_guardrails.md` | 更新 Rule 3，排除透過 graph 執行的 tools |
| Create | `backend/tests/poc/__init__.py` | POC test package |
| Create | `backend/tests/poc/test_observability_gates.py` | Observability POC gate 驗證腳本 |
| Create | `backend/tests/streaming/__init__.py` | Streaming test package |
| Create | `backend/tests/streaming/test_events.py` | Domain events 單元測試 |
| Create | `backend/tests/streaming/test_serializer.py` | SSE serializer 單元測試 |
| Create | `backend/tests/streaming/test_mapper.py` | `StreamEventMapper` 單元測試 |
| Create | `backend/tests/agents/test_astream_run.py` | `astream_run()` 單元測試 |
| Create | `backend/tests/api/test_chat_stream.py` | Streaming endpoint 測試 |

**Structure sketch:**

```text
backend/
  agent_engine/
    streaming/               ← new package
      __init__.py
      events.py              ← domain event dataclasses
      mapper.py              ← StreamEventMapper
      serializer.py          ← SSE serializer (singledispatch)
    agents/
      base.py                ← add astream_run(), checkpointer
    tools/
      financial.py           ← remove @observe(), add progress writer
      sec.py                 ← remove @observe(), add progress writer
    docs/
      streaming_observability_guardrails.md  ← update Rule 3
  api/
    routers/
      chat.py                ← add POST /api/v1/chat/stream
  tests/
    poc/                     ← new: POC gate validation
      test_observability_gates.py
    streaming/               ← new: streaming unit tests
      test_events.py
      test_serializer.py
      test_mapper.py
    agents/
      test_astream_run.py    ← new
    api/
      test_chat_stream.py    ← new
```

---

### Task 1: POC — Observability Gates 1-6

**Files:**

- Create: `backend/tests/poc/__init__.py`
- Create: `backend/tests/poc/test_observability_gates.py`

**What & Why:** 在寫任何 production streaming code 之前，必須驗證 `astream()` + `CallbackHandler` 在 streaming context 下的 observability 行為。Design 明確要求 POC Gates 全部通過才能繼續。此 task 建立一個最小可執行的 POC，直接用 `create_agent()` + `InMemorySaver()` + `astream()` 驗證 6 個 gate。

**Implementation Notes:**

- POC 測試需要真實的 Langfuse API key（`LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST`）和 LLM API key
- 用 `pytest.mark.poc` marker 標記，不納入 CI 常規測試
- 每個 gate 為一個獨立的 test function，手動執行後到 Langfuse dashboard 驗證 trace 結構
- Gate 6 需額外安裝 `braintrust`（作為 dev dependency）並設定 Braintrust API key
- Gate 失敗時：分析 root cause（`CallbackHandler` / `contextvars` / `@observe()` 殘留 / global handler flush 時機），解決後重新驗證
- Gate 6 fallback：若 Braintrust global handler 在 `astream()` 下無法正常工作，eval task function 退回使用 `run()`（非 streaming），不影響 API server streaming 路徑

**Critical Contract / Snippet:**

POC agent 建立方式（後續 Task 6 正式整合到 `Orchestrator`，POC 用獨立 setup）：

```python
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import InMemorySaver
from langfuse import propagate_attributes
from langfuse.langchain import CallbackHandler

model = init_chat_model("gpt-4o-mini", temperature=0.0)
checkpointer = InMemorySaver()
agent = create_agent(model=model, tools=[...], checkpointer=checkpointer)

handler = CallbackHandler()
config = {
    "callbacks": [handler],
    "configurable": {"thread_id": "poc-test-1"},
}

with propagate_attributes(session_id="poc-session"):
    async for chunk in agent.astream(
        {"messages": [{"role": "user", "content": "..."}]},
        config=config,
        stream_mode=["messages", "updates", "custom"],
        version="v2",
    ):
        pass  # Consume all chunks
```

6 個 gate 的驗證邏輯：

| Gate | Test Function | 驗證方式 | 通過標準 |
|---|---|---|---|
| 1 | `test_gate1_single_trace` | 單一 `astream()` 呼叫後，查 Langfuse trace count | 一個 request → 一個 trace，`session_id` 正確 |
| 2 | `test_gate2_tool_observation` | 用含 tool call 的 prompt，檢查 trace 的 child observations | Tool name/args/result/duration 有紀錄，是 trace 的 child |
| 3 | `test_gate3_disconnect_cleanup` | 中途取消 async generator（`aclose()`），檢查 trace 狀態 | 不留 orphan trace |
| 4 | `test_gate4_exception_visible` | 觸發 tool exception，檢查 trace error 狀態和 SSE output | Trace 和 output 都有 error 紀錄 |
| 5 | `test_gate5_concurrent_isolation` | 3 個並發 `astream()` 各用不同 `session_id`，檢查 trace 隔離 | 3 個 request → 3 個獨立 trace，session_id 不交叉 |
| 6 | `test_gate6_dual_handler` | `set_global_handler(BraintrustCallbackHandler())` + Langfuse per-request handler，跑 `astream()` | 兩平台各自收到完整 trace，互不干擾 |

**Test Strategy:** POC gate 本身就是測試。每個 gate 的 assertion 驗證本地可檢查的行為（chunk 格式、exception 是否被吞）；trace 完整性需目視 Langfuse dashboard 確認。Gate 6 需同時檢查 Braintrust experiment 和 Langfuse trace。

**Verification:**

| Scope | Command | Expected Result | Why |
|---|---|---|---|
| POC gates | `pytest backend/tests/poc/ -m poc -v --tb=short` | 所有 gate assert 通過 | 驗證 streaming observability 基礎假設 |
| Langfuse dashboard | 手動檢查 trace 結構 | 每個 gate 對應的 trace 結構正確 | 自動化 assert 無法完全涵蓋 trace hierarchy |

**Execution Checklist:**

- [ ] 確認 `.env` 有 Langfuse + LLM API keys
- [ ] 建立 `backend/tests/poc/__init__.py` 和 `backend/tests/poc/test_observability_gates.py`
- [ ] 實作 Gate 1-5 test functions
- [ ] 執行 Gate 1-5 並在 Langfuse dashboard 驗證
- [ ] 實作 Gate 6 test function（需 Braintrust API key）
- [ ] 執行 Gate 6 並在兩個平台驗證
- [ ] 記錄每個 gate 的通過結果（screenshot 或 trace URL）
- [ ] 若任何 gate 失敗，分析 root cause 並記錄緩解方案
- [ ] Commit：`test(S1): observability POC gates 1-6 validation`

---

### Task 2: Domain Events

**Files:**

- Create: `backend/agent_engine/streaming/__init__.py`
- Create: `backend/agent_engine/streaming/events.py`
- Create: `backend/tests/streaming/__init__.py`
- Create: `backend/tests/streaming/test_events.py`

**What & Why:** 定義 streaming pipeline 的中間表示層。所有 domain events 為 `frozen` dataclasses，與 LangGraph chunk format 和 SSE wire format 完全解耦。這是 mapper 和 serializer 共同依賴的基礎。

**Critical Contract / Snippet:**

```python
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class MessageStart:
    message_id: str

@dataclass(frozen=True)
class TextStart:
    text_id: str

@dataclass(frozen=True)
class TextDelta:
    text_id: str
    delta: str

@dataclass(frozen=True)
class TextEnd:
    text_id: str

@dataclass(frozen=True)
class ToolCallStart:
    tool_call_id: str
    tool_name: str

@dataclass(frozen=True)
class ToolCallEnd:
    tool_call_id: str

@dataclass(frozen=True)
class ToolResult:
    tool_call_id: str
    result: str

@dataclass(frozen=True)
class ToolError:
    tool_call_id: str
    error: str

@dataclass(frozen=True)
class ToolProgress:
    tool_call_id: str
    data: dict[str, Any]

@dataclass(frozen=True)
class StreamError:
    error_text: str

@dataclass(frozen=True)
class Finish:
    finish_reason: str
    usage: dict[str, int]

# Union type for type narrowing
DomainEvent = (
    MessageStart | TextStart | TextDelta | TextEnd
    | ToolCallStart | ToolCallEnd | ToolResult | ToolError | ToolProgress
    | StreamError | Finish
)
```

**Test Strategy:** 單元測試驗證：(1) 每個 event type 可正確建立，(2) frozen 不可變性（賦值 raise `FrozenInstanceError`），(3) `DomainEvent` union type 涵蓋所有 event types。純 data class 測試，不需 mock。

**Verification:**

| Scope | Command | Expected Result | Why |
|---|---|---|---|
| Targeted | `pytest backend/tests/streaming/test_events.py -v` | 全部通過 | 驗證 event dataclass 定義正確 |

**Execution Checklist:**

- [ ] 🔴 寫 `test_events.py`：instantiation、frozen 不可變、field 型別
- [ ] 🔴 執行測試確認 **fail**（`events.py` 尚不存在）
- [ ] 🟢 建立 `backend/agent_engine/streaming/__init__.py` 和 `events.py`，實作 11 個 frozen dataclasses + `DomainEvent` type alias
- [ ] 🔵 檢視實作，確認命名與 design document 一致
- [ ] 🔵 重新執行測試確認 **still pass**
- [ ] Commit：`feat(S1): add domain event dataclasses for streaming pipeline`

---

### Task 3: SSE Serializer

**Files:**

- Create: `backend/agent_engine/streaming/serializer.py`
- Create: `backend/tests/streaming/test_serializer.py`

**What & Why:** 將 domain events 轉換為 AI SDK UIMessage Stream Protocol v1 的 SSE wire format（`data: {json}\n\n`）。使用 `functools.singledispatch` 讓每個 event type 有獨立的 serialization function，擴展時不改既有 code。Serializer 是純函數，不持有狀態。

**Implementation Notes:**

- 每個 `singledispatch` handler 負責 domain event field 到 wire format field 的映射（如 `message_id` → `"messageId"`, `text_id` → `"id"`, `tool_call_id` → `"toolCallId"`）
- `ToolProgress` serializer 負責加入 `"transient": true`
- `ToolError` serializer 產出 `"type": "data-tool-error"`（custom event namespace）
- `Finish` serializer 產出 `usage` 為 `{"inputTokens": N, "outputTokens": N}` 格式
- `StreamError` serializer 產出 `"errorText"` 欄位（與 master design 一致）
- 最終輸出格式：`f"data: {json.dumps(payload)}\n\n"`

**Critical Contract / Snippet:**

```python
import json
from functools import singledispatch
from backend.agent_engine.streaming.events import (
    DomainEvent, MessageStart, TextDelta, ToolProgress, ...
)

@singledispatch
def serialize_event(event: DomainEvent) -> str:
    raise TypeError(f"Unhandled event type: {type(event)}")

@serialize_event.register
def _(event: MessageStart) -> str:
    return _sse({"type": "start", "messageId": event.message_id})

@serialize_event.register
def _(event: TextDelta) -> str:
    return _sse({"type": "text-delta", "id": event.text_id, "delta": event.delta})

# ... (each event type registered)

def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload)}\n\n"
```

**Test Strategy:** 每個 event type 一個測試，驗證 (1) 輸出是 `data: {json}\n\n` 格式，(2) JSON payload 的 field name 和 value 正確對應，(3) 未註冊的 event type raise `TypeError`。特別測試：`ToolProgress` 含 `"transient": true`，`ToolError` type 為 `"data-tool-error"`，`Finish` usage 格式。

**Verification:**

| Scope | Command | Expected Result | Why |
|---|---|---|---|
| Targeted | `pytest backend/tests/streaming/test_serializer.py -v` | 全部通過 | 驗證 wire format 符合 AI SDK protocol |

**Execution Checklist:**

- [ ] 🔴 寫 `test_serializer.py`：每個 event type 的 serialization 輸出、`_sse` 格式、未知 type raise
- [ ] 🔴 執行測試確認 **fail**
- [ ] 🟢 實作 `serializer.py`，`singledispatch` + 11 個 `register` handlers + `_sse` helper
- [ ] 🔵 檢視欄位映射（camelCase wire format vs snake_case domain），確認與 design Event Taxonomy 一致
- [ ] 🔵 重新執行測試確認 **still pass**
- [ ] Commit：`feat(S1): add SSE serializer with singledispatch pattern`

---

### Task 4: StreamEventMapper

**Files:**

- Create: `backend/agent_engine/streaming/mapper.py`
- Create: `backend/tests/streaming/test_mapper.py`

**What & Why:** 有狀態的翻譯器，追蹤 text block 和 tool call 的生命週期。LangGraph 不產生 `text-start/end`、tool call 資訊分散在三個 stream mode，mapper 負責這些翻譯和補充。這是整個 streaming pipeline 最複雜的元件。

**Implementation Notes:**

- 內部狀態：
  - `_started: bool` — 是否已發出 `MessageStart`
  - `_text_open: bool` — 當前是否有開啟的 text block
  - `_current_text_id: str | None` — 當前 text block 的 ID
  - `_text_counter: int` — text block 計數器
  - `_message_id: str` — 本次 stream 的 message ID
  - `_pending_tool_calls: dict[str, str]` — `tool_name → tool_call_id` mapping（供 progress 反查）
  - `_seen_tool_call_ids: set[str]` — 已發出 `ToolCallStart` 的 tool_call_id
- `process_chunk(chunk: dict) -> list[DomainEvent]`：處理一個 v2 format chunk，回傳 0 到多個 domain events
- `finalize() -> list[DomainEvent]`：stream 結束時呼叫，補上 `TextEnd`（若 text block 仍開啟）和 `Finish`
- 三個 stream mode 的處理邏輯：

| chunk["type"] | 處理邏輯 |
|---|---|
| `"messages"` | `data = (AIMessageChunk, metadata)`。若有 `.content`：檢查 text block 狀態，補 `TextStart` 若需要，產出 `TextDelta`。若有 `.tool_call_chunks`：關閉 text block（補 `TextEnd`），對每個新 tool call 產出 `ToolCallStart` 並記入 `pending_tool_calls` |
| `"updates"` | `data = {node_name: state}`。掃描 state 中的 messages：`AIMessage` 有 `tool_calls` → 對每個 call 產出 `ToolCallEnd`；`ToolMessage` → 根據 `status` 產出 `ToolResult` 或 `ToolError` |
| `"custom"` | `data = dict`。從 `data["toolName"]` 反查 `pending_tool_calls` 取得 `tool_call_id`，產出 `ToolProgress` |

- ID 生成：`message_id` 用 `f"msg_{uuid4().hex[:8]}"`，`text_id` 用 `f"txt_{counter:03d}"`

**Test Strategy:** 6 組測試覆蓋 mapper 核心行為：

1. **Text streaming**：連續 text content chunks → 正確產出 `MessageStart` + `TextStart` + 多個 `TextDelta` + `TextEnd`（finalize 時）
2. **Tool call lifecycle**：`messages` mode tool_call_chunks → `ToolCallStart`，`updates` mode agent node 完成 → `ToolCallEnd`，`updates` mode tool node 完成 → `ToolResult`
3. **Tool error**：`ToolMessage` 有 `status="error"` → 產出 `ToolError`
4. **Tool progress**：`custom` mode chunk → 正確反查 `tool_call_id` 並產出 `ToolProgress`
5. **Text-tool-text transition**：text → tool call → text，驗證 text block 正確關閉和重新開啟
6. **Finalize**：stream 結束時補齊 `TextEnd` 和 `Finish`

**Verification:**

| Scope | Command | Expected Result | Why |
|---|---|---|---|
| Targeted | `pytest backend/tests/streaming/test_mapper.py -v` | 全部通過 | 驗證 LangGraph chunk → domain event 翻譯正確 |

**Execution Checklist:**

- [ ] 🔴 寫 `test_mapper.py`：6 組測試（text streaming、tool call lifecycle、tool error、tool progress、text-tool-text transition、finalize）
- [ ] 🔴 執行測試確認 **fail**
- [ ] 🟢 實作 `mapper.py`：`StreamEventMapper` class + `process_chunk()` + `finalize()` + 內部狀態管理
- [ ] 🔵 檢視狀態管理邏輯，確認 text block 和 tool call 生命週期配對正確
- [ ] 🔵 重新執行測試確認 **still pass**
- [ ] 執行 Tasks 2-3 的測試確認無 regression：`pytest backend/tests/streaming/ -v`
- [ ] Commit：`feat(S1): add StreamEventMapper for LangGraph chunk translation`

---

### Flow Verification: Streaming Data Pipeline

> Tasks 2-4 完成了 domain events → serializer → mapper 的 streaming data pipeline。
> 所有驗證必須通過後才進入下一階段。

| # | Method | Step | Expected Result |
|---|---|---|---|
| 1 | Runtime / function invocation | 建立 `StreamEventMapper`，餵入模擬的 text content chunks（`messages` mode），收集所有 domain events，再用 `serialize_event()` 轉為 SSE strings | SSE output 包含正確順序的 `start` → `text-start` → `text-delta` × N → `text-end` → `finish` |
| 2 | Runtime / function invocation | 餵入含 tool call 的 chunk 序列（`messages` + `updates` + `custom` mode），驗證完整 tool lifecycle | SSE output 包含 `tool-call-start` → `tool-call-end` → `data-tool-progress` → `tool-result`，field 名稱正確 |
| 3 | Targeted tests | `pytest backend/tests/streaming/ -v` | 全部通過 |

- [ ] All flow verifications pass

---

### Task 5: Tool Layer — Remove `@observe()`, Add Progress Writer

**Files:**

- Update: `backend/agent_engine/tools/financial.py`
- Update: `backend/agent_engine/tools/sec.py`
- Tests: `backend/tests/tools/test_financial.py`, `backend/tests/tools/test_sec.py`, `backend/tests/tools/test_observe_decorators.py`

**What & Why:** 根據 D5 設計決策，移除 tools 上的 `@observe()` decorator（與 `CallbackHandler` 重複且在 LangGraph 環境下產生 disconnected traces）。同時加入 `get_stream_writer()` 讓 tools 在 streaming context 下發出 progress events。使用 `try/except` 確保非 streaming context（如 `invoke()`）下 gracefully fallback。

**Implementation Notes:**

- 從 `financial.py` 移除 3 個 `@observe()` decorator（`yfinance_stock_quote`、`yfinance_get_available_fields`、`tavily_financial_search`）
- 從 `sec.py` 移除 1 個 `@observe()` decorator（`sec_official_docs_retriever`）
- 移除兩個檔案中的 `from langfuse import observe` import
- 在每個 tool function 開頭加入 progress writer：

```python
from langgraph.config import get_stream_writer

@tool("yfinance_stock_quote", args_schema=YFinanceStockQuoteInput)
def yfinance_stock_quote(ticker: str) -> dict[str, Any]:
    try:
        writer = get_stream_writer()
        writer({"status": "querying_stock", "message": f"查詢 {ticker} 股價...", "toolName": "yfinance_stock_quote"})
    except Exception:
        pass  # Not in streaming context
    # ... existing logic unchanged
```

- Progress payload 遵循 design 定義的格式：`{"status": str, "message": str, "toolName": str}`

| Tool | `status` | `message` 範例 |
|---|---|---|
| `yfinance_stock_quote` | `querying_stock` | `"查詢 {ticker} 股價..."` |
| `yfinance_get_available_fields` | `querying_fields` | `"查詢 {ticker} 可用欄位..."` |
| `tavily_financial_search` | `searching_web` | `"搜尋：{query}..."` |
| `sec_official_docs_retriever` | `retrieving_filing` | `"檢索 {ticker} {doc_type} 報告..."` |

**Test Strategy:** 驗證 (1) 現有 tool 功能不受影響（既有測試必須通過），(2) `@observe()` 確實已移除（如果存在 `test_observe_decorators.py` 中有相關斷言則需更新），(3) progress writer 在非 streaming context 下不 raise。不需 mock `get_stream_writer`——只需確認 try/except fallback 正常。

**Verification:**

| Scope | Command | Expected Result | Why |
|---|---|---|---|
| Targeted | `pytest backend/tests/tools/ -v` | 全部通過 | 移除 `@observe()` 後 tool 功能不受影響 |
| Broader | `pytest backend/tests/ -v --ignore=backend/tests/poc` | 全部通過 | 確認無 regression |

**Execution Checklist:**

- [ ] 讀取 `backend/tests/tools/test_observe_decorators.py` 了解現有 `@observe()` 相關測試
- [ ] 🔴 若有 `@observe()` 相關斷言，更新為斷言 `@observe()` 不存在
- [ ] 🟢 從 `financial.py` 移除 3 個 `@observe()` + import，加入 4 個 tool 的 progress writer（含 try/except fallback）
- [ ] 🟢 從 `sec.py` 移除 1 個 `@observe()` + import，加入 progress writer（含 try/except fallback）
- [ ] 🔵 檢視修改，確認只移除 decorator 和 import，tool 業務邏輯未動
- [ ] 🔵 執行全部測試確認 **still pass**
- [ ] Commit：`refactor(S1): remove @observe() from tools, add stream progress writer`

---

### Task 6: Orchestrator — `astream_run()` + Checkpointer

**Files:**

- Update: `backend/agent_engine/agents/base.py`
- Create: `backend/tests/agents/test_astream_run.py`

**What & Why:** 為 `Orchestrator` 加入 streaming 能力。新增 `astream_run()` 方法，使用 `astream()` 搭配三個 stream mode 和 `StreamEventMapper` 產出 domain events。同時整合 `InMemorySaver` checkpointer 到 `create_agent()` 讓 conversation state 自動管理。

**Implementation Notes:**

- `__init__` 變更：
  - 新增 `from langgraph.checkpoint.memory import InMemorySaver`
  - `self.checkpointer = InMemorySaver()`
  - `create_agent()` 加入 `checkpointer=self.checkpointer`
- `run()` / `arun()` 變更：
  - 在 config 中加入 `"configurable": {"thread_id": str(uuid.uuid4())}`
  - 使用 ephemeral `thread_id` 確保 checkpointer 不影響現有非 streaming 行為（每次都是新 thread）
- `astream_run()` 新增：

```python
async def astream_run(
    self,
    *,
    session_id: str,
    message: str | None = None,
    regenerate: bool = False,
) -> AsyncGenerator[DomainEvent, None]:
    handler = CallbackHandler()
    config: RunnableConfig = {
        "callbacks": [handler],
        "configurable": {"thread_id": session_id},
    }

    with propagate_attributes(session_id=session_id):
        if regenerate:
            # V1: 移除最後一個 assistant turn，重新執行
            state = await self.agent.aget_state(config)
            messages = state.values.get("messages", [])
            trimmed = self._trim_last_assistant_turn(messages)
            await self.agent.aupdate_state(config, {"messages": trimmed})
            input_data = None
        else:
            input_data = {"messages": [{"role": "user", "content": message}]}

        mapper = StreamEventMapper()
        try:
            async for chunk in self.agent.astream(
                input_data,
                config=config,
                stream_mode=["messages", "updates", "custom"],
                version="v2",
            ):
                for event in mapper.process_chunk(chunk):
                    yield event
            for event in mapper.finalize():
                yield event
        except Exception as exc:
            yield StreamError(error_text=str(exc))
            yield Finish(finish_reason="error", usage={"inputTokens": 0, "outputTokens": 0})
```

- `_trim_last_assistant_turn()` 新增：從 messages 末尾往前移除最後一組 assistant 回覆（最後一個 `AIMessage` 及其相關的 `ToolMessage`），直到碰到最後一個 `HumanMessage` 為止
- Regenerate 時 `input_data=None`：agent 從 trimmed state 重新執行

**Test Strategy:** 4 組測試：

1. **Happy path text-only**：mock `agent.astream` 回傳 text chunks → 驗證 `astream_run()` yields `MessageStart` + `TextDelta` + `Finish`
2. **Happy path with tool call**：mock `agent.astream` 回傳 tool call chunks → 驗證完整 tool lifecycle domain events
3. **Exception handling**：mock `agent.astream` raise → 驗證 `StreamError` + `Finish(finish_reason="error")`
4. **Checkpointer integration**：驗證 `run()` 和 `arun()` 在加入 checkpointer 後仍正常工作

不測試 regenerate 的實際 state manipulation（需要更完整的 integration test），只測試 `_trim_last_assistant_turn()` 的邏輯。

**Verification:**

| Scope | Command | Expected Result | Why |
|---|---|---|---|
| Targeted | `pytest backend/tests/agents/test_astream_run.py -v` | 全部通過 | 驗證 streaming 方法正確 |
| Broader | `pytest backend/tests/agents/ -v` | 全部通過（含既有 `test_base.py`, `test_orchestrator_langfuse.py`） | 確認 checkpointer 整合未破壞現有行為 |

**Execution Checklist:**

- [ ] 🔴 寫 `test_astream_run.py`：happy path text、happy path tool call、exception handling、checkpointer 相容性、`_trim_last_assistant_turn()` 邏輯
- [ ] 🔴 執行測試確認 **fail**
- [ ] 🟢 更新 `base.py`：新增 imports、`checkpointer` 初始化、`run()`/`arun()` 加 `thread_id`、實作 `astream_run()` + `_trim_last_assistant_turn()`
- [ ] 🔵 檢視實作，確認 Langfuse 整合正確（`propagate_attributes` + `CallbackHandler`），streaming path 無 `@observe()`
- [ ] 🔵 重新執行 `backend/tests/agents/` 全部測試確認 **still pass**
- [ ] Commit：`feat(S1): add astream_run() with checkpointer and streaming support`

---

### Task 7: FastAPI SSE Endpoint

**Files:**

- Update: `backend/api/routers/chat.py`
- Create: `backend/tests/api/test_chat_stream.py`

**What & Why:** 新增 `POST /api/v1/chat/stream` endpoint，將 `Orchestrator.astream_run()` 的 domain events 透過 SSE serializer 轉換後以 `StreamingResponse` 送出。支援新訊息和 regenerate 兩種 request body。

**Implementation Notes:**

- Request body 定義：

```python
class StreamChatRequest(BaseModel):
    message: str | None = None
    id: str | None = None      # session/chat ID
    trigger: str | None = None  # "regenerate" for regenerate
    messageId: str | None = None  # target message ID for regenerate
```

- Validation：新訊息必須有 `message`；regenerate 必須有 `id` + `trigger="regenerate"`
- Response headers：
  - `Content-Type: text/event-stream`
  - `x-vercel-ai-ui-message-stream: v1`
  - `Cache-Control: no-cache`
  - `X-Accel-Buffering: no`
- Endpoint 邏輯：

```python
@router.post("/chat/stream")
async def chat_stream(body: StreamChatRequest, request: Request, orchestrator = Depends(get_orchestrator)):
    session_id = body.id or str(uuid.uuid4())
    is_regenerate = body.trigger == "regenerate"

    async def event_generator():
        try:
            async for event in orchestrator.astream_run(
                session_id=session_id,
                message=body.message,
                regenerate=is_regenerate,
            ):
                if await request.is_disconnected():
                    break
                yield serialize_event(event)
        except asyncio.CancelledError:
            pass  # Client disconnected

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "x-vercel-ai-ui-message-stream": "v1",
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
```

- 現有 `POST /api/v1/chat` 不修改

**Test Strategy:** 5 組測試：

1. **Endpoint exists**：`POST /api/v1/chat/stream` 回傳非 404
2. **Response headers**：驗證 `Content-Type`, `x-vercel-ai-ui-message-stream`, `Cache-Control`
3. **SSE format**：mock orchestrator，驗證 response body 是有效的 SSE format（`data: {json}\n\n`）
4. **Missing message returns 422**：空 body 或缺 `message` 時回傳 validation error
5. **Existing endpoint untouched**：`POST /api/v1/chat` 仍正常工作

使用 `httpx.AsyncClient` 的 `stream()` 方法或 `TestClient` 讀取 streaming response。

**Verification:**

| Scope | Command | Expected Result | Why |
|---|---|---|---|
| Targeted | `pytest backend/tests/api/test_chat_stream.py -v` | 全部通過 | 驗證 streaming endpoint 正確 |
| Broader | `pytest backend/tests/api/ -v` | 全部通過（含既有 `test_chat.py`） | 確認現有 endpoint 不受影響 |

**Execution Checklist:**

- [ ] 🔴 寫 `test_chat_stream.py`：endpoint exists、headers、SSE format、validation、既有 endpoint 不受影響
- [ ] 🔴 執行測試確認 **fail**
- [ ] 🟢 更新 `chat.py`：新增 `StreamChatRequest` model、`POST /api/v1/chat/stream` endpoint、import serializer + StreamingResponse
- [ ] 🔵 檢視 endpoint 邏輯，確認 disconnect handling 和 error path 正確
- [ ] 🔵 重新執行 `backend/tests/api/` 全部測試確認 **still pass**
- [ ] Commit：`feat(S1): add POST /api/v1/chat/stream SSE endpoint`

---

### Flow Verification: End-to-end Streaming

> Tasks 5-7 完成了 tool changes → orchestrator streaming → HTTP endpoint 的完整串接。
> 所有驗證必須通過後才標記 S1 完成。

| # | Method | Step | Expected Result |
|---|---|---|---|
| 1 | curl | `curl -N -X POST http://localhost:8000/api/v1/chat/stream -H "Content-Type: application/json" -d '{"message": "What is AAPL stock price?"}' 2>&1 \| head -20` | Response headers 含 `content-type: text/event-stream` 和 `x-vercel-ai-ui-message-stream: v1`；body 為 `data: {json}\n\n` 格式；包含 `start` → `text-delta` → `tool-call-start` → `tool-result` → `finish` 事件 |
| 2 | curl | `curl -N -X POST http://localhost:8000/api/v1/chat/stream -H "Content-Type: application/json" -d '{"message": "Hello", "id": "test-session-1"}'` 然後 `curl -N -X POST http://localhost:8000/api/v1/chat/stream -H "Content-Type: application/json" -d '{"message": "What did I just say?", "id": "test-session-1"}'` | 第二個 request 的回覆引用第一個 request 的內容（checkpointer 保持 conversation state） |
| 3 | curl | `curl -X POST http://localhost:8000/api/v1/chat -H "Content-Type: application/json" -d '{"message": "Hello"}'` | 現有 non-streaming endpoint 仍正常回傳 JSON |
| 4 | Trace inspection | 執行 step 1 後檢查 Langfuse dashboard | 一個 request → 一個 trace，tool observations 正確 attach |
| 5 | Targeted tests | `pytest backend/tests/ -v --ignore=backend/tests/poc` | 全部通過 |

- [ ] All flow verifications pass

---

### Task 8: Guardrails Doc Update

**Files:**

- Update: `backend/agent_engine/docs/streaming_observability_guardrails.md`

**What & Why:** 更新 Rule 3，將透過 LangGraph graph 執行的 tools 排除在 `@observe()` 適用範圍外，反映 D5 設計決策。同時記載何時仍需使用 `@observe()`（不透過 LangGraph 框架執行的獨立函數，或 tool 內部有獨立子操作需追蹤時）。

**Implementation Notes:**

- Rule 3 現有文字：
  > Apply `@observe()` only to deterministic functions that complete once and return once.
  > Examples: tools, retrieval helpers, reranking helpers...

- 更新後需在 examples 中區分：
  - **適用** `@observe()`：不透過 LangGraph/LangChain 框架執行的獨立函數（如直接呼叫的 utility function）、tool 內部有獨立子操作需追蹤時（如 tool 內部又呼叫另一個 LLM）
  - **不適用** `@observe()`：透過 `create_agent()` / LangGraph graph 執行的 tools（`CallbackHandler` 已自動 trace）

**Verification:**

| Scope | Command | Expected Result | Why |
|---|---|---|---|
| Targeted | 讀取更新後的文件內容 | Rule 3 明確區分 graph-managed tools 和獨立函數 | 確保後續開發者遵循正確規則 |

**Execution Checklist:**

- [ ] 讀取現有 `streaming_observability_guardrails.md` Rule 3
- [ ] 更新 Rule 3 examples，區分 graph-managed tools 和獨立函數
- [ ] 檢視更新，確認與 D5 研究 Evidence 一致
- [ ] Commit：`docs(S1): update observability guardrails Rule 3 for graph-managed tools`

---

## Pre-delivery Checklist

### Code Level (TDD)

- [ ] Task 2 (Domain Events) 測試通過
- [ ] Task 3 (SSE Serializer) 測試通過
- [ ] Task 4 (StreamEventMapper) 測試通過
- [ ] Task 5 (Tool Changes) 測試通過，含既有 tool 測試
- [ ] Task 6 (Orchestrator astream_run) 測試通過，含既有 orchestrator 測試
- [ ] Task 7 (SSE Endpoint) 測試通過，含既有 API 測試
- [ ] 全部測試：`pytest backend/tests/ -v --ignore=backend/tests/poc` 通過
- [ ] Type check：`pyright backend/` 通過（若 CI 有設定）
- [ ] Lint：`ruff check backend/` 通過

### Flow Level (Behavioral)

- [ ] Flow: Streaming Data Pipeline — PASS / FAIL
- [ ] Flow: End-to-end Streaming — PASS / FAIL

### Summary

- [ ] Both levels pass → ready for delivery
- [ ] Any failure is documented with cause and next action
