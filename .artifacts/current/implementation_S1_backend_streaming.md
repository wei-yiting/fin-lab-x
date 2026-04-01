# Implementation Plan: S1 Backend Streaming

> Design Reference: [`design_master.md`](./design_master.md) (S1 sections, DR-01 ~ DR-07, interface contracts), [`design_S1_backend_streaming_v2.md`](./design_S1_backend_streaming_v2.md)

**Goal:** 在現有 FinLab-X 後端加入 streaming 能力——從 LangGraph agent 取得即時 chunks，經 domain event layer 翻譯為 AI SDK UIMessage Stream Protocol v1 SSE events，透過 FastAPI endpoint 送出。

**Architecture / Key Decisions:**

- 三層 pipeline：LangGraph `astream(stream_mode=["messages","updates","custom"], version="v2")` → `StreamEventMapper`（domain events）→ SSE Serializer（`singledispatch`，wire format）
- Conversation history 由 LangGraph `InMemorySaver` checkpointer 管理，`id` 映射為 `thread_id`（DR-06）
- Tool observability 移除 `@observe()`，改依賴 `CallbackHandler` 自動 trace（D5）；tool progress 透過 `get_stream_writer()`
- Observability POC（Gates 1-6）全數通過後才進入正式實作

**Tech Stack:** FastAPI, LangGraph, LangChain >=1.2.10, Langfuse v4, Python 3.13

---

## Dependencies Verification

| Dependency | Version | Source | What Was Verified | Notes |
|---|---|---|---|---|
| langgraph | >=0.5.0 | Context7 (langchain_oss_python_langgraph) | `astream(stream_mode=[...], version="v2")` 回傳 `{"type": str, "data": Any}` 格式；`InMemorySaver` from `langgraph.checkpoint.memory`；`get_stream_writer()` from `langgraph.config` | 須新增至 pyproject.toml |
| langchain | >=1.2.10 | Context7 (langchain_oss_python_langchain) | `create_agent()` 回傳 `CompiledStateGraph`，支援 `middleware` 參數（`ToolCallLimitMiddleware`）；`handle_tool_errors` 參數存在性待 Task 1 驗證 | 已在 pyproject.toml |
| langfuse | >=4.0.0 | 現有程式碼 | `CallbackHandler`、`propagate_attributes()` per-request tracing | 已在 pyproject.toml |
| fastapi | >=0.115.0 | 現有程式碼 | `StreamingResponse` 支援 async generator + custom headers | 已在 pyproject.toml |

## Constraints

- 現有 `POST /api/v1/chat` endpoint 不得修改（既有測試全數通過）
- 不在 async generator 或 SSE serializer 上使用 `@observe()`（`streaming_observability_guardrails.md` Rule 3-4）
- V1 不支援 tool input streaming（無 `tool-call-delta`）
- V1 只支援 regenerate 最後一條 assistant message
- V1 conversation store 為 in-memory（process 重啟消失，DD-06 accepted behavior）
- SSE output 中的 tool error message 必須經過 sanitization（過濾 API keys、internal paths、stack traces）

---

## File Plan

| Operation | Path | Purpose |
|---|---|---|
| Create | `backend/agent_engine/streaming/__init__.py` | Streaming package init |
| Create | `backend/agent_engine/streaming/domain_events.py` | 11 frozen dataclasses — mapper 與 serializer 的共用契約 |
| Create | `backend/agent_engine/streaming/event_mapper.py` | `StreamEventMapper`：LangGraph chunks → domain events |
| Create | `backend/agent_engine/streaming/sse_serializer.py` | `singledispatch` SSE serializer：domain events → wire format |
| Create | `backend/agent_engine/streaming/error_sanitizer.py` | Tool error sanitization utility |
| Create | `backend/api/routers/chat_stream.py` | `POST /api/v1/chat/stream` endpoint + per-session lock |
| Create | `backend/tests/streaming/__init__.py` | Test package init |
| Create | `backend/tests/streaming/test_domain_events.py` | Domain event unit tests |
| Create | `backend/tests/streaming/test_event_mapper.py` | StreamEventMapper unit tests |
| Create | `backend/tests/streaming/test_sse_serializer.py` | SSE serializer unit tests |
| Create | `backend/tests/streaming/test_error_sanitizer.py` | Error sanitizer unit tests |
| Create | `backend/tests/api/test_chat_stream.py` | Streaming endpoint tests |
| Create | `backend/tests/streaming/test_poc_observability.py` | POC gate verification tests（`@pytest.mark.poc`） |
| Update | `pyproject.toml` | 新增 `langgraph` dependency |
| Update | `backend/agent_engine/agents/base.py` | 新增 `astream_run()`、checkpointer 初始化、regenerate |
| Update | `backend/agent_engine/tools/financial.py` | 移除 `@observe()`、新增 `get_stream_writer()` progress |
| Update | `backend/agent_engine/tools/sec.py` | 移除 `@observe()`、新增 `get_stream_writer()` progress |
| Update | `backend/api/main.py` | Include `chat_stream` router |
| Update | `backend/tests/tools/test_observe_decorators.py` | 反轉：驗證 tools 不再有 `@observe()` |
| Update | `backend/tests/agents/test_orchestrator_langfuse.py` | 新增 `astream_run` tracing tests |
| Update | `backend/agent_engine/docs/streaming_observability_guardrails.md` | 更新 Rule 3 |

**Structure sketch:**

