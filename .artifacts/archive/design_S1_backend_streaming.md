# S1 Backend Streaming — Design Document

> S1 subsystem design。定義 backend streaming 的 component 架構、domain event layer、SSE serializer、conversation store、observability 策略與 POC gate。
> 供 `implementation-planning` skill 作為輸入。

---

## 背景

FinLab-X V1 streaming chat 採 subsystem-first 分解：

| Subsystem | 職責 | 依賴 |
|---|---|---|
| **S1** Backend Streaming（本文件） | Orchestrator streaming + FastAPI SSE endpoint | — |
| **S2** Frontend Scaffold（已完成設計） | 前端專案基礎建設 | — |
| **S3** Streaming Chat UI | useChat 整合、message rendering | S1 + S2 |

### 現有架構

- `Orchestrator` 使用 `create_agent()`（LangChain 1.2.10+），回傳 `CompiledStateGraph`
- 目前只有 `ainvoke()`（非 streaming），endpoint 為 `POST /api/v1/chat`
- Langfuse 整合已到位：`CallbackHandler` + `propagate_attributes(session_id=...)`
- Tools 有 `@tool` + `@observe()` decorator（S1 將移除 `@observe()`）

---

## Scope

### S1 包含

1. `Orchestrator.astream_run()` async generator method
2. `StreamEventMapper`：LangGraph chunks → DomainEvent
3. `SSE Serializer`：DomainEvent → AI SDK UIMessage Stream Protocol v1
4. `POST /api/v1/chat/stream` FastAPI SSE endpoint（含 regenerate 支援）
5. LangGraph `InMemorySaver` checkpointer 整合（conversation store）
6. Tool 層面變更：移除 `@observe()`、加入 progress writer
7. Observability guardrails 文件更新
8. Observability POC（5 個 gate）

### S1 不包含

- ❌ 前端任何變更（S3 scope）
- ❌ 現有 `POST /api/v1/chat` endpoint 的修改（保留不動）
- ❌ Persistent conversation store（V2+ 換 `PostgresSaver`）
- ❌ Tool input streaming（V1 不支援 `tool-call-delta`）
- ❌ 任意歷史 message regenerate（V1 只支援最後一條）

---

## 設計決策

| # | 決策 | 選擇 | 理由 |
|---|---|---|---|
| D1 | Streaming 基礎 | `astream(stream_mode=["messages", "updates", "custom"], version="v2")` | `messages` 給 token-level streaming，`updates` 給 node 完成事件，`custom` 給 tool progress。`version="v2"` 統一 chunk format |
| D2 | Tool error wire format | `data-tool-error` custom event | AI SDK v5 UIMessage Stream Protocol v1 的標準 event types 中不存在 `tool-error`（已查閱 `ai-sdk.dev/docs/ai-sdk-ui/stream-protocol` 及 `vercel/ai` source `ai_5_0_0` tag）。`data-*` 是 AI SDK 官方為自訂事件設計的 namespace。**⚠️ 此決策偏離 master design DR-07，需後續修正 master design 和 S3 design 以對齊。** |
| D3 | Conversation store | LangGraph 內建 `InMemorySaver` checkpointer | 取代 master design DR-06 規劃的自建 store interface。Checkpointer 自動管理 state persistence（每個 node 結束後自動存 checkpoint），用 `thread_id` 映射前端 session ID。State 中的 `messages` list 已完整包含 tool call args + results，不需額外儲存。**此為 intentional simplification**：master DR-06 的核心意圖「後端管理歷史、前端只送最新訊息」由 checkpointer 完全滿足。未來可換 `PostgresSaver` |
| D8 | Request body message 型別 | Plain string | S1 接收 `{ message: string }`。S3 的 `prepareSendMessagesRequest` 負責從 `UIMessage` 中提取文字內容後傳送。Backend 不需理解 UIMessage 結構 |
| D4 | Tool progress 機制 | `get_stream_writer()` + try/except graceful fallback | 官方推薦方式（Python >= 3.11）。POC 優先驗證 `ToolRuntime` 方案以取得精確 `tool_call_id` |
| D5 | Tool observability | 移除 tools 上的 `@observe()`，依賴 `CallbackHandler` | `CallbackHandler` 已自動 trace tool name/args/result/duration。`@observe()` 在 LangGraph 環境下產生 disconnected traces（refs: langfuse discussions #5991, #3267）。兩者並存是重複 tracing |
| D6 | Serializer pattern | `functools.singledispatch` | 每個 event type 獨立 register，新增 type 不改既有 code，忘了 register 會 TypeError |
| D7 | Regenerate 策略 | V1: 手動移除 messages 最後一個 assistant turn | 只需處理最後一條。未來任意歷史 regenerate 需引入 `messageId → checkpoint thread_ts` mapping |

