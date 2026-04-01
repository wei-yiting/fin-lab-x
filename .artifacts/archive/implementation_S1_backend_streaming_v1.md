# Implementation Plan: S1 Backend Streaming

> Design Reference: [`design_S1_backend_streaming.md`](./design_S1_backend_streaming.md)

**目標：** 為 FinLab-X backend 加入 streaming 支援 — `Orchestrator.astream_run()`、domain event pipeline、SSE endpoint（`POST /api/v1/chat/stream`）、`InMemorySaver` checkpointer、tool observability 清理、以及 observability POC 驗證。

**架構與關鍵決策：** LangGraph `astream(stream_mode=["messages", "updates", "custom"], version="v2")` 產出 raw chunks，經 `StreamEventMapper` 轉為 typed `DomainEvent`，再由 `singledispatch` SSE serializer 轉為 AI SDK UIMessage Stream Protocol v1 wire format。`InMemorySaver` checkpointer 以 `thread_id` 管理對話歷史。Observability POC（5 個 gates）必須全部通過後才開始正式 streaming 實作。

**技術棧：** Python 3.10+、LangGraph（via `langchain>=1.2.10`）、`langfuse>=4.0.0`、`FastAPI>=0.115.0`

---

## 依賴驗證

| 依賴 | 版本 | 來源 | 驗證內容 | 備註 |
| --- | --- | --- | --- | --- |
| LangGraph streaming | via `langchain>=1.2.10` | Context7 `/websites/langchain_oss_python_langgraph` | `astream()` 搭配 `stream_mode=["messages", "updates", "custom"]`, `version="v2"` 回傳 `StreamPart` dict `{"type": str, "data": Any, "ns": tuple}`。`messages` mode 的 data 是 `(AIMessageChunk, metadata)` tuple。`get_stream_writer()` 從 `langgraph.config` 匯入。 | v2 unified format 已確認 |
| LangGraph checkpointer | via `langchain>=1.2.10` | Context7 `/websites/langchain_oss_python_langgraph` | `InMemorySaver` 從 `langgraph.checkpoint.memory` 匯入。`create_agent()` 接受 `checkpointer` 參數。`thread_id` 透過 `config={"configurable": {"thread_id": ...}}` 傳入。 | `MemorySaver` 是別名；明確使用 `InMemorySaver` |
| Langfuse + LangGraph streaming | `>=4.0.0` | Context7 `/langfuse/langfuse-docs` | `CallbackHandler` 從 `langfuse.langchain` 匯入，透過 `config={"callbacks": [handler]}` 傳給 `astream()`。`propagate_attributes(session_id=...)` 從 `langfuse` 匯入設定 correlation。Handler 自動透過 `on_tool_start`/`on_tool_end` trace tool calls。 | 確認與 LangGraph `stream()` 相容 |
| FastAPI StreamingResponse | `>=0.115.0` | Context7 `/websites/fastapi_tiangolo` | `StreamingResponse(content=async_generator, media_type="text/event-stream", headers={...})`。接受 async generator，串流 chunks。 | 標準 SSE pattern |

---

## 約束條件

- Observability POC（5 gates）必須全部通過才能開始 Tasks 2–7
- 不可修改現有 `POST /api/v1/chat` endpoint 或 `api/routers/chat.py`
- 僅使用 `InMemorySaver` — 不做 persistent store（V2 scope）
- 不支援 tool input streaming（`tool-call-delta`）
- 不支援任意歷史 message regenerate（V1 僅支援最後一條）
- `.artifacts/` 不可 commit 至 git

---

## 檔案計畫

| 操作 | 路徑 | 用途 |
| --- | --- | --- |
| Create | `backend/agent_engine/streaming/__init__.py` | Package init，re-export 主要介面 |
| Create | `backend/agent_engine/streaming/domain_events.py` | 11 個 frozen dataclass + `DomainEvent` Union type |
| Create | `backend/agent_engine/streaming/sse_serializer.py` | `singledispatch` serializer：`DomainEvent` → SSE `data:` line |
| Create | `backend/agent_engine/streaming/event_mapper.py` | `StreamEventMapper`：LangGraph v2 chunks → `DomainEvent` 序列 |
| Create | `backend/agent_engine/streaming/progress_writer.py` | `get_progress_writer()` helper，供 tools 使用 |
| Create | `backend/api/routers/chat_stream.py` | `POST /api/v1/chat/stream` SSE endpoint |
| Update | `backend/agent_engine/agents/base.py` | 加入 `InMemorySaver` checkpointer + `astream_run()` method |
| Update | `backend/agent_engine/tools/financial.py` | 移除 `@observe()`，加入 progress writer 呼叫 |
| Update | `backend/agent_engine/tools/sec.py` | 移除 `@observe()`，加入 progress writer 呼叫 |
| Update | `backend/api/main.py` | 註冊 `chat_stream` router |
| Update | `backend/agent_engine/docs/streaming_observability_guardrails.md` | 更新 Rule 3 用語 |
| Update | `backend/agent_engine/CLAUDE.md` | 同步 Rule 3 |
| Create | `backend/tests/streaming/__init__.py` | 測試 package |
| Create | `backend/tests/streaming/test_domain_events.py` | Domain event 建構 + frozen 測試 |
| Create | `backend/tests/streaming/test_sse_serializer.py` | 每種 event type 的序列化輸出測試 |
| Create | `backend/tests/streaming/test_event_mapper.py` | Mapper：chunk 序列 → event 序列測試 |
| Create | `backend/tests/api/test_chat_stream.py` | SSE endpoint 整合測試 |
| Create | `backend/tests/poc/__init__.py` | POC package |
| Create | `backend/tests/poc/test_observability_poc.py` | 5 gate 驗證腳本（不納入 CI） |
| Create | `backend/tests/agents/test_streaming.py` | `astream_run()` unit tests |
| Update | `backend/tests/api/conftest.py` | 為 mock agent 加入 astream / aget_state mock |
| Update | `backend/tests/tools/test_observe_decorators.py` | 移除 `@observe` 斷言；保留 tool schema 檢查 |