```text
backend/
  agent_engine/
    streaming/                      # NEW
      __init__.py
      domain_events.py
      event_mapper.py
      sse_serializer.py
      error_sanitizer.py
    agents/
      base.py                       # UPDATE
    tools/
      financial.py                  # UPDATE
      sec.py                        # UPDATE
    docs/
      streaming_observability_guardrails.md  # UPDATE
  api/
    routers/
      chat_stream.py                # NEW
    main.py                         # UPDATE
  tests/
    streaming/                      # NEW
      __init__.py
      test_domain_events.py
      test_event_mapper.py
      test_sse_serializer.py
      test_error_sanitizer.py
      test_poc_observability.py
    api/
      test_chat_stream.py           # NEW
    tools/
      test_observe_decorators.py    # UPDATE
    agents/
      test_orchestrator_langfuse.py # UPDATE
```

---

### Task 1: Add `langgraph` Dependency & Verify Integration

**Files:**

- Update: `pyproject.toml`

**What & Why:** `langgraph` 是 `astream()`、`InMemorySaver`、`get_stream_writer()` 的來源。雖然 `langchain` 內部可能 transitively 依賴 `langgraph`，但本專案需直接 import 這些 API，必須顯式宣告。本 task 同時驗證 `create_agent()` 回傳的 graph 是否支援 `checkpointer` 參數及 `astream()` 方法。

**Implementation Notes:**

- 在 `pyproject.toml` 的 `dependencies` 加入 `langgraph>=0.5.0`
- 驗證以下 import 可正常執行：
  - `from langgraph.checkpoint.memory import InMemorySaver`
  - `from langgraph.config import get_stream_writer`
- 驗證 `create_agent()` 是否接受 `checkpointer` 參數：
  - 嘗試 `create_agent(..., checkpointer=InMemorySaver())` 並呼叫 `astream()`
  - 若不支援，嘗試 `agent.get_graph().compile(checkpointer=InMemorySaver())` 重新 compile
  - 若兩者都不可行，記錄需使用 `langgraph.prebuilt.create_react_agent` 替代 `langchain.agents.create_agent`
  - **同時驗證** `create_agent()` 是否支援 `handle_tool_errors` 參數（作為未預期 tool exception 的安全網）
  - 將驗證結果記錄在 commit message 中，Task 7 依此選擇路徑
- 執行 `uv sync` 確認 dependency resolution 無衝突

**Verification:**

| Scope | Command | Expected Result | Why |
|---|---|---|---|
| Dependency install | `cd backend && uv sync` | 安裝成功，無 version conflict | 確認 langgraph 與現有 deps 相容 |
| Import check | `python -c "from langgraph.checkpoint.memory import InMemorySaver; from langgraph.config import get_stream_writer; print('OK')"` | 輸出 `OK` | 確認核心 API 可用 |
| Existing tests | `cd backend && python -m pytest tests/ -x -q` | 全部通過 | 確認新 dependency 不破壞既有 code |

**Execution Checklist:**

- [ ] 更新 `pyproject.toml` 加入 `langgraph>=0.5.0`
- [ ] 執行 `uv sync`
- [ ] 驗證 import 正常
- [ ] 驗證 `create_agent()` + `checkpointer` 整合方式（記錄在 commit message）
- [ ] 確認既有測試全數通過
- [ ] Commit: `git commit -m "chore(s1): add langgraph dependency"`

---

### Task 2: Observability POC (Gates 1-6)

**Files:**

- Create: `backend/tests/streaming/__init__.py`
- Create: `backend/tests/streaming/test_poc_observability.py`

**What & Why:** Design 要求 POC 全數通過後才進入正式實作。本 task 用最簡單的 `astream()` + `CallbackHandler` 組合驗證 6 個 gate，確認 streaming 路徑上的 observability 基礎設施可靠。Gate 失敗則需重新評估方案。

**Implementation Notes:**

- 使用 `@pytest.mark.poc` marker，讓 CI 可選擇性跳過（需真實 Langfuse credentials）
- 每個 gate 一個獨立 test function
- Gate 1-5 只需 Langfuse；Gate 6 額外需要 Braintrust
- 驗證方式：透過 Langfuse Python SDK `langfuse.Langfuse()` client 查詢 trace，assert 結構正確

**POC 測試骨架（每個 gate 的核心 assert）：**

| Gate | Test Function | 驗證邏輯 |
|---|---|---|
| 1 | `test_single_request_single_trace` | 呼叫 `astream()` → **flush handler** → 查詢 Langfuse，確認 session 只有 1 個 top-level trace |
| 2 | `test_tool_observation_attached` | 用含 tool call 的 prompt → flush → 確認 tool observation 是 trace 的 child，非獨立 trace |
| 3 | `test_disconnect_clean_close` | 用 `asyncio.timeout()` 提前中斷 → flush → 確認 trace 有 end_time、無 orphan child |
| 4 | `test_exception_visible` | 注入 tool exception → flush → 確認 trace status 為 error、SSE output 含 error event |
| 5 | `test_concurrent_no_contamination` | 3 個並發 `astream()` 各用不同 session_id → flush → 確認 3 個獨立 trace、session_id 不交叉 |
| 6 | `test_braintrust_langfuse_coexistence` | `set_global_handler(BraintrustCallbackHandler())` + Langfuse per-request → flush → 兩平台各自完整 trace |