---

## 術語對照

S1 內部、前端 request、LangGraph 各自使用不同的名稱指涉同一個概念：

| 概念 | S1 內部命名 | Request body 欄位 | LangGraph config | 說明 |
|---|---|---|---|---|
| Chat session 識別碼 | `session_id` | `id` | `configurable.thread_id` | 同一個值，不同層級不同名稱 |
| Assistant 回覆識別碼 | `message_id` | `messageId`（regenerate 用） | — | S1 在 `astream_run()` 開始時產生 |
| Text block 識別碼 | `text_id` | — | — | S1 mapper 內部產生，SSE wire format 映射為 `"id"` |
| Tool call 識別碼 | `tool_call_id` | — | — | 來自 LLM response 的 `AIMessage.tool_calls[].id` |

---

## Component Architecture

### 資料流（由 LangGraph → HTTP Response）

```
LangGraph Agent (CompiledStateGraph)
    │  astream() 產生 raw chunks
    ▼
Orchestrator.astream_run()
    │  設定 Langfuse CallbackHandler + propagate_attributes
    │  設定 checkpointer thread_id
    │  將 raw chunks 交給 StreamEventMapper
    │  yields DomainEvent
    ▼
StreamEventMapper
    │  1. 格式翻譯：LangGraph chunk shape → DomainEvent
    │  2. 補上缺失事件：text-start/end, start, finish
    │  3. 跨 stream mode 拼湊完整生命週期
    ▼
SSE Serializer (Router 層)
    │  DomainEvent → "data: {json}\n\n"
    ▼
FastAPI Endpoint
    │  StreamingResponse + headers
    │  處理 client disconnect
    ▼
HTTP SSE Response（S1 邊界到此為止）
```

### 元件職責邊界

| 元件 | 知道什麼 | 不知道什麼 |
|---|---|---|
| **Endpoint** | HTTP protocol, headers, disconnect | Domain events 的內容 |
| **SSE Serializer** | AI SDK wire format, JSON encoding | LangGraph, Langfuse |
| **Orchestrator.astream_run()** | Langfuse config, checkpointer config | SSE format |
| **StreamEventMapper** | LangGraph chunk 結構, domain event 定義 | Langfuse, HTTP |
| **LangGraph Agent** | Tools, LLM, state management | Domain events, SSE |

---

## Domain Event 型別定義

Domain Events 是 StreamEventMapper 的產出物，也是 SSE Serializer 的輸入。與 LangGraph 格式和 SSE wire format 都解耦。

### 型別

```python
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
    result: str              # JSON string

@dataclass(frozen=True)
class ToolError:
    tool_call_id: str
    error: str

@dataclass(frozen=True)
class ToolProgress:
    tool_call_id: str
    data: dict               # {status, message, toolName}

@dataclass(frozen=True)
class StreamError:
    error_text: str

@dataclass(frozen=True)
class Finish:
    finish_reason: str       # "stop" | "error"
    input_tokens: int | None = None
    output_tokens: int | None = None

DomainEvent = (
    MessageStart | TextStart | TextDelta | TextEnd |
    ToolCallStart | ToolCallEnd | ToolResult | ToolError |
    ToolProgress | StreamError | Finish
)
```

### Domain Event → SSE Event 對照

| Domain Event | SSE `type` | 來源 stream mode |
|---|---|---|
| `MessageStart` | `start` | mapper 在第一筆 chunk 時補上 |
| `TextStart` | `text-start` | mapper 偵測到新 text block 開始時補上 |
| `TextDelta` | `text-delta` | `messages`（AIMessageChunk.content） |
| `TextEnd` | `text-end` | mapper 偵測到 text block 結束時補上 |
| `ToolCallStart` | `tool-call-start` | `messages`（AIMessageChunk.tool_call_chunks） |
| `ToolCallEnd` | `tool-call-end` | `updates`（agent node 完成） |
| `ToolResult` | `tool-result` | `updates`（tool node 完成，status != error） |
| `ToolError` | `data-tool-error` | `updates`（tool node 完成，status == error） |
| `ToolProgress` | `data-tool-progress` | `custom`（get_stream_writer） |
| `StreamError` | `error` | exception 捕捉 |
| `Finish` | `finish` | stream 結束 |