```text
backend/
├── agent_engine/
│   ├── agents/
│   │   └── base.py                  ← +checkpointer, +astream_run()
│   ├── tools/
│   │   ├── financial.py             ← -@observe, +progress writer
│   │   └── sec.py                   ← -@observe, +progress writer
│   ├── streaming/                   ← NEW
│   │   ├── __init__.py
│   │   ├── domain_events.py
│   │   ├── event_mapper.py
│   │   ├── sse_serializer.py
│   │   └── progress_writer.py
│   ├── docs/
│   │   └── streaming_observability_guardrails.md  ← update Rule 3
│   └── CLAUDE.md                    ← sync Rule 3
├── api/
│   ├── main.py                      ← +chat_stream router
│   └── routers/
│       ├── chat.py                  ← 不動
│       └── chat_stream.py           ← NEW
└── tests/
    ├── streaming/                   ← NEW
    │   ├── __init__.py
    │   ├── test_domain_events.py
    │   ├── test_sse_serializer.py
    │   └── test_event_mapper.py
    ├── api/
    │   └── test_chat_stream.py      ← NEW
    ├── agents/
    │   └── test_streaming.py        ← NEW
    ├── tools/
    │   └── test_observe_decorators.py  ← update
    └── poc/                         ← NEW（不納入 CI）
        ├── __init__.py
        └── test_observability_poc.py
```

---

### Task 1：Observability POC — Checkpointer + 5 Gate 驗證

**檔案：**

- Update: `backend/agent_engine/agents/base.py`
- Create: `backend/tests/poc/__init__.py`
- Create: `backend/tests/poc/test_observability_poc.py`

**做什麼、為什麼：** 在建構完整 streaming pipeline 之前，先驗證 `CallbackHandler` + `astream()` 能正確產生 Langfuse traces。POC 同時驗證 `handle_tool_errors` 在 `create_agent()` 上是否可用，並選擇性測試 `ToolRuntime` 能否提供精確的 `tool_call_id`。任何 gate 失敗都可能需要修改方向 — 提早發現可避免大量返工。

**實作備註：**

- 在 `Orchestrator.__init__()` 的 `create_agent()` 呼叫中加入 `checkpointer=InMemorySaver()`：

```python
from langgraph.checkpoint.memory import InMemorySaver

self.agent = create_agent(
    model=model,
    tools=self.tools,
    system_prompt=self.system_prompt,
    middleware=[tool_call_limit],
    checkpointer=InMemorySaver(),
)
```

- 嘗試在 `create_agent()` 加入 `handle_tool_errors=True`。如果 `create_agent()` 不支援此參數，記錄發現並回退到 tool 內部 try/except（現有 pattern 已處理 — 所有 tools 皆 catch exceptions 並回傳 error dict）。

- POC 腳本結構：5 個 async 函式（每個 gate 一個），每個函式直接呼叫 `orchestrator.agent.astream()` 搭配 `CallbackHandler` 並檢查結果。Gates：
  1. **Single trace**：一個 streaming request → Langfuse 恰好一個 trace，`session_id` 正確
  2. **Tool observations**：觸發 tool call → tool observation 存在於 trace 的 child（name、args、result、duration 皆有紀錄）
  3. **Cancellation**：串流中途取消 async generator → trace 已關閉（不會永遠 pending）
  4. **Exception visibility**：使用刻意拋錯的 mock tool → exception 出現在 trace 中 + stream 輸出有 error event
  5. **Concurrent isolation**：同時送 3 個 request 帶不同 `session_id` → 3 個 trace，不交叉

- Gate 2 定義一個不帶 `@observe()` 的簡單 test tool，確認 `CallbackHandler` 自動 trace。
- Gate 4 定義一個永遠拋 `ValueError` 的 mock tool。
- POC 輸出：console 結果 + 檢查 Langfuse dashboard 的指引。
- 選擇性 POC 子項：測試 `ToolRuntime`（from `langgraph.prebuilt.chat_agent_executor`）能否在 `get_stream_writer()` context 中提供精確 `tool_call_id`。如果 `ToolRuntime` 可用（`langchain-ai/langgraph#6431` 的 Pydantic bug 已修復），記錄供未來使用。如果不行，確認 V1 使用 `toolName` 反查。

**測試策略：** 此 task 產出手動驗證腳本（`tests/poc/test_observability_poc.py`），不是自動化 CI 測試。腳本需搭配真實 API keys 對真實 Langfuse instance 執行。每個 gate 印出 PASS/FAIL。

**驗證：**

| 範圍 | 指令 | 預期結果 | 原因 |
| --- | --- | --- | --- |
| POC gates | `cd backend && python -m pytest tests/poc/test_observability_poc.py -v -s` | 5 個 gates 全部印出 PASS，console 顯示每個 gate 的 trace ID | 確認 Langfuse + astream 整合可用，再開始建構 pipeline |
| 既有測試 | `cd backend && python -m pytest tests/agents/test_base.py -v` | 所有既有 Orchestrator 測試通過 | 加入 checkpointer 不破壞既有行為 |
| Trace 檢視 | 在 Langfuse dashboard 檢查 POC 建立的 traces | 5+ traces 可見，tool observations 正確巢狀，cancelled trace 已關閉 | 視覺確認 observability 品質 |