**關鍵注意事項 — Langfuse flush timing：** Langfuse trace ingestion 是非同步的，`astream()` 結束後 trace 可能尚未入庫。每個 gate test 在 assert 前必須呼叫 `handler.flush()`（`CallbackHandler` 實例方法）或 `langfuse_client.flush()` 確保 trace 已送達，否則會出現 intermittent failures。

- Gate 6 失敗的 fallback：eval task function 退回使用 `run()`（非 streaming），不影響 API server streaming 路徑。在測試中記錄結果，不 block 後續實作。

**Test Strategy:** 這些是 integration tests，驗證 Langfuse 在 streaming 路徑下的行為。每個 test 都是一個 gate，直接呼叫 Langfuse SDK 查詢 trace metadata。Gate 6 另需 Braintrust SDK。

**Verification:**

| Scope | Command | Expected Result | Why |
|---|---|---|---|
| POC Gates 1-5 | `cd backend && python -m pytest tests/streaming/test_poc_observability.py -m poc -k "not braintrust" -v` | 5 tests PASSED | Langfuse streaming tracing 基礎可靠 |
| POC Gate 6 | `cd backend && python -m pytest tests/streaming/test_poc_observability.py -m poc -k "braintrust" -v` | PASSED 或 XFAIL（附 fallback 記錄） | Braintrust 共存驗證 |
| Langfuse UI | 手動檢查 Langfuse dashboard | Trace 結構可視化確認 | 補充自動化 assert 可能遺漏的細節 |

**Execution Checklist:**

- [ ] 建立 `backend/tests/streaming/__init__.py` 和 `test_poc_observability.py`
- [ ] 實作 Gate 1-5 test functions
- [ ] 實作 Gate 6 test function（含 xfail fallback）
- [ ] 執行 POC，全部 gate 通過（或 Gate 6 記錄 fallback）
- [ ] Commit: `git commit -m "test(s1): observability POC gates 1-6"`

---

### Flow Verification: Observability POC

> Task 2 完成 POC 驗證。**所有 Gate（1-5 必須通過，Gate 6 允許 fallback）必須確認後才能進入 Task 3+。**

| # | Method | Step | Expected Result |
|---|---|---|---|
| 1 | Runtime / function invocation | 執行 POC test suite | Gates 1-5 PASSED |
| 2 | Trace inspection | 在 Langfuse UI 確認 trace 結構 | 每個 gate 的 trace 符合預期 |
| 3 | Runtime / function invocation | 執行 Gate 6 | PASSED 或 XFAIL with documented fallback |

- [ ] All flow verifications pass

---

### Task 3: Domain Events & Error Sanitizer

**Files:**

- Create: `backend/agent_engine/streaming/__init__.py`
- Create: `backend/agent_engine/streaming/domain_events.py`
- Create: `backend/agent_engine/streaming/error_sanitizer.py`
- Create: `backend/tests/streaming/test_domain_events.py`
- Create: `backend/tests/streaming/test_error_sanitizer.py`

**What & Why:** Domain events 是 `StreamEventMapper` 和 SSE Serializer 之間的共用契約。Error sanitizer 是 tool error → SSE 路徑上的 sanitization boundary。兩者皆為純值物件 / 純函數，無外部依賴，可獨立測試。

**Critical Contract:**

```python
from dataclasses import dataclass, field

@dataclass(frozen=True)
class MessageStart:
    message_id: str
    session_id: str

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
    data: dict

@dataclass(frozen=True)
class StreamError:
    error_text: str

@dataclass(frozen=True)
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0

@dataclass(frozen=True)
class Finish:
    finish_reason: str
    usage: Usage = field(default_factory=Usage)

# Union type for type hints
DomainEvent = (
    MessageStart | TextStart | TextDelta | TextEnd
    | ToolCallStart | ToolCallEnd | ToolResult | ToolError | ToolProgress
    | StreamError | Finish
)
```

**Error sanitizer contract:**

```python
def sanitize_tool_error(raw_error: str) -> str:
    """移除 API keys、internal paths/hostnames、connection strings、stack traces。
    保留足夠描述讓使用者理解（如 'yfinance API timeout'）。"""
```

**Test Strategy:**

- Domain events：驗證 frozen 不可變性、正確建構、equality
- Error sanitizer：
  - 含 API key 的 error → key 被移除
  - 含 internal path 的 error → path 被移除
  - 含 stack trace 的 error → 只保留最後一行描述
  - 含 connection string 的 error → 被清除
  - 正常 error message（如 "API timeout"）→ 保持不變

**Verification:**

| Scope | Command | Expected Result | Why |
|---|---|---|---|
| Unit tests | `cd backend && python -m pytest tests/streaming/test_domain_events.py tests/streaming/test_error_sanitizer.py -v` | All PASSED | 核心契約正確 |
| Type check | `cd backend && pyright backend/agent_engine/streaming/` | 無 error | 型別定義正確 |

**Execution Checklist:**

- [ ] 🔴 撰寫 domain events tests（frozen、建構、equality）
- [ ] 🔴 撰寫 error sanitizer tests（API key、path、stack trace、connection string、normal message）
- [ ] 🔴 執行測試，確認全部 **fail**
- [ ] 🟢 實作 `domain_events.py`（frozen dataclasses）和 `error_sanitizer.py`（regex-based sanitization）
- [ ] 🟢 執行測試，確認全部 **pass**
- [ ] 🔵 Review：命名一致性、是否遺漏 edge case
- [ ] 🔵 執行測試，確認 refactor 後仍 **pass**
- [ ] Commit: `git commit -m "feat(s1): add domain events and error sanitizer"`