### SSE Serializer 欄位映射

Domain event 的欄位名是內部命名，serializer 負責轉換為 AI SDK wire format：

- `message_id` → `"messageId"`
- `text_id` → `"id"`
- `tool_call_id` → `"toolCallId"`

### 設計原則

- `frozen=True`：Domain events 是不可變的值物件
- 欄位只放必要資料，不包含 SSE wire format 細節
- `ToolProgress.data` 用 dict 保持彈性
- `ToolResult.result` 是 JSON string（與 AI SDK protocol 一致）
- 沒有 abstract base class，11 個事件用 Union type + `isinstance` 即可
- Domain events 不需要 `transient` 欄位，只有 `ToolProgress` 在 SSE payload 中帶 `"transient": true`

---

## StreamEventMapper 內部邏輯

### Mapper 追蹤的狀態

- **text block 是否開啟** — 決定要不要補 `TextStart` / `TextEnd`
- **哪些 tool calls 正在進行中** — 配對 progress 和 result（`tool_call_id → tool_name` map）
- **是否已發送過 MessageStart** — 確保只發一次

### 處理規則

```
WHEN 收到任何 chunk 且尚未 started:
    emit MessageStart
    mark started

WHEN 收到 messages chunk 且有文字 content:
    IF text block 未開啟:
        emit TextStart（產生新的 text_id）
        mark text block 開啟
    emit TextDelta

WHEN 收到 messages chunk 且有 tool_call_chunks:
    IF text block 開啟中:
        emit TextEnd
        mark text block 關閉
    FOR 每個新的 tool call（之前沒看過的 id）:
        emit ToolCallStart
        記錄到 pending tool calls

WHEN 收到 updates chunk 來自 agent node:
    FOR 每個 pending tool call:
        emit ToolCallEnd

WHEN 收到 updates chunk 來自 tool node:
    FOR 每個 ToolMessage:
        IF status == error:
            emit ToolError
        ELSE:
            emit ToolResult
        從 pending tool calls 移除

WHEN 收到 custom chunk:
    用 toolName 查找對應的 pending tool_call_id
    emit ToolProgress

WHEN stream 結束:
    IF text block 開啟中:
        emit TextEnd
    emit Finish
```

### StreamEventMapper 的三個職責

**1. 格式翻譯**

LangGraph chunk 的 shape 跟 AI SDK event 的 shape 不同。例如：

```
LangGraph: {"type": "messages", "data": (AIMessageChunk(content="讓"), metadata)}
    ↓ mapper
DomainEvent: TextDelta(text_id="txt_001", delta="讓")
```

**2. 補上 AI SDK 需要但 LangGraph 不給的事件**

LangGraph 只是一個 token 一個 token 地吐，它不區分 text block 邊界。AI SDK protocol 規定每段文字必須用 `text-start` 和 `text-end` 包起來。Mapper 用 boolean 追蹤 text block 狀態來在正確時機補上。

**3. 從不同 stream mode 的 chunks 拼湊出完整生命週期**

一個 tool call 的完整資訊分散在三個 stream mode 中：

| 資訊 | 來源 stream mode | 時機 |
|---|---|---|
| Tool name、開始呼叫 | `messages`（tool_call_chunks） | LLM 決定呼叫時 |
| Tool call 定義完成 | `updates`（agent node 完成） | LLM 生成完畢 |
| Tool 執行進度 | `custom`（get_stream_writer） | Tool 執行中 |
| Tool 執行結果 | `updates`（tool node 完成） | Tool 執行完成 |

### Agent Node vs Tool Node 的 Updates 時機

LangGraph ReAct agent 內部是兩個 node 的循環：

```
┌──────────┐          ┌──────────┐
│  agent   │──有tool──→│  tools   │
│  node    │  calls    │  node    │
│ (呼叫LLM)│←─回傳結果─│(執行tool) │
└────┬─────┘          └──────────┘
     │ 沒有 tool calls
     ▼
   結束
```