**執行清單：**

- [ ] 🔴 **Red** — 建立 `tests/poc/__init__.py` 和 `tests/poc/test_observability_poc.py`，含 5 個 gate 函式 → 執行 → 預期 FAIL（checkpointer 尚未加入，`astream` 缺少 `thread_id` config）
- [ ] 🟢 **Green** — 在 `agents/base.py` 的 `Orchestrator.__init__()` 加入 `InMemorySaver` import 和 `checkpointer=InMemorySaver()`；驗證 `handle_tool_errors` 參數是否可用（可用就加，不可用就記錄）→ 執行既有 Orchestrator 測試確認無 regression → 用真實 API keys 執行 POC 腳本 → 5 個 gates 全部 PASS
- [ ] 🔵 **Refactor** — 審視 `agents/base.py` 變更：checkpointer 初始化是否乾淨、`_build_langfuse_config` 是否需要調整以適應未來 `astream_run` 使用。審視 POC 腳本：消除重複的 setup code、提取共用 helper → 執行既有 Orchestrator 測試 + POC 腳本 → 仍全部 PASS
- [ ] 將發現（handle_tool_errors、ToolRuntime）記錄為 POC 腳本中的 comments
- [ ] Commit：`feat(S1): add InMemorySaver checkpointer and observability POC gates`

**Gate 失敗處理：** 任一 gate 失敗 → 停下分析 root cause 再繼續。常見原因：
- `CallbackHandler` 版本問題 → 確認 `langfuse>=4.0.0`
- `contextvars` 傳播問題 → 調整 async 邊界處理
- `@observe()` 殘留影響 → 確認 test tool 上沒有 residual decorator

---

### Task 2：Domain Events + SSE Serializer

**檔案：**

- Create: `backend/agent_engine/streaming/__init__.py`
- Create: `backend/agent_engine/streaming/domain_events.py`
- Create: `backend/agent_engine/streaming/sse_serializer.py`
- Create: `backend/tests/streaming/__init__.py`
- Create: `backend/tests/streaming/test_domain_events.py`
- Create: `backend/tests/streaming/test_sse_serializer.py`

**做什麼、為什麼：** Domain events 是 `StreamEventMapper` 和 `SSE Serializer` 之間的介面。必須先定義，因為所有其他元件都依賴它。SSE serializer 是同一個 contract 的另一端 — 一起定義確保 serializer contract 能針對它實際會處理的 event types 進行測試。

**Critical Contract：**

```python
# domain_events.py
from dataclasses import dataclass

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
    result: str  # JSON string

@dataclass(frozen=True)
class ToolError:
    tool_call_id: str
    error: str

@dataclass(frozen=True)
class ToolProgress:
    tool_call_id: str
    data: dict  # {status, message, toolName}

@dataclass(frozen=True)
class StreamError:
    error_text: str

@dataclass(frozen=True)
class Finish:
    finish_reason: str  # "stop" | "error"
    input_tokens: int | None = None
    output_tokens: int | None = None

DomainEvent = (
    MessageStart | TextStart | TextDelta | TextEnd
    | ToolCallStart | ToolCallEnd | ToolResult | ToolError
    | ToolProgress | StreamError | Finish
)
```

```python
# sse_serializer.py — singledispatch pattern
import json
import functools
from backend.agent_engine.streaming.domain_events import *

@functools.singledispatch
def serialize(event: DomainEvent) -> str:
    """DomainEvent → SSE data line: 'data: {json}\n\n'"""
    raise TypeError(f"Unhandled event type: {type(event).__name__}")

@serialize.register
def _(event: MessageStart) -> str:
    return _sse_line({"type": "start", "messageId": event.message_id})

@serialize.register
def _(event: TextDelta) -> str:
    return _sse_line({"type": "text-delta", "id": event.text_id, "delta": event.delta})

# ... 對所有 11 個 event types 做 register

def _sse_line(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
```

欄位映射（internal → wire）：
- `message_id` → `"messageId"`
- `text_id` → `"id"`
- `tool_call_id` → `"toolCallId"`
- `tool_name` → `"toolName"`
- `ToolProgress` 在 wire format 中加上 `"transient": true`
- `ToolError` 的 wire type 是 `"data-tool-error"`（非 `"tool-error"`）
- `ToolProgress` 的 wire type 是 `"data-tool-progress"`

**測試策略：**

`test_domain_events.py`：
- 11 個 event types 皆可用正確欄位實例化
- 所有 events 為 frozen（不可變）— 修改欄位時 raise `FrozenInstanceError`
- `ToolProgress.data` 接受任意 dict

`test_sse_serializer.py`：
- 11 個 event types 各自序列化為正確的 JSON 結構（assert `type` 欄位、欄位名稱映射、`ensure_ascii=False` 支援 CJK）
- `ToolProgress` 輸出包含 `"transient": true`
- `ToolError` 輸出的 `type` 為 `"data-tool-error"`
- `Finish` 帶 token counts 時包含 `usage` object；不帶時省略
- 未註冊的 type raise `TypeError`
- 所有輸出行符合 `data: {...}\n\n` 格式

**驗證：**

| 範圍 | 指令 | 預期結果 | 原因 |
| --- | --- | --- | --- |
| Domain events | `cd backend && python -m pytest tests/streaming/test_domain_events.py -v` | 全部通過 | Event types 正確且 frozen |
| SSE serializer | `cd backend && python -m pytest tests/streaming/test_sse_serializer.py -v` | 全部通過 | Wire format 符合 AI SDK UIMessage Stream Protocol v1 |

**執行清單：**