---

### Task 4: SSE Serializer

**Files:**

- Create: `backend/agent_engine/streaming/sse_serializer.py`
- Create: `backend/tests/streaming/test_sse_serializer.py`

**What & Why:** SSE Serializer 將 domain events 轉為 AI SDK UIMessage Stream Protocol v1 wire format（`data: {json}\n\n`）。使用 `functools.singledispatch` 讓每個 event type 獨立 register，擴展時不改既有 code。

**Critical Contract:**

```python
import functools
import json

@functools.singledispatch
def serialize_event(event) -> str:
    raise TypeError(f"Unhandled event type: {type(event).__name__}")

@serialize_event.register
def _(event: MessageStart) -> str:
    payload = {"type": "start", "messageId": event.message_id, "sessionId": event.session_id}
    return f"data: {json.dumps(payload)}\n\n"

# ToolProgress 需加 "transient": true
@serialize_event.register
def _(event: ToolProgress) -> str:
    payload = {"type": "data-tool-progress", "toolCallId": event.tool_call_id, "data": event.data, "transient": True}
    return f"data: {json.dumps(payload)}\n\n"

# Finish 包含 usage
@serialize_event.register
def _(event: Finish) -> str:
    payload = {"type": "finish", "finishReason": event.finish_reason, "usage": {"inputTokens": event.usage.input_tokens, "outputTokens": event.usage.output_tokens}}
    return f"data: {json.dumps(payload)}\n\n"
```

**欄位映射規則**（serializer 負責 snake_case → camelCase）：

| Domain Event 欄位 | Wire format 欄位 |
|---|---|
| `message_id` | `messageId` |
| `session_id` | `sessionId` |
| `text_id` | `id` |
| `tool_call_id` | `toolCallId` |
| `tool_name` | `toolName` |
| `error_text` | `errorText` |
| `finish_reason` | `finishReason` |

**Test Strategy:**

- 每個 event type 一個 test：建構 domain event → 呼叫 `serialize_event()` → assert output 為正確的 `data: {json}\n\n` 格式
- 驗證 JSON 中的 key name 為 camelCase
- 驗證 ToolProgress 帶 `"transient": true`
- 驗證 ToolError 使用 `"data-tool-error"` type（非標準 event）
- 驗證 unknown event type → `TypeError`
- 驗證 JSON special characters（引號、換行）正確 escape

**Verification:**

| Scope | Command | Expected Result | Why |
|---|---|---|---|
| Unit tests | `cd backend && python -m pytest tests/streaming/test_sse_serializer.py -v` | All PASSED | Wire format 符合 protocol spec |

**Execution Checklist:**

- [ ] 🔴 撰寫 tests：11 event types + unknown type + special chars
- [ ] 🔴 確認 **fail**
- [ ] 🟢 實作 `sse_serializer.py`（singledispatch + 所有 register）
- [ ] 🟢 確認 **pass**
- [ ] 🔵 Review：是否有遺漏的欄位映射、JSON edge case
- [ ] 🔵 確認 refactor 後 **pass**
- [ ] Commit: `git commit -m "feat(s1): add SSE serializer with singledispatch"`

---

### Task 5: StreamEventMapper

**Files:**

- Create: `backend/agent_engine/streaming/event_mapper.py`
- Create: `backend/tests/streaming/test_event_mapper.py`

**What & Why:** `StreamEventMapper` 是有狀態的翻譯器，將 LangGraph `astream(version="v2")` 的 raw chunks 翻譯為 domain events。它處理三件 LangGraph 不做的事：(1) 補上 `text-start`/`text-end` 配對、(2) `MessageStart`/`Finish` framing、(3) 跨 stream mode 拼湊 tool call 生命週期。

**LangGraph v2 Chunk 格式**（來自 Context7 驗證）：

| `chunk["type"]` | `chunk["data"]` | 對應 Domain Event |
|---|---|---|
| `"messages"` | `(AIMessageChunk, metadata)` — `content` 非空 | `TextDelta`（mapper 補 `TextStart`/`TextEnd`） |
| `"messages"` | `(AIMessageChunk, metadata)` — `tool_call_chunks` 非空 | `ToolCallStart`（首次出現該 tool_call_id 時） |
| `"updates"` | `{node_name: state_update}` — agent node 完成 | `ToolCallEnd`（從 `AIMessage.tool_calls` 取 ID） |
| `"updates"` | `{node_name: state_update}` — tool node 完成，`ToolMessage` | `ToolResult` 或 `ToolError`（依 `status` 判斷） |
| `"custom"` | `{data}` from `get_stream_writer()` | `ToolProgress` |

**Mapper 狀態追蹤：**

```
state:
  message_started: bool         # MessageStart 是否已 emit
  text_block_open: bool         # 當前是否在 text block 中
  current_text_id: str | None   # 當前 text block ID
  pending_tool_calls: dict[str, str]  # tool_call_id → tool_name
  text_id_counter: int          # text block ID 生成器
  total_input_tokens: int       # 累計 input tokens
  total_output_tokens: int      # 累計 output tokens
```

**關鍵轉換邏輯（pseudo code）：**