`stream_mode="updates"` 的規則：每個 node 執行完畢時 emit 一個 update chunk。

- `{"agent": {...}}` — agent node 完成 → LLM 決策結束 → `ToolCallEnd`
- `{"tools": {...}}` — tools node 完成 → tool 執行結束 → `ToolResult` 或 `ToolError`

### ToolCallEnd vs ToolResult 的差異

代表不同時刻的不同事情：

```
LLM 開始生成 tool call → ToolCallStart
LLM 生成完畢           → ToolCallEnd（tool call 的「定義」完成）
    ~~~~~ 中間有時間差 ~~~~~
Tool 執行中            → ToolProgress
Tool 執行完成          → ToolResult（tool 的「執行」完成）
```

前端用這個區分顯示不同 UI 狀態：
- `ToolCallStart` → tool card 出現
- `ToolCallEnd` → 參數確定
- `ToolProgress` → 進度更新
- `ToolResult` → 顯示結果

### Tool Progress 的 tool_call_id 配對

`get_stream_writer()` 發出的 custom chunk 不帶 `tool_call_id`（tool 不知道自己的 call ID）。

**V1 做法**：用 progress data 中的 `toolName` 去 `pending_tool_calls` 反查。

**V1 限制**：同名 tool 被平行呼叫時會有歧義。

**改進方向**：POC 驗證 `ToolRuntime` 是否可用。`ToolRuntime` 提供 `tool_call_id` + `stream_writer`，讓 progress data 帶精確的 `toolCallId`，不需要反查。已知 `ToolRuntime` 有 Pydantic validation bug（langchain-ai/langgraph#6431），需驗證是否已修復。

### Tool Error 偵測

LangGraph 的 tool node 在 `handle_tool_errors` 啟用時：tool 拋 exception → 產生 `ToolMessage(status="error", content="Error: ...")`，stream 不中斷。

Mapper 檢查 `ToolMessage.status`：`"error"` → `ToolError`，其他 → `ToolResult`。

### 完整範例：一次對話的 chunk → event 對照

```
LangGraph chunk                              Mapper 產出的 DomainEvent
───────────────────────────────────────      ─────────────────────────────
messages: AIMessageChunk(content="讓")       MessageStart("msg_001")
                                             TextStart("txt_001")
                                             TextDelta("txt_001", "讓")

messages: AIMessageChunk(content="我查一下")  TextDelta("txt_001", "我查一下")

messages: AIMessageChunk(tool_call_chunks=   TextEnd("txt_001")
  [{name:"yfinance_stock_quote",             ToolCallStart("call_abc", "yfinance_stock_quote")
    id:"call_abc"}])

updates: {"agent": {messages: [AI(...)]}}    ToolCallEnd("call_abc")

custom: {toolName:"yfinance_stock_quote",    ToolProgress("call_abc", {status, message, toolName})
  status:"querying_stock", message:"..."}

updates: {"tools": {messages:                ToolResult("call_abc", '{"price":1045}')
  [ToolMessage(status="success")]}}

messages: AIMessageChunk(content="根據")      TextStart("txt_002")
                                             TextDelta("txt_002", "根據")

messages: AIMessageChunk(content="查詢結果")  TextDelta("txt_002", "查詢結果")

(stream 結束)                                TextEnd("txt_002")
                                             Finish("stop")
```

---

## Orchestrator 變更

### 新增 Checkpointer

```python
create_agent(
    model=model,
    tools=self.tools,
    system_prompt=self.system_prompt,
    middleware=[tool_call_limit],
    checkpointer=InMemorySaver(),       # 新增
)
```

同一個 `thread_id` 的多次 request 自動累積對話歷史。

### 新增 `astream_run()` Method

```
Orchestrator
  ├─ __init__(): 同上 + checkpointer
  ├─ run(): 不變
  ├─ arun(): 不變
  ├─ astream_run(message, session_id) → AsyncGenerator[DomainEvent]   ← 新增
  └─ _build_langfuse_config(): 不變
```

`astream_run()` 的職責：