- [ ] 建立 `backend/agent_engine/streaming/__init__.py`（空 package init，後續補 re-export）
- [ ] 建立 `backend/tests/streaming/__init__.py`
- [ ] 🔴 **Red** — 撰寫 `test_domain_events.py` → 執行 → 預期 FAIL（`domain_events` module 不存在）
- [ ] 🟢 **Green** — 建立 `domain_events.py`，含 11 個 dataclass + Union type → 執行 `test_domain_events.py` → PASS
- [ ] 🔵 **Refactor** — 審視 `domain_events.py`：命名一致性、import 結構、Union type 定義是否乾淨 → 執行 `test_domain_events.py` → 仍 PASS
- [ ] 🔴 **Red** — 撰寫 `test_sse_serializer.py` → 執行 → 預期 FAIL（`sse_serializer` module 不存在）
- [ ] 🟢 **Green** — 建立 `sse_serializer.py`，含所有 11 個 `singledispatch` registration → 執行 `test_sse_serializer.py` → PASS
- [ ] 🔵 **Refactor** — 審視 `sse_serializer.py`：`_sse_line` helper 是否有重複邏輯可抽取、各 register 函式結構是否一致 → 執行全部 streaming 測試 → 仍 PASS
- [ ] 更新 `__init__.py` re-export `DomainEvent`、`serialize`
- [ ] Commit：`feat(S1): add domain events and SSE serializer`

---

### Task 3：StreamEventMapper

**檔案：**

- Create: `backend/agent_engine/streaming/event_mapper.py`
- Create: `backend/tests/streaming/test_event_mapper.py`

**做什麼、為什麼：** Mapper 是核心翻譯層 — 將 LangGraph v2 `StreamPart` chunks 轉為 typed `DomainEvent` 序列。它追蹤 text block 狀態、pending tool calls、和 `MessageStart` 是否已發送。這是 S1 中最複雜的單一元件，需要充分的測試覆蓋。

**實作備註：**

- `StreamEventMapper` 是 per-stream 實例化的有狀態 class：

```python
class StreamEventMapper:
    def __init__(self, message_id: str):
        self._message_id = message_id
        self._started = False
        self._text_block_open = False
        self._current_text_id: str | None = None
        self._pending_tool_calls: dict[str, str] = {}  # tool_call_id → tool_name
        self._text_id_counter = 0

    def process(self, chunk: dict) -> list[DomainEvent]: ...
    def close_text_block(self) -> list[DomainEvent]: ...
    def finish(self, finish_reason: str = "stop",
               input_tokens: int | None = None,
               output_tokens: int | None = None) -> list[DomainEvent]: ...
```

- `process()` 根據 `chunk["type"]` 分派：
  - `"messages"` → 處理 `AIMessageChunk` 的 text content 和 tool_call_chunks
  - `"updates"` → 處理 agent node 完成（`ToolCallEnd`）和 tools node 完成（`ToolResult` / `ToolError`）
  - `"custom"` → 處理 `ToolProgress`（用 `toolName` 反查 `tool_call_id`）

- LangGraph v2 chunk 格式（已透過 Context7 確認）：
  ```python
  {"type": "messages", "data": (AIMessageChunk(...), metadata), "ns": ()}
  {"type": "updates", "data": {"agent": {"messages": [...]}}, "ns": ()}
  {"type": "updates", "data": {"tools": {"messages": [...]}}, "ns": ()}
  {"type": "custom",  "data": {"toolName": "...", "status": "...", "message": "..."}, "ns": ()}
  ```

- 處理規則（來自 design）：
  - 第一個 chunk → emit `MessageStart`（只發一次）
  - Text content → 自動在 text blocks 前後補上 `TextStart`/`TextEnd`
  - Tool call chunks → 關閉開啟中的 text block，對新 tool calls emit `ToolCallStart`
  - Agent node update → 對所有 pending tool calls emit `ToolCallEnd`
  - Tools node update → 每個 `ToolMessage` emit `ToolResult` 或 `ToolError`（檢查 `.status == "error"`）
  - Custom chunk → 用 `toolName` 在 `_pending_tool_calls` 中查找 `tool_call_id`，emit `ToolProgress`（找不到時靜默跳過）
  - `finish()` → 內部呼叫 `close_text_block()`，emit `Finish`

- `text_id` 生成：`f"txt_{self._text_id_counter:03d}"` 自動遞增
- 公開 `close_text_block() -> list[DomainEvent]` — 如果 text block 開啟中回傳 `[TextEnd]`，否則回傳 `[]`。同時被 `finish()` 內部使用和 `astream_run()` error handling 使用，避免存取 private state。

**測試策略：**

`test_event_mapper.py` — 每個測試餵入一組 mock chunks 並 assert 產出的 `DomainEvent` list：

1. **純文字串流**：`[messages(content="Hello")]` → `[MessageStart, TextStart, TextDelta, TextEnd (via finish), Finish]`
2. **多 chunk 文字**：`[messages("A"), messages("B")]` → 單一 TextStart、兩個 TextDelta、finish 時 TextEnd
3. **Tool call 流程**：`[messages(tool_call_chunks), updates(agent), updates(tools)]` → `[MessageStart, ToolCallStart, ToolCallEnd, ToolResult]`
4. **文字 → tool → 文字**：完整循環（design 的「完整範例」）— 驗證 text blocks 在 tool calls 前後正確開關
5. **Tool error**：`ToolMessage(status="error")` → `ToolError` 而非 `ToolResult`
6. **Tool progress**：Custom chunk 帶匹配的 `toolName` → `ToolProgress` 帶正確 `tool_call_id`
7. **Tool progress 未知 tool**：Custom chunk 帶未知 `toolName` → 不 emit 任何 event（靜默跳過）
8. **多個 tool calls**：一個 agent turn 中兩個 tool calls → 兩個 `ToolCallStart`、兩個 `ToolCallEnd`
9. **Error finish**：`finish("error")` → `Finish(finish_reason="error")`
10. **MessageStart 只發一次**：多個 chunks → 只有一個 `MessageStart`