```
process_chunk(chunk):
  if not message_started:
    yield MessageStart(message_id, session_id)
    message_started = true

  match chunk["type"]:
    case "messages":
      msg_chunk, metadata = chunk["data"]
      if msg_chunk.content:                    # 文字 token
        if not text_block_open:
          current_text_id = next_text_id()
          yield TextStart(current_text_id)
          text_block_open = true
        yield TextDelta(current_text_id, msg_chunk.content)
      if msg_chunk.tool_call_chunks:           # tool call 開始
        if text_block_open:
          yield TextEnd(current_text_id)
          text_block_open = false
        for tc in msg_chunk.tool_call_chunks:
          if tc["id"] not in pending_tool_calls:
            pending_tool_calls[tc["id"]] = tc["name"]
            yield ToolCallStart(tc["id"], tc["name"])
      # 累計 usage：AIMessageChunk.usage_metadata 是 dict，含 input_tokens / output_tokens / total_tokens

    case "updates":
      for node_name, update in chunk["data"].items():
        messages = update.get("messages", [])
        for msg in messages:
          if is AIMessage with tool_calls:     # agent node 完成
            for tc in msg.tool_calls:
              yield ToolCallEnd(tc["id"])
          if is ToolMessage:                   # tool node 完成
            if msg.status == "error":
              yield ToolError(msg.tool_call_id, sanitize_tool_error(msg.content))
            elif is_error_result(msg.content):  # {"error": True, "message": "..."}
              yield ToolError(msg.tool_call_id, sanitize_tool_error(parse_error_message(msg.content)))
            else:
              yield ToolResult(msg.tool_call_id, msg.content)
            pending_tool_calls.pop(msg.tool_call_id, None)

    case "custom":
      data = chunk["data"]
      tool_name = data.get("toolName")
      # V1: 用 toolName 反查 pending_tool_calls 取得 tool_call_id
      tool_call_id = reverse_lookup(pending_tool_calls, tool_name)
      if tool_call_id:
        yield ToolProgress(tool_call_id, data)

finalize():
  if text_block_open:
    yield TextEnd(current_text_id)
  yield Finish("stop", Usage(total_input_tokens, total_output_tokens))
```

**Test Strategy:**

以 mock LangGraph chunks 驅動 mapper，驗證 domain event 輸出。不需真實 LLM。

- **Happy path — 純文字回覆**：`messages` chunks with content → `MessageStart` + `TextStart` + `TextDelta`* + `TextEnd` + `Finish`
- **Happy path — 含 tool call**：text chunks → tool_call_chunks → agent update → tool update → more text → finish → 完整事件序列
- **Tool error — status="error"**：tool update with `ToolMessage(status="error")` → `ToolError`（sanitized）
- **Tool error — error result dict**：tool update with `ToolMessage(content='{"error":true,"message":"API timeout"}')` → `ToolError`（sanitized）
- **Tool progress**：custom chunk → `ToolProgress`（配對到 pending tool call）
- **Multiple text blocks**：text → tool → text → 兩個 `TextStart`/`TextEnd` 配對
- **MessageStart 只 emit 一次**
- **Text block auto-close on tool call**
- **Finalize closes open text block**
- **Usage accumulation**

**Verification:**

| Scope | Command | Expected Result | Why |
|---|---|---|---|
| Unit tests | `cd backend && python -m pytest tests/streaming/test_event_mapper.py -v` | All PASSED | Mapper 正確翻譯所有 chunk 組合 |

**Execution Checklist:**

- [ ] 🔴 撰寫 tests：happy path（text-only、text+tool）、tool error、tool progress、multi text block、edge cases
- [ ] 🔴 確認 **fail**
- [ ] 🟢 實作 `event_mapper.py`（`StreamEventMapper` class）
- [ ] 🟢 確認 **pass**
- [ ] 🔵 Review：state 管理是否完整、edge case coverage
- [ ] 🔵 確認 refactor 後 **pass**
- [ ] Commit: `git commit -m "feat(s1): add StreamEventMapper for LangGraph chunk translation"`

---

### Flow Verification: Streaming Pipeline Unit Tests

> Tasks 3-5 完成 streaming pipeline 的純邏輯元件（domain events → mapper → serializer）。

| # | Method | Step | Expected Result |
|---|---|---|---|
| 1 | Runtime / function invocation | `cd backend && python -m pytest tests/streaming/ -v --ignore=tests/streaming/test_poc_observability.py` | All tests PASSED |
| 2 | Runtime / function invocation | 建構 mock chunks → 餵入 mapper → 輸出 domain events → 餵入 serializer → 驗證 SSE wire format | 完整 pipeline 產出符合 protocol spec 的 SSE strings |

- [ ] All flow verifications pass

---

### Task 6: Tool Changes — 移除 `@observe()`、新增 Progress Writer

**Files:**

- Update: `backend/agent_engine/tools/financial.py`
- Update: `backend/agent_engine/tools/sec.py`
- Update: `backend/tests/tools/test_observe_decorators.py`

**What & Why:** Design D5 要求移除 tools 上的 `@observe()`，因為 `CallbackHandler` 已自動 trace tool calls，`@observe()` 在 LangGraph 環境下反而產生 disconnected traces。同時加入 `get_stream_writer()` 讓 tools 發送 progress events。

**Implementation Notes:**

- 移除所有 tool 函數上的 `@observe(name=...)` decorator 和 `from langfuse import observe` import
- 在每個 tool 開頭加入 `get_stream_writer()` + try/except graceful fallback（非 streaming context 下 `get_stream_writer()` 會 raise，需 catch）：