```
astream_run(message, session_id):
    1. 建立 Langfuse config（CallbackHandler + propagate_attributes）
    2. 建立 StreamEventMapper（產生 message_id）
    3. 呼叫 self.agent.astream(
           input={"messages": [HumanMessage(message)]},
           stream_mode=["messages", "updates", "custom"],
           config={
               "callbacks": [handler],
               "configurable": {"thread_id": session_id}
           },
           version="v2"
       )
    4. FOR 每個 LangGraph chunk:
           domain_events = mapper.process(chunk)
           FOR 每個 event: yield event
    5. stream 結束後:
           closing_events = mapper.finish(...)
           FOR 每個 event: yield event
    6. 如果發生不可恢復的 exception:
           yield StreamError(error_text)
           yield Finish("error")
```

### Error Handling

```
TRY:
    FOR chunk in agent.astream(...):
        yield mapper.process(chunk) 的結果們
    yield mapper.finish("stop")

EXCEPT LLM 不可用 / rate limit / 未知 exception:
    IF text block 開啟中:
        yield TextEnd
    yield StreamError(錯誤訊息)
    yield Finish("error")

FINALLY:
    確保 Langfuse trace 被正確 flush
```

即使出錯，前端也會收到 `error` event + `finish` event，而不是 stream 突然斷掉。

### Client Disconnect

FastAPI `StreamingResponse` 在 client 斷線時取消 async generator。`astream_run()` 的 finally block 做清理，確保 Langfuse trace 被正確 flush。

---

## FastAPI Endpoint

### 規格

```
POST /api/v1/chat/stream

Required Response Headers:
  Content-Type: text/event-stream
  x-vercel-ai-ui-message-stream: v1
  Cache-Control: no-cache
  X-Accel-Buffering: no              # 防止 reverse proxy buffering
```

### 兩種 Request Body

**新訊息**：

```json
{
  "message": "TSMC 最近表現如何？",
  "id": "session-abc-123"
}
```

- `id` 可選，沒給就自動產生 UUID
- `id` 作為 `thread_id` 送入 checkpointer

**Regenerate（Retry）**：

```json
{
  "id": "session-abc-123",
  "trigger": "regenerate",
  "messageId": "msg_001"
}
```

- Endpoint 用 `trigger` 欄位是否存在來區分兩種 flow

### Regenerate 流程

```
1. 用 id 作為 thread_id，從 checkpointer 載入當前 state
2. 從 messages 中移除最後一個 assistant turn
   （最後一個 AIMessage 及其關聯的 ToolMessages）
3. 用剩餘的 messages 作為 context，重新呼叫 agent
4. Stream 新的回覆
```

### Regenerate — V1 限制與未來改進

V1 的 regenerate 只支援最後一條 assistant message（Retry on error 場景）。

未來支援任意歷史 message regenerate 時：
- 需引入 `messageId → checkpoint thread_ts` mapping
- `thread_ts` 是 checkpointer 每個存檔點的唯一識別碼
- Mapping 讓後端能精確回退到指定 message 被生成之前的 state
- Orchestrator 需在每次 `astream_run()` 開始時記錄 `messageId → thread_ts` 對應

### 與現有 Endpoint 的關係

```
POST /api/v1/chat          ← 現有，不動，回傳完整 JSON
POST /api/v1/chat/stream   ← 新增，回傳 SSE stream
```

共用同一個 `Orchestrator` singleton（從 `app.state` 取得）。

---

## Tool 層面變更

### 變更一：移除 `@observe()`

移除所有 tool 上的 `@observe()` decorator：`yfinance_stock_quote`、`yfinance_get_available_fields`、`tavily_financial_search`、`sec_official_docs_retriever`。

原因：
- `CallbackHandler` 已自動 trace tool 的 name、args、result、duration（實作了 `on_tool_start`/`on_tool_end` callback）
- `@observe()` 在 LangGraph 環境下產生 disconnected traces（兩者 contextvars 互不認識）
- 移除後 trace 品質更好（單一來源，正確的 parent-child 關係）

### `@observe()` 的適用時機（更新後的規則）

`@observe()` 僅用於以下場景：
- 不透過 LangGraph/LangChain 框架執行的 deterministic single-return functions
- Tool 內部有獨立的子操作需要追蹤（例如 tool 內部又呼叫了另一個 LLM）

透過 graph 執行的 tools 不需要 `@observe()`，`CallbackHandler` 已自動 trace。

### 變更二：加入 Progress Writer

新增共用 helper `get_progress_writer()`（位於 `streaming/progress_writer.py`）：