Mock chunk helper：

```python
def _msg_chunk(content="", tool_call_chunks=None):
    """建構帶 mock AIMessageChunk 的 v2 'messages' StreamPart。"""
    chunk = MagicMock()
    chunk.content = content
    chunk.tool_call_chunks = tool_call_chunks or []
    return {"type": "messages", "data": (chunk, {}), "ns": ()}
```

**驗證：**

| 範圍 | 指令 | 預期結果 | 原因 |
| --- | --- | --- | --- |
| Mapper 測試 | `cd backend && python -m pytest tests/streaming/test_event_mapper.py -v` | 10 個 cases 全部通過 | Mapper 正確翻譯所有 chunk patterns |
| 完整 streaming package | `cd backend && python -m pytest tests/streaming/ -v` | 所有 streaming 測試通過 | Domain events 和 serializer 無 regression |

**執行清單：**

- [ ] 🔴 **Red** — 撰寫 `test_event_mapper.py`，含 mock chunk helpers 和 10 個 test cases → 執行 → 預期 FAIL（`event_mapper` module 不存在）
- [ ] 🟢 **Green** — 建立 `event_mapper.py`，實作 `StreamEventMapper` 含 `process()`、`close_text_block()` 和 `finish()` → 執行 mapper 測試 → PASS
- [ ] 🔵 **Refactor** — 審視 `event_mapper.py`：`process()` 內部分派邏輯是否可拆成 private methods（`_handle_messages`、`_handle_updates`、`_handle_custom`）以提升可讀性、state tracking 邏輯是否有重複 → 執行完整 streaming 測試套件 → 仍全部 PASS
- [ ] Commit：`feat(S1): add StreamEventMapper for LangGraph chunk translation`

---

### Flow Verification：Domain Event Pipeline

> Tasks 2–3 完成了 domain event 翻譯 pipeline。在繼續前驗證完整鏈路
>（mock chunks → mapper → serializer → SSE lines）。

| # | 方法 | 步驟 | 預期結果 |
| --- | --- | --- | --- |
| 1 | Runtime / function invocation | 在測試或 REPL 中：建立 `StreamEventMapper("msg_001")`，餵入 design 中「完整範例」的 chunk 序列，收集 events，每個通過 `serialize()` | SSE 輸出符合 design 的「完整 SSE Stream 範例」section（相同 `type`、`messageId`、`id`、`toolCallId`、`delta` 值） |
| 2 | 測試套件 | `cd backend && python -m pytest tests/streaming/ -v` | 所有 domain event、serializer、mapper 測試通過 |

- [ ] 所有 flow verifications 通過

---

### Task 4：Progress Writer + Tool 變更

**檔案：**

- Create: `backend/agent_engine/streaming/progress_writer.py`
- Update: `backend/agent_engine/tools/financial.py`
- Update: `backend/agent_engine/tools/sec.py`
- Update: `backend/tests/tools/test_observe_decorators.py`

**做什麼、為什麼：** 兩個耦合的變更：(1) 建立 `get_progress_writer()` helper 讓 tools 發送 progress events，(2) 修改所有 4 個 tools 移除 `@observe()` 並加入 progress 呼叫。合在一起是因為 progress writer 只在整合到 tools 時才有意義，且 `@observe()` 移除是正確 observability 的前提（design decision D5）。

**實作備註：**

Progress writer helper：

```python
# streaming/progress_writer.py
from langgraph.config import get_stream_writer

def get_progress_writer():
    """回傳 tool progress 用的 stream writer，若不可用則回傳 no-op。"""
    try:
        return get_stream_writer()
    except RuntimeError:
        return lambda data: None  # streaming context 外回傳 no-op
```

Tool 變更 pattern（4 個 tools 相同）：
1. 移除 `from langfuse import observe` import
2. 移除 `@observe(name="...")` decorator 行
3. 加入 `from backend.agent_engine.streaming.progress_writer import get_progress_writer`
4. 在 tool function 開頭呼叫 `writer = get_progress_writer()` 後 `writer({...})` 發送 progress data

各 tool 的 progress 訊息（來自 design）：
- `yfinance_stock_quote` → `{"toolName": "yfinance_stock_quote", "status": "querying_stock", "message": "查詢 {ticker} 股價..."}`
- `yfinance_get_available_fields` → `{"toolName": "yfinance_get_available_fields", "status": "querying_fields", "message": "取得 {ticker} 可用欄位..."}`
- `tavily_financial_search` → `{"toolName": "tavily_financial_search", "status": "searching_news", "message": "搜尋 {ticker} 相關新聞..."}`
- `sec_official_docs_retriever` → 兩次呼叫：`{"toolName": "sec_official_docs_retriever", "status": "fetching_filing", "message": "搜尋 {ticker} {doc_type}..."}` 然後 `{"toolName": "sec_official_docs_retriever", "status": "parsing_filing", "message": "解析報告內容..."}`

測試檔案更新（`test_observe_decorators.py`）：
- 移除 `test_tools_use_observe_decorator`（不再適用）
- 保留 `test_observe_decorator_does_not_break_tool_schema` — 更名為 `test_tool_schema_intact`（仍有效，測試 tool name、description、args_schema）

**測試策略：**