```python
from langgraph.config import get_stream_writer

@tool("yfinance_stock_quote", args_schema=YFinanceStockQuoteInput)
def yfinance_stock_quote(ticker: str) -> dict[str, Any]:
    try:
        writer = get_stream_writer()
    except Exception:
        writer = None

    normalized_ticker = ticker.strip().upper()
    if writer:
        writer({"status": "querying_stock", "message": f"查詢 {normalized_ticker} 股價...", "toolName": "yfinance_stock_quote"})
    # ... existing logic ...
```

- 更新 `test_observe_decorators.py`：反轉驗證邏輯，確認 tools **不再有** `@observe()` wrapper

**Test Strategy:**

- 驗證 tools 不再有 `__wrapped__` attribute（`@observe()` 設的）
- 驗證 tool schema 未被 progress writer 改變
- 驗證非 streaming context 下 tool 仍正常執行（`get_stream_writer()` graceful fallback）

**Verification:**

| Scope | Command | Expected Result | Why |
|---|---|---|---|
| Tool tests | `cd backend && python -m pytest tests/tools/ -v` | All PASSED | Tools 正確移除 @observe 且 schema 完整 |
| Existing tests | `cd backend && python -m pytest tests/ -x -q --ignore=tests/streaming/test_poc_observability.py` | All PASSED | 移除 @observe 不破壞既有功能 |

**Execution Checklist:**

- [ ] 🔴 更新 `test_observe_decorators.py`：反轉 assert（verify no `__wrapped__`）
- [ ] 🔴 確認 **fail**（因為 tools 仍有 @observe）
- [ ] 🟢 移除 `financial.py` 和 `sec.py` 中的 `@observe()` 和 import；加入 `get_stream_writer()` progress
- [ ] 🟢 確認 tool tests **pass**
- [ ] 🔵 Review：fallback pattern 一致性
- [ ] 🔵 確認 refactor 後 **pass**
- [ ] 執行完整 test suite 確認無 regression
- [ ] Commit: `git commit -m "refactor(s1): remove @observe from tools, add stream progress writer"`

---

### Task 7: `Orchestrator.astream_run()` + Checkpointer

**Files:**

- Update: `backend/agent_engine/agents/base.py`
- Update: `backend/tests/agents/test_orchestrator_langfuse.py`

**What & Why:** 核心 streaming method。設定 `InMemorySaver` checkpointer 管理對話狀態，用 `astream()` 取得 chunks，交給 `StreamEventMapper` 翻譯為 domain events。包含 regenerate 支援（V1 只支援最後一條 assistant message）。

**Implementation Notes:**

- 在 `Orchestrator.__init__` 中初始化 `InMemorySaver` 並整合至 agent。**Task 1 已驗證整合方式**，依結果選擇以下路徑：

  **路徑 A（優先）**：`create_agent(..., checkpointer=checkpointer)` — 若 `create_agent` 接受 checkpointer 參數
  
  **路徑 B（fallback）**：`create_agent()` 回傳的 compiled graph 不含 checkpointer → 呼叫 `agent.get_graph().compile(checkpointer=checkpointer)` 重新 compile，或在 init 中直接使用 LangGraph `StateGraph` + `create_react_agent` 替代 `create_agent`
  
  不論走哪條路徑，最終 `self.agent` 必須支援 `astream()`、`aget_state()`、`aupdate_state()` 方法
- **Tool error 偵測策略（已解決）**：

  現有 tools 已在內部 catch exceptions 並回傳 `{"error": True, "message": "..."}` dict。這些是正常的 `ToolResult`（LangGraph 視為成功的 tool call）。`StreamEventMapper` 負責偵測 error pattern 並轉為 `ToolError` domain event：

  | 來源 | Mapper 偵測方式 | 產出 |
  |---|---|---|
  | Tool 內部 try/except → `{"error": True, "message": "..."}` | 解析 `ToolMessage.content` JSON，檢查 `error` key | `ToolError`（sanitized） |
  | Tool 未預期 exception（未被 catch） | `ToolMessage.status == "error"`（若 `create_agent` 支援 `handle_tool_errors`）；否則 exception 會 propagate 成 `StreamError` | `ToolError` 或 `StreamError` |

  **不使用 `@wrap_tool_call` middleware**——Context7 查到的此 API 可能非標準 export，改用 mapper-side 偵測更穩定。Task 1 驗證 `create_agent()` 是否支援 `handle_tool_errors` 參數作為未預期 exception 的安全網。

- 新增 `astream_run()` async generator：

```python
async def astream_run(
    self,
    *,
    message: str | None = None,
    session_id: str,
    trigger: str | None = None,
    message_id: str | None = None,
) -> AsyncGenerator[DomainEvent, None]:
    config, propagation = self._build_langfuse_config(session_id=session_id)
    config["configurable"] = {"thread_id": session_id}
    mapper = StreamEventMapper(session_id=session_id)

    if trigger == "regenerate":
        await self._prepare_regenerate(config, message_id)
        input_data = None  # re-run from truncated state
    else:
        input_data = {"messages": [{"role": "user", "content": message}]}

    with propagate_attributes(**propagation):
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
        except Exception as e:
            yield StreamError(error_text=str(e))
            yield Finish(finish_reason="error")
```

- Regenerate 流程（V1 只支援最後一條）：