```
get_progress_writer():
    TRY: 取得 get_stream_writer()
    EXCEPT RuntimeError: 回傳 no-op function
```

各 tool 加入 progress 呼叫：
- `yfinance_stock_quote` → "查詢 {ticker} 股價..."
- `yfinance_get_available_fields` → "取得 {ticker} 可用欄位..."
- `tavily_financial_search` → "搜尋 {ticker} 相關新聞..."
- `sec_official_docs_retriever` → "搜尋 {ticker} {doc_type}..." → "解析報告內容..."（兩次）

Progress 是 fire-and-forget side effect：tool 的核心職責是回傳結果，progress 失敗不影響功能。

### 變更三：確保 `handle_tool_errors` 啟用

需要 tool error 不中斷 stream，讓 agent 繼續推理。

優先方案：`create_agent()` 層面設定 `handle_tool_errors=True`。
Fallback 方案：tool 內部自行 try/except。

POC 階段確認哪個方案可用。

---

## Observability 變更

### 更新 `streaming_observability_guardrails.md` Rule 3

現有 Rule 3：
> Apply `@observe()` ONLY to deterministic single-return functions (tools, retrieval helpers, reranking, parsing, post-processing)

更新為：
> `@observe()` 僅用於 LangChain/LangGraph 框架外部的 deterministic single-return functions。透過 graph 執行的 tools 不需要 `@observe()`，`CallbackHandler` 已自動 trace（實作了 `on_tool_start`/`on_tool_end`）。當 tool 內部有獨立的子操作需要追蹤（例如內部呼叫另一個 LLM）時，才需要 `@observe()`。

### Streaming 路徑的 Observability 架構

```
FastAPI endpoint（不加 @observe）
  → Orchestrator.astream_run()
       → propagate_attributes(session_id=...)
            → CallbackHandler()（自動繼承 context）
            → agent.astream(config={"callbacks": [handler]})
                 → yields chunks（CallbackHandler 內部自動 trace）
  → SSE serializer 純 passthrough（不涉及 Langfuse）
```

`CallbackHandler` 處理所有 trace lifecycle。SSE 層是純 passthrough。streaming 路徑上不使用 `@observe()`。

---

## POC Gate 策略

S1 implementation 的第一步是 observability POC。全部 5 個 gate 通過後才開始正式 streaming implementation。

### Gate 1：單一 request → 一個穩定的 top-level trace

- 發送一個 streaming request
- Langfuse 上出現恰好一個 trace（不是零個、不是碎片）
- Trace 的 session_id 正確
- **通過標準**：一個 request 對應一個 trace，session_id 正確

### Gate 2：Tool observations 正確 attach 到 parent trace

- 使用會觸發 tool call 的 prompt
- 移除 `@observe()` 後，CallbackHandler 仍 trace tool calls
- **通過標準**：tool observation 存在、name/args/result/duration 有紀錄、是 trace 的 child（不是 disconnected）

### Gate 3：Cancellation 正常關閉 trace

- Streaming 中途關閉連線
- **通過標準**：trace 存在且已關閉（不是永遠 pending）、到斷開為止的 observations 有紀錄

### Gate 4：Exception 可見且不被吞掉

- 使用刻意拋錯的 mock tool
- **通過標準**：exception 出現在 trace 中、SSE output 有 error event + finish event

### Gate 5：並發 request 不會交叉汙染 context

- 同時送 3 個 request，各帶不同 session_id
- **通過標準**：3 個 trace、各 session_id 正確、child observations 不交叉

### POC 產出物

1. 可重複執行的測試腳本（不納入 CI，保留作 regression 參考）
2. 每個 gate 的 Langfuse screenshot 或 trace link 作為 evidence
3. 問題的 root cause 和解決方式記錄

### Gate 失敗處理

任一 gate 失敗 → 分析 root cause：
- `CallbackHandler` 問題 → 檢查 Langfuse 版本 / 回報 issue
- `contextvars` 傳播問題 → 調整 async 邊界處理
- `@observe()` 殘留影響 → 確認全部移除

---

## Edge Cases

### 空訊息 / 無效輸入

Endpoint 在呼叫 `astream_run()` 之前驗證 `message`：
- 空字串或純空白 → 回傳 HTTP 422（不進入 streaming）
- `id` 未提供 → 自動產生 UUID