- `test_tool_schema_intact`（更新既有測試）：移除 `@observe()` 後 4 個 tools 仍有正確的 `name`、`description`、`args_schema`
- Progress writer 測試（可加在 `test_event_mapper.py` 或另建小檔案）：
  - `get_progress_writer()` 在 streaming context 外呼叫時回傳可呼叫的 no-op（不拋 exception）
  - 回傳的 callable 可安全地帶任意 dict 呼叫

**驗證：**

| 範圍 | 指令 | 預期結果 | 原因 |
| --- | --- | --- | --- |
| Tool schema | `cd backend && python -m pytest tests/tools/test_observe_decorators.py -v` | Schema 測試通過；舊 observe 測試已移除 | 移除 @observe 後 tools 仍有正確的 LangChain metadata |
| 所有 tool 測試 | `cd backend && python -m pytest tests/tools/ -v` | 全部通過 | Tool 測試無 regression |
| Import 檢查 | `cd backend && python -c "from backend.agent_engine.tools.financial import yfinance_stock_quote; print(yfinance_stock_quote.name)"` | 印出 `yfinance_stock_quote` | Tool 在無 @observe 的情況下可正常 import |

**執行清單：**

- [ ] 🔴 **Red** — 更新 `test_observe_decorators.py`：移除 `test_tools_use_observe_decorator`，保留並更名為 `test_tool_schema_intact`；新增 progress writer 測試（no-op fallback + callable） → 執行 → 預期 FAIL（`progress_writer` module 不存在）
- [ ] 🟢 **Green** — 建立 `streaming/progress_writer.py` 含 `get_progress_writer()`；更新 `__init__.py` export → 執行 progress writer 測試 → PASS
- [ ] 🟢 **Green** — 移除 `financial.py` 和 `sec.py` 中所有 4 個 tools 的 `@observe()` + `from langfuse import observe` imports；加入 progress writer 呼叫 → 執行所有 tool 測試 → PASS（schema 測試確認 tools 完整）
- [ ] 🔵 **Refactor** — 審視 tool 變更：progress writer 呼叫位置是否一致（皆在 function 開頭）、import 路徑是否統一、移除 `@observe` 後有無殘留 dead imports → 執行所有 tool 測試 → 仍全部 PASS
- [ ] Commit：`refactor(S1): remove @observe from tools, add progress writer`

---

### Task 5：Orchestrator.astream_run()

**檔案：**

- Update: `backend/agent_engine/agents/base.py`
- Create: `backend/tests/agents/test_streaming.py`

**做什麼、為什麼：** 核心 streaming method，串接 checkpointer、`StreamEventMapper`、Langfuse tracing、和 error handling。這是 agent runtime 和 SSE endpoint 之間的橋樑。

**實作備註：**

Method signature 和流程：

```python
async def astream_run(
    self, message: str | None, session_id: str
) -> AsyncGenerator[DomainEvent, None]:
    config, propagation = self._build_langfuse_config(session_id=session_id)
    message_id = f"msg_{uuid.uuid4().hex[:12]}"
    mapper = StreamEventMapper(message_id)

    # message=None 代表 regenerate（從 checkpoint 的既有 messages 繼續）
    astream_input = (
        {"messages": [HumanMessage(content=message)]} if message else None
    )

    with propagate_attributes(**propagation):
        try:
            async for chunk in self.agent.astream(
                astream_input,
                stream_mode=["messages", "updates", "custom"],
                config={
                    **config,
                    "configurable": {"thread_id": session_id},
                },
                version="v2",
            ):
                for event in mapper.process(chunk):
                    yield event

            for event in mapper.finish("stop"):
                yield event

        except Exception as exc:
            for event in mapper.close_text_block():
                yield event
            yield StreamError(error_text=str(exc))
            yield Finish(finish_reason="error")
```

- `message=None` 觸發 regenerate 模式 — `astream()` 收到 `None` input，從 checkpoint 的既有 messages 繼續（endpoint 在呼叫前負責從 checkpoint state 移除最後一個 assistant turn）
- `message_id` 是 per-stream 生成的（非 per-session）
- `thread_id = session_id` — checkpointer 用此管理對話 persistence
- Error handling 使用 `mapper.close_text_block()`（public method）乾淨地關閉開啟中的 text block，然後 emit `StreamError` + `Finish("error")`

**測試策略：**

`test_streaming.py`：
1. **Happy path**：Mock `agent.astream` yield 一組 v2 chunks（純文字）→ `astream_run()` yields `[MessageStart, TextStart, TextDelta, ..., TextEnd, Finish("stop")]`
2. **帶 tool call**：Mock astream yields messages + updates chunks → 正確的 tool lifecycle events
3. **串流中錯誤**：Mock astream 中途 raise → yields `StreamError` + `Finish("error")`
4. **文字開啟中遇錯**：文字開始後 raise → yields `TextEnd`（via `close_text_block()`） 在 `StreamError` 之前
5. **Session ID 傳播**：驗證 `astream` 被呼叫時 `configurable.thread_id` 符合 `session_id`
6. **Langfuse handler**：驗證 `CallbackHandler` 包含在 config callbacks 中
7. **Regenerate 模式**：呼叫 `astream_run(None, session_id)` → `astream` 收到 `None` input

Mock pattern：

```python
async def mock_astream(*args, **kwargs):
    yield {"type": "messages", "data": (mock_chunk, {}), "ns": ()}
    yield {"type": "updates", "data": {"agent": {"messages": [...]}}, "ns": ()}

mock_agent.astream = mock_astream
```

**驗證：**

| 範圍 | 指令 | 預期結果 | 原因 |
| --- | --- | --- | --- |
| Streaming 測試 | `cd backend && python -m pytest tests/agents/test_streaming.py -v` | 7 個 cases 全部通過 | astream_run 產出正確的 event 序列 |
| 既有 agent 測試 | `cd backend && python -m pytest tests/agents/ -v` | 全部通過 | 既有 run/arun 無 regression |