```python
async def _prepare_regenerate(self, config: dict, message_id: str | None) -> None:
    state = await self.agent.aget_state(config)
    messages = state.values.get("messages", [])
    # 找到最後一個 AIMessage（非 tool call 的）
    last_ai_idx = None
    for i in reversed(range(len(messages))):
        if isinstance(messages[i], AIMessage):
            last_ai_idx = i
            break
    if last_ai_idx is None:
        raise ValueError("No assistant message to regenerate")
    # 驗證 messageId（如果提供）
    if message_id and messages[last_ai_idx].id != message_id:
        raise ValueError("messageId does not match last assistant message")
    # 移除最後 assistant turn（AIMessage + 後續 ToolMessages）
    trimmed = messages[:last_ai_idx]
    await self.agent.aupdate_state(config, {"messages": trimmed})
```

**Test Strategy:**

用 mock agent 驗證 `astream_run()` 的行為。不需真實 LLM。

- **Happy path**：mock `agent.astream()` yield 預設 chunks → 驗證 domain event 序列正確（`MessageStart` → `TextDelta`* → `Finish`）
- **Checkpointer config**：驗證 `astream()` 被呼叫時 config 含 `configurable.thread_id`
- **Langfuse injection**：驗證 `CallbackHandler` 在 config 中、`propagate_attributes` 被呼叫
- **Regenerate**：mock state with messages → 呼叫 regenerate → 驗證 state 被正確 truncate
- **Regenerate messageId mismatch**：→ `ValueError`
- **Exception handling**：mock `astream()` raise → 驗證 yields `StreamError` + `Finish("error")`
- **Checkpointer config**：驗證 `InMemorySaver` 被正確設定，`aget_state()` / `aupdate_state()` 可用

**Verification:**

| Scope | Command | Expected Result | Why |
|---|---|---|---|
| Unit tests | `cd backend && python -m pytest tests/agents/test_orchestrator_langfuse.py -v` | All PASSED（含新 tests） | astream_run 行為正確 |
| Existing tests | `cd backend && python -m pytest tests/ -x -q --ignore=tests/streaming/test_poc_observability.py` | All PASSED | 不破壞 run/arun |

**Execution Checklist:**

- [ ] 🔴 撰寫 `astream_run` tests：happy path、checkpointer config、Langfuse injection、regenerate、regenerate mismatch、exception handling
- [ ] 🔴 確認 **fail**
- [ ] 🟢 實作：checkpointer init、`handle_tool_errors` 參數（若 Task 1 確認可用）、`astream_run()`、`_prepare_regenerate()`
- [ ] 🟢 確認 **pass**
- [ ] 🔵 Review：error handling path、state management、Langfuse lifecycle
- [ ] 🔵 確認 refactor 後 **pass**
- [ ] 確認 `run()` 和 `arun()` 既有 tests 仍 pass
- [ ] Commit: `git commit -m "feat(s1): add Orchestrator.astream_run with checkpointer and regenerate"`

---

### Task 8: Streaming Endpoint

**Files:**

- Create: `backend/api/routers/chat_stream.py`
- Create: `backend/tests/api/test_chat_stream.py`
- Update: `backend/api/main.py`

**What & Why:** `POST /api/v1/chat/stream` endpoint。接收 request → 驗證 → 取得 session lock → 呼叫 `astream_run()` → 透過 serializer 輸出 SSE → `StreamingResponse` 送出。

**Critical Contract — Request Model:**

```python
from pydantic import BaseModel, Field
from typing import Literal

class StreamChatRequest(BaseModel):
    id: str = Field(..., min_length=1)
    message: str | None = None
    trigger: Literal["regenerate"] | None = None
    messageId: str | None = None  # regenerate 時必填
```

**Implementation Notes:**

- Per-session non-blocking lock（DD-03）：

```python
import asyncio

_session_locks: dict[str, asyncio.Lock] = {}

# In endpoint:
lock = _session_locks.setdefault(body.id, asyncio.Lock())
if lock.locked():
    raise HTTPException(status_code=409, detail="Session busy")
```

  **V1 accepted limitation：** `_session_locks` dict 會隨 session 數量增長，不主動清理。與 DD-06（InMemorySaver 重啟消失）一致——process 重啟即清零。V2 可加 TTL-based cleanup。

- Request 驗證規則（用 Pydantic `@model_validator(mode="after")` 實作互斥檢查）：
  - `id` 必填且非空（`Field(..., min_length=1)` 處理）
  - 同時有 `message` 和 `trigger` → 422
  - 無 `message` 也無 `trigger` → 422
  - `trigger="regenerate"` 時 `messageId` 必填 → 422
- Response headers（master design 介面契約）：

```python
return StreamingResponse(
    generate(),
    media_type="text/event-stream",
    headers={
        "x-vercel-ai-ui-message-stream": "v1",
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
    },
)
```

- Client disconnect handling：

```python
async def generate():
    async with lock:
        async for event in orchestrator.astream_run(...):
            if await request.is_disconnected():
                break
            yield serialize_event(event)
```

- 在 `main.py` 中 include 新 router

**Test Strategy:**

用 mock orchestrator 驗證 endpoint 的 HTTP 行為。不需真實 streaming。