### Regenerate 找不到 session

`InMemorySaver` 在 server 重啟後會遺失所有 state。Regenerate request 帶著一個不存在的 `id` 時：
- Checkpointer 載入 → 得到空 state → 沒有 messages 可以移除
- 回傳 HTTP 404 或包含 error message 的 SSE stream（不進入正常 streaming flow）

### 同 session 並發 request

同一個 `session_id` 同時送兩個 streaming request 可能導致 checkpointer state race condition。

V1 處理方式：Endpoint 層用 per-session lock（簡單的 in-memory dict of asyncio.Lock），同一個 `session_id` 的 request 必須序列化執行。第二個 request 等待第一個完成，或回傳 HTTP 409 Conflict。

### Tool progress lookup 失敗

當 custom chunk 的 `toolName` 在 `pending_tool_calls` 中找不到對應的 `tool_call_id` 時，靜默丟棄該 progress event（不 emit ToolProgress）。這是 fire-and-forget 的 side effect，不影響核心 flow。

### finishReason 映射

| LangGraph 結束原因 | AI SDK `finishReason` |
|---|---|
| 正常完成（agent 不再呼叫 tool） | `"stop"` |
| `ToolCallLimitMiddleware` 達到上限 | `"stop"`（middleware 中斷後 agent 仍產生最終回覆） |
| Exception / LLM 不可用 | `"error"` |

---

## 模組結構

### 新增的目錄與檔案

```
backend/
├── agent_engine/
│   ├── agents/
│   │   └── base.py                  ← 修改：加 checkpointer, 加 astream_run()
│   ├── tools/
│   │   ├── financial.py             ← 修改：移除 @observe, 加 progress writer
│   │   └── sec.py                   ← 修改：移除 @observe, 加 progress writer
│   ├── streaming/                   ← 新增：整個目錄
│   │   ├── __init__.py
│   │   ├── domain_events.py         ← Domain Event type definitions (dataclass)
│   │   ├── event_mapper.py          ← StreamEventMapper: LangGraph chunks → DomainEvent
│   │   ├── sse_serializer.py        ← singledispatch: DomainEvent → SSE wire format
│   │   └── progress_writer.py       ← get_progress_writer() helper for tools
│   ├── docs/
│   │   └── streaming_observability_guardrails.md  ← 修改：更新 Rule 3
│   └── CLAUDE.md                    ← 修改：同步 Rule 3
├── api/
│   ├── main.py                      ← 修改：註冊新 router
│   └── routers/
│       ├── chat.py                  ← 不動
│       └── chat_stream.py           ← 新增：POST /api/v1/chat/stream
└── tests/
    ├── streaming/                   ← 新增
    │   ├── test_domain_events.py
    │   ├── test_event_mapper.py
    │   └── test_sse_serializer.py
    ├── api/
    │   └── test_chat_stream.py      ← 新增
    └── poc/                         ← 新增（不納入 CI）
        └── test_observability_poc.py
```

### 依賴方向

```
chat_stream.py（router）
    │  imports
    ├─ sse_serializer.py
    └─ base.py（Orchestrator.astream_run）
           │  imports
           ├─ event_mapper.py
           └─ domain_events.py

tools/financial.py, tools/sec.py
    │  imports
    └─ streaming/progress_writer.py
```

- `domain_events.py` 不依賴任何其他模組（純資料定義）
- `event_mapper.py` 只依賴 `domain_events.py` + LangChain message types
- `sse_serializer.py` 只依賴 `domain_events.py` + `json`
- 沒有循環依賴

### 修改檔案清單

| 檔案 | 變更類型 | 內容 |
|---|---|---|
| `agents/base.py` | 修改 | 加 `InMemorySaver` checkpointer、新增 `astream_run()` |
| `tools/financial.py` | 修改 | 移除 `@observe()`、加 progress writer |
| `tools/sec.py` | 修改 | 移除 `@observe()`、加 progress writer |
| `streaming/domain_events.py` | 新增 | 11 個 DomainEvent dataclass + Union type |
| `streaming/event_mapper.py` | 新增 | StreamEventMapper class |
| `streaming/sse_serializer.py` | 新增 | singledispatch serialize function |
| `streaming/progress_writer.py` | 新增 | get_progress_writer() helper |
| `api/routers/chat_stream.py` | 新增 | SSE streaming endpoint |
| `api/main.py` | 修改 | 註冊 `chat_stream.router` |
| `docs/streaming_observability_guardrails.md` | 修改 | 更新 Rule 3 |
| `CLAUDE.md` | 修改 | 同步 Rule 3 |