**執行清單：**

- [ ] 🔴 **Red** — 撰寫 `test_streaming.py`，含 mock astream helper 和 7 個 test cases → 執行 → 預期 FAIL（`astream_run()` method 不存在）
- [ ] 🟢 **Green** — 在 `agents/base.py` 加入必要 imports（`uuid`、`HumanMessage`、streaming module imports）並實作 `astream_run()` method → 執行 `test_streaming.py` → PASS
- [ ] 🔵 **Refactor** — 審視 `astream_run()`：error handling 路徑是否與 happy path 共用 mapper 正確、`_build_langfuse_config` 的 config merge 是否乾淨（不 clobber existing keys）、method 長度是否合理（考慮拆出 `_prepare_astream_config` helper） → 執行完整 agent 測試套件（含既有 `test_base.py`）→ 仍全部 PASS
- [ ] Commit：`feat(S1): add Orchestrator.astream_run() with StreamEventMapper integration`

---

### Task 6：FastAPI SSE Endpoint

**檔案：**

- Create: `backend/api/routers/chat_stream.py`
- Update: `backend/api/main.py`
- Create: `backend/tests/api/test_chat_stream.py`
- Update: `backend/tests/api/conftest.py`

**做什麼、為什麼：** Streaming 的 HTTP 表面 — `POST /api/v1/chat/stream` 搭配 SSE response。處理新訊息和 regenerate 兩種流程、per-session 並行鎖、以及 AI SDK UIMessage Stream Protocol v1 所需的 response headers。

**實作備註：**

Request models：

```python
class StreamChatRequest(BaseModel):
    message: str | None = None
    id: str | None = None  # session ID
    trigger: str | None = None  # "regenerate" or None
    messageId: str | None = None  # for regenerate

    @model_validator(mode="after")
    def validate_request(self):
        if self.trigger == "regenerate":
            if not self.id:
                raise ValueError("id is required for regenerate")
            if not self.messageId:
                raise ValueError("messageId is required for regenerate")
        else:
            if not self.message or not self.message.strip():
                raise ValueError("message is required and must not be empty")
        return self
```

Endpoint 流程：

```
POST /api/v1/chat/stream
  1. Parse request → 新訊息或 regenerate
  2. 取得 per-session asyncio.Lock（或設定為回傳 409）
  3. 未提供 id 時自動產生 session_id
  4. 新訊息：
     → 呼叫 orchestrator.astream_run(message, session_id)
  5. Regenerate：
     → 透過 agent.aget_state(config) 從 checkpointer 載入 state
     → 從 messages 中移除最後一個 assistant turn（最後的 AIMessage + 關聯的 ToolMessages）
     → 透過 agent.aupdate_state(config, modified_values) 更新 state
     → 呼叫 orchestrator.astream_run(None, session_id)
       （message=None 讓 astream 從更新後的 checkpoint 繼續，不會重複注入 user message）
  6. 包裝成 async generator，對每個 DomainEvent 呼叫 serialize()
  7. 回傳 StreamingResponse 帶必要 headers
```

必要 response headers：

```python
headers = {
    "Content-Type": "text/event-stream",
    "Cache-Control": "no-cache",
    "X-Accel-Buffering": "no",
    "x-vercel-ai-ui-message-stream": "v1",
}
```

Per-session lock：

```python
_session_locks: dict[str, asyncio.Lock] = {}

async def acquire_session_lock(session_id: str) -> asyncio.Lock:
    if session_id not in _session_locks:
        _session_locks[session_id] = asyncio.Lock()
    return _session_locks[session_id]
```

Regenerate 找不到 session（`InMemorySaver` 在 server 重啟後遺失 state）→ 回傳 HTTP 404。

Router 註冊（`main.py`）：

```python
from backend.api.routers import chat, chat_stream
app.include_router(chat_stream.router)
```

更新 `conftest.py`：為 mock agent 加入 `astream` async generator mock、`aget_state` / `aupdate_state` mock（regenerate 測試用）。

**測試備註：** 使用 `TestClient`（synchronous）測試。`TestClient` 會 buffer 完整 `StreamingResponse` 後回傳，這對驗證 SSE content 和 headers 是足夠的。不需要切換到 `httpx.AsyncClient` — V1 的測試重點是 wire format 正確性，不是 streaming lifecycle。

**測試策略：**

`test_chat_stream.py`：
1. **新訊息 — SSE 格式**：POST `{"message": "test", "id": "sess-1"}` → response 為 `text/event-stream`，包含 `data: {"type":"start",...}` 行，以 `data: {"type":"finish",...}` 結尾
2. **新訊息 — 自動 session ID**：POST 不帶 `id` → response 中 `start` event 的 `messageId` 為有效 UUID
3. **必要 headers**：Response 包含全部 4 個必要 headers
4. **空訊息 — 422**：POST `{"message": ""}` → 422
5. **缺少 message — 422**：POST `{}` → 422
6. **Regenerate — 有效**：POST `{"id": "sess-1", "trigger": "regenerate", "messageId": "msg_001"}` → SSE stream
7. **Regenerate — session 不存在（404）**：對未知 session 做 regenerate → 404
8. **Orchestrator 錯誤 — stream 中的 error event**：Mock astream raise → stream 包含 `error` event + `finish` event
9. **Content type**：驗證 `Content-Type: text/event-stream` header

**驗證：**