- **Happy path**：mock `astream_run` yields events → 驗證 response status 200、content-type、headers、body 為 SSE 格式
- **id 空字串**：→ 422
- **id 缺失**：→ 422
- **message + trigger 同時存在**：→ 422
- **無 message 也無 trigger**：→ 422
- **regenerate 缺 messageId**：→ 422
- **Session lock（409）**：同 session 兩個並發 request → 第二個得到 409
- **Regenerate messageId mismatch**：orchestrator raises `ValueError` → endpoint 回 422
- **Orchestrator exception**：→ SSE 中有 error + finish events（不是 HTTP 500）
- **既有 /chat endpoint 不受影響**

**Verification:**

| Scope | Command | Expected Result | Why |
|---|---|---|---|
| Endpoint tests | `cd backend && python -m pytest tests/api/test_chat_stream.py -v` | All PASSED | Endpoint 行為符合介面契約 |
| Existing endpoint | `cd backend && python -m pytest tests/api/test_chat.py -v` | All PASSED | /chat 不受影響 |
| Full suite | `cd backend && python -m pytest tests/ -x -q --ignore=tests/streaming/test_poc_observability.py` | All PASSED | 無 regression |

**Execution Checklist:**

- [ ] 🔴 撰寫 endpoint tests：happy path、validation errors（422）、session lock（409）、regenerate、exception handling
- [ ] 🔴 確認 **fail**
- [ ] 🟢 實作 `chat_stream.py`（request model、validation、session lock、streaming response）
- [ ] 🟢 更新 `main.py` include 新 router
- [ ] 🟢 確認 **pass**
- [ ] 🔵 Review：error path completeness、header 正確性、lock cleanup
- [ ] 🔵 確認 refactor 後 **pass**
- [ ] 確認 `/chat` 既有 tests 仍 pass
- [ ] Commit: `git commit -m "feat(s1): add POST /api/v1/chat/stream endpoint"`

---

### Flow Verification: End-to-end Streaming

> Tasks 6-8 完成從 tool 變更到 endpoint 的完整 streaming 功能。

| # | Method | Step | Expected Result |
|---|---|---|---|
| 1 | curl | `curl -N -X POST http://localhost:8000/api/v1/chat/stream -H "Content-Type: application/json" -d '{"id":"test-session","message":"TSMC 最近表現如何？"}'` | Status 200；response headers 含 `x-vercel-ai-ui-message-stream: v1`；body 為 `data: {json}\n\n` 格式的 SSE events，包含 `start` → `text-start` → `text-delta`* → `text-end` → `finish` |
| 2 | curl | 同 session 第二個 request（新 message） | 回覆內容反映前一輪對話 context（checkpointer 正常運作） |
| 3 | curl | `curl -X POST ... -d '{"id":"","message":"test"}'` | Status 422 |
| 4 | curl | `curl -X POST ... -d '{"id":"s1","message":"hi","trigger":"regenerate"}'` | Status 422（conflict body） |
| 5 | Trace inspection | 檢查 Langfuse trace | 一個 request 產生一個 trace，tool observations 正確 attach |
| 6 | curl | 現有 endpoint：`curl -X POST http://localhost:8000/api/v1/chat -H "Content-Type: application/json" -d '{"message":"test"}'` | Status 200，正常回覆（不受影響） |

- [ ] All flow verifications pass

---

### Task 9: Documentation & Final Verification

**Files:**

- Update: `backend/agent_engine/docs/streaming_observability_guardrails.md`

**What & Why:** 更新 Rule 3 將 LangGraph tools 排除在 `@observe()` 適用範圍外，反映 D5 決策。確認所有測試通過、lint 通過。

**Implementation Notes:**

- 更新 Rule 3 的 Examples section：
  - 移除 `tools` 項目（透過 LangGraph 執行的 tools 不應使用 `@observe()`）
  - 新增說明：「透過 LangGraph/LangChain `CallbackHandler` 自動 trace 的 tools 不需 `@observe()`」
  - 新增「仍需使用 `@observe()` 的場景」：tool 內部有獨立子操作需追蹤時（如 tool 內部呼叫另一個 LLM）

**Verification:**

| Scope | Command | Expected Result | Why |
|---|---|---|---|
| Full test suite | `cd backend && python -m pytest tests/ -x -q --ignore=tests/streaming/test_poc_observability.py` | All PASSED | 完整 regression 檢查 |
| Lint | `cd backend && ruff check .` | No errors | Code style 一致 |
| Type check | `cd backend && pyright` | No errors（或只有 pre-existing） | 型別正確 |

**Execution Checklist:**

- [ ] 更新 `streaming_observability_guardrails.md` Rule 3
- [ ] 執行完整 test suite
- [ ] 執行 ruff lint
- [ ] 執行 pyright type check
- [ ] Commit: `git commit -m "docs(s1): update observability guardrails for streaming tools"`

---

## Pre-delivery Checklist

### Code Level (TDD)

- [ ] 所有 task 的 targeted tests 通過
- [ ] Full test suite 通過：`cd backend && python -m pytest tests/ -x -q --ignore=tests/streaming/test_poc_observability.py`
- [ ] Lint 通過：`cd backend && ruff check .`
- [ ] Type check 通過：`cd backend && pyright`

### Flow Level (Behavioral)

- [ ] Flow: Observability POC — PASS / FAIL
- [ ] Flow: Streaming Pipeline Unit Tests — PASS / FAIL
- [ ] Flow: End-to-end Streaming — PASS / FAIL

### Summary

- [ ] Both levels pass → ready for delivery
- [ ] Any failure is documented with cause and next action