新增 7 個檔案、修改 6 個檔案。不刪除任何現有檔案。

---

## SSE Wire Format 參考

### 必要 Response Headers

```
Content-Type: text/event-stream
x-vercel-ai-ui-message-stream: v1
Cache-Control: no-cache
X-Accel-Buffering: no
```

### 完整 SSE Stream 範例（帶 tool call）

```
data: {"type":"start","messageId":"msg_001"}

data: {"type":"text-start","id":"txt_001"}

data: {"type":"text-delta","id":"txt_001","delta":"讓我查一下"}

data: {"type":"text-end","id":"txt_001"}

data: {"type":"tool-call-start","toolCallId":"call_abc","toolName":"yfinance_stock_quote"}

data: {"type":"tool-call-end","toolCallId":"call_abc"}

data: {"type":"data-tool-progress","toolCallId":"call_abc","data":{"status":"querying_stock","message":"查詢 2330.TW 股價...","toolName":"yfinance_stock_quote"},"transient":true}

data: {"type":"tool-result","toolCallId":"call_abc","result":"{\"price\":1045}"}

data: {"type":"text-start","id":"txt_002"}

data: {"type":"text-delta","id":"txt_002","delta":"根據查詢結果，台積電目前股價為 NT$1,045。"}

data: {"type":"text-end","id":"txt_002"}

data: {"type":"finish","finishReason":"stop","usage":{"inputTokens":150,"outputTokens":85}}
```

### Tool Error 範例

```
data: {"type":"data-tool-error","toolCallId":"call_def","error":"yfinance API timeout after 10s"}
```

### Stream Error 範例

```
data: {"type":"error","error":"LLM service unavailable"}

data: {"type":"finish","finishReason":"error"}
```

---

## 與其他 Subsystem 的介面契約

### S1 → S3

- **Endpoint**: `POST /api/v1/chat/stream`
- **Request body（新訊息）**: `{ message: string, id?: string }`
- **Request body（Regenerate）**: `{ id: string, trigger: "regenerate", messageId: string }`
- **Response header**: `x-vercel-ai-ui-message-stream: v1`
- **Event taxonomy**: 見 Domain Event → SSE Event 對照表
- **Error events**: `data-tool-error`（stream 繼續）/ `error`（stream 結束）

### 依賴

- **LangGraph**: `create_agent()` + `InMemorySaver` + `astream()` + `get_stream_writer()`
- **Langfuse**: `CallbackHandler` + `propagate_attributes()`
- **FastAPI**: `StreamingResponse`

---

## 跨文件修正事項

S1 設計過程中發現以下需要修正其他文件的事項：

| 文件 | 需修正內容 | 原因 |
|---|---|---|
| **master design** DR-07 | `tool-error` → `data-tool-error` | AI SDK v5 沒有標準 `tool-error` event type（查閱 `ai-sdk.dev/docs/ai-sdk-ui/stream-protocol` 及 `vercel/ai` source `ai_5_0_0` tag 確認）|
| **master design** DR-06 | Conversation store interface → LangGraph checkpointer | Checkpointer 完全滿足「後端管理歷史」的需求，自建 interface 是不必要的抽象 |
| **S3 design** 介面契約 | `tool-error` → `data-tool-error` | S3 需用 `onData` callback 處理 `data-tool-error` custom event，而非依賴 AI SDK 原生 parsing |
| **S3 design** request body | `message: UIMessage` → `message: string`（由 S3 transport 提取文字） | S1 接收 plain string，S3 的 `prepareSendMessagesRequest` 負責從 UIMessage 提取 content |

---

## Must NOT Have（範圍護欄）

- ❌ 前端任何變更
- ❌ 修改現有 `POST /api/v1/chat` endpoint
- ❌ Persistent conversation store（PostgresSaver 等）
- ❌ Tool input streaming（`tool-call-delta`）
- ❌ 任意歷史 message regenerate
- ❌ Multi-agent routing
- ❌ WebSocket（用 SSE）