| 範圍 | 指令 | 預期結果 | 原因 |
| --- | --- | --- | --- |
| Endpoint 測試 | `cd backend && python -m pytest tests/api/test_chat_stream.py -v` | 9 個 cases 全部通過 | SSE endpoint 正確處理所有 request 變體 |
| 所有 API 測試 | `cd backend && python -m pytest tests/api/ -v` | 全部通過（含既有 chat 測試） | 既有 endpoint 無 regression |

**執行清單：**

- [ ] 🔴 **Red** — 更新 `conftest.py` 為 mock agent 加入 `astream` async generator mock、`aget_state` / `aupdate_state` mock；撰寫 `test_chat_stream.py` 含 9 個 test cases → 執行 → 預期 FAIL（`chat_stream` module 不存在、router 未註冊）
- [ ] 🟢 **Green** — 建立 `api/routers/chat_stream.py`，含 endpoint、request model、session lock、SSE generator；更新 `api/main.py` 註冊 `chat_stream.router` → 執行 `test_chat_stream.py` → PASS
- [ ] 🔵 **Refactor** — 審視 `chat_stream.py`：request validation 是否清晰、regenerate 流程是否可拆為 helper function、`_session_locks` 生命週期是否合理、SSE generator 和 `serialize()` 的銜接是否乾淨 → 執行所有 API 測試（含既有 `test_chat.py`）→ 仍全部 PASS
- [ ] Commit：`feat(S1): add POST /api/v1/chat/stream SSE endpoint`

---

### Flow Verification：End-to-End Streaming

> Tasks 1–6 完成了完整的 S1 backend streaming pipeline。以下所有驗證
> 必須通過後才能繼續 docs 清理。

| # | 方法 | 步驟 | 預期結果 |
| --- | --- | --- | --- |
| 1 | curl | 啟動 server：`cd backend && uvicorn backend.api.main:app --port 8000`。然後：`curl -N -X POST http://localhost:8000/api/v1/chat/stream -H "Content-Type: application/json" -d '{"message": "Hello"}'` | SSE stream 輸出包含 `data: {"type":"start",...}` … `data: {"type":"finish",...}`。Stream 乾淨終止。 |
| 2 | curl（headers） | 同上 curl 加 `-v` flag | Response 包含 `content-type: text/event-stream`、`x-vercel-ai-ui-message-stream: v1`、`cache-control: no-cache` |
| 3 | Trace 檢視 | curl 測試後，檢查 Langfuse dashboard | 該 request 有一個 trace，`session_id` 符合自動產生或提供的 ID，如有觸發 tool 則 tool observations 正確巢狀 |
| 4 | curl（regenerate） | 先送一則訊息，再用回傳的 session ID 送 regenerate request | 產生新的 SSE stream 包含 regenerated response |
| 5 | 測試套件 | `cd backend && python -m pytest tests/ -v --ignore=tests/poc --ignore=tests/integration` | 所有 unit + API 測試通過 |
| 6 | Lint | `cd backend && ruff check .` | 無錯誤 |

- [ ] 所有 flow verifications 通過

---

### Task 7：Observability 文件更新 + 測試清理

**檔案：**

- Update: `backend/agent_engine/docs/streaming_observability_guardrails.md`
- Update: `backend/agent_engine/CLAUDE.md`

**做什麼、為什麼：** 更新 Rule 3 用語以反映 design decision D5（透過 LangGraph 執行的 tools 不需要 `@observe()`）。保持 guardrails 文件與實際實作一致。

**實作備註：**

更新 `streaming_observability_guardrails.md` 中的 Rule 3，從：
> Apply `@observe()` ONLY to deterministic single-return functions (tools, retrieval helpers, reranking, parsing, post-processing)

改為：
> `@observe()` 僅用於 LangChain/LangGraph 框架外部的 deterministic single-return functions。透過 graph 執行的 tools 不需要 `@observe()`，`CallbackHandler` 已自動 trace（實作了 `on_tool_start`/`on_tool_end`）。當 tool 內部有獨立的子操作需要追蹤（例如內部呼叫另一個 LLM）時，才需要 `@observe()`。

同步更新 `CLAUDE.md` 中對應的 Core Rules section。

**驗證：**

| 範圍 | 指令 | 預期結果 | 原因 |
| --- | --- | --- | --- |
| Guardrails 文件 | 讀取 `docs/streaming_observability_guardrails.md` Rule 3 | 更新後的用語符合 design D5 | 文件與實作一致 |
| CLAUDE.md | 讀取 `CLAUDE.md` Core Rules | Rule 3 已同步 | 入口文件與詳細 guardrails 一致 |
| 完整測試套件 | `cd backend && python -m pytest tests/ -v --ignore=tests/poc --ignore=tests/integration` | 全部通過 | 最終 regression 確認 |

**執行清單：**

- [ ] 更新 `streaming_observability_guardrails.md` 中的 Rule 3
- [ ] 同步 `CLAUDE.md` 中的 Rule 3
- [ ] 執行完整測試套件 — 全部通過
- [ ] Commit：`docs(S1): update observability guardrails Rule 3 for streaming`

---

## Pre-delivery Checklist

### Code Level（TDD）

- [ ] 每個 task 的 targeted verification 通過
- [ ] `cd backend && python -m pytest tests/ -v --ignore=tests/poc --ignore=tests/integration` — 全部通過
- [ ] `cd backend && ruff check .` — 無 lint 錯誤

### Flow Level（Behavioral）

- [ ] 所有 flow verification 步驟已執行並通過
- [ ] Flow: Domain Event Pipeline — PASS / FAIL
- [ ] Flow: End-to-End Streaming — PASS / FAIL

### Summary

- [ ] 兩個 levels 皆通過 → 可交付
- [ ] 任何失敗已記錄原因和下一步行動
