# Multi-Provider Streaming with Reasoning — Feature Spec

> Status: Draft
> Owner: TBD
> Related:
> - Backend: `backend/agent_engine/streaming/`, `backend/agent_engine/agents/versions/`, `backend/agent_engine/utils/model_context_registry.yaml`, `backend/evals/scenarios/language_policy/eval_spec.yaml`
> - Frontend: `frontend/src/components/organisms/AssistantMessage.tsx`
> - Dependencies: `pyproject.toml`, `backend/.env`

## 1. Context

這份 spec 把兩件互相耦合的工作合併處理：

1. **Provider 切換**：把 agent model 從 OpenAI 切到 Gemini 2.5 Flash，judge model 切到 GPT-5.4-mini（cross-vendor judging）
2. **Streaming pipeline 多 provider 化**：解決 (1) 衍生的 wire format 不相容問題，並順勢支援 reasoning content streaming

兩件原本可以分開做，但 (1) 一旦改下去，(2) 的 bug 就會立刻在前端炸出 — 所以實作層面綁在一起。

### 1.1 為什麼 Streaming Pipeline 需要改

目前 `StreamEventMapper` (`event_mapper.py:74`) 隱含假設 `AIMessageChunk.content` 是 `str`：

```python
events.append(TextDelta(text_id=self._current_text_id, delta=msg_chunk.content))
```

這個假設只對 **OpenAI Chat Completions API** 成立。當 agent model 切到任一以下 provider，`content` 就會變成 `list[ContentBlock]`：

- Gemini 2.5 Flash（thinking on / off 都可能）
- Anthropic Claude 4.x
- OpenAI Responses API（gpt-5.4 / o3 等）

list-of-blocks 直接被當成 string 送出後，前端 AI SDK v6 schema 驗證失敗（`text-delta.delta` 要求 string），整個訊息流斷掉。

### 1.2 為什麼順帶處理 Reasoning

新世代 reasoning models（OpenAI o3 / gpt-5、Anthropic Extended Thinking、Gemini 2.5 thinking）在 streaming 中會額外產生「推理內容」block。目前完全被丟棄。如果未來要把推理過程呈現給使用者（trust / debugging / education），需要建立 wire protocol 與 UI 容器。

把這個跟 (1) 一起做的理由是：兩者**改動同一個 mapper state machine**。分兩次做會把 mapper 改兩遍、tests 也要改兩遍，不划算。

### 1.3 Model Swap 的決策背景

- 過去 codebase 統一用 OpenAI；Provider 互換只在腦中假設可行，實際從未驗證
- Gemini 2.5 Flash 有 1M context、cost 低、適合作為 v1-v5 五個 version 的共用 baseline
- LLM-as-judge 過去用 `gpt-4o`，跟 agent 同 vendor 會有 self-preference bias
- 設計文件（`design_reference.md` §8.3）原本就有 cross-vendor judge 的 design intent，但沒落地

## 2. Problem Statement

| 問題 | 影響 |
|---|---|
| Agent 全用 OpenAI，無法驗證 provider-agnostic 設計 | 換 provider 風險未知 |
| Judge `gpt-4o` 跟 agent 同 vendor → self-preference bias | LLM-as-judge 結果偏頗 |
| `event_mapper.py:74` 直接把 `chunk.content` 餵給 `TextDelta.delta` | Gemini / Anthropic / OpenAI Responses API streaming 直接打壞前端 |
| Reasoning content（thinking / summary）目前完全被忽略 | 即使後端 model 在思考，使用者只看到一段空白等待 |
| 無 provider-agnostic 抽象 | 換 provider 就要改 mapper |

## 3. Goals / Non-Goals

### Goals

- v1-v5 五個 agent version 統一切到 Gemini 2.5 Flash
- LLM-as-judge 改用 cross-vendor 的 GPT-5.4-mini
- 後端 streaming pipeline 對任意 LangChain v1 chat model provider 可用，不依賴 provider-specific 假設
- Reasoning content 以獨立 stream channel 暴露給前端，不混入 final answer text
- Wire format 對齊 AI SDK v6 native event types（`reasoning-start` / `reasoning-delta` / `reasoning-end`），讓 `useChat` 自動 populate `message.parts`
- 對非 reasoning model（如 Gemini 2.5 Flash without thinking）保持 zero overhead
- Test suite 通過後可以實際丟一輪 streaming chat 給使用者，畫面正常呈現

### Non-Goals

- 不實作 judge model whitelist 驗證（`design_reference.md` §8.3 提及但屬另一個 PR）
- 不做 reasoning content 的 LLM-as-judge / scorer（純 streaming display）
- 不處理 Anthropic / Gemini 多輪 thinking signature round-trip 的設計（這由 LangGraph checkpointer 管，本 spec 假設 state 已正確保存，僅做 E2E 驗證）
- 不改變 `Orchestrator.invoke` / `Orchestrator.invoke_async` 的 non-streaming 路徑
- 不重做 frontend reasoning 折疊 / 動畫的 Design system（沿用現有 `ReasoningIndicator` 視覺語彙，但 part 元件是新增）
- 不引入 Vertex AI（採 Gemini Developer API + `GOOGLE_API_KEY`）
- 不引入 Anthropic 為 default provider（保留為未來選項）

## 4. Provider Reasoning Streaming Matrix

| Provider | Model 類別 | `chunk.content` 形態 | Reasoning streaming | Reasoning 內容 | 依賴 |
|---|---|---|---|---|---|
| OpenAI | Chat Completions（gpt-4o, gpt-3.5） | `str` | 無 | — | 舊 API |
| OpenAI | Responses 非 reasoning（gpt-5.4, gpt-5.4-mini） | `list[block]` | 無 | text only | LangChain v1.2.0 起 default |
| OpenAI | Responses reasoning（o1, o3, gpt-5 reasoning） | `list[block]` | 有 | reasoning **summary** 多段 + `encrypted_content` opaque blob | 需 `include=["reasoning.encrypted_content"]` |
| Anthropic | Claude 4.x + Extended Thinking | `list[block]` | 有 | 完整 thinking 文字 + per-block `signature` | `thinking={"type":"enabled","budget_tokens":N}` |
| Gemini | 2.5 Flash / Pro with thinking | `list[block]` | 有 | thought summary 文字（部分 tier） + `thoughtSignature` | `thinking_budget` / `include_thoughts` |
| Gemini | 1.5 / 2.0 / 2.5 thinking off | `str` 或 `list[block]` | 無 | text only | — |

關鍵不對稱：

- **OpenAI reasoning model 只給 summary**，不給完整推理。
- **Anthropic 給完整 thinking 文字**，是三家中最詳細的。
- **Gemini 給 summary**（依 tier 不同），但每段 text block 都會帶 `thoughtSignature` opaque blob，多輪 thinking continuity 必須回傳。
- **三家的 signature / encrypted_content 性質一致**：客戶端不解讀，只負責原封 round-trip。

對應到本 feature 的決策：

- 本次 swap 後 default 是 **Gemini 2.5 Flash without thinking**（最便宜、最快），所以 default path 走「list[block] but no reasoning blocks」
- Reasoning streaming 的 wire / UI 落地，但**初版不在 5 個 agent config 開啟 thinking**
- 開啟 thinking 是後續 prompt-engineering / cost 取捨，不在本 spec 範圍

## 5. Architecture Overview

```
LangGraph astream(stream_mode=["messages", ...])
        │
        ▼
   AIMessageChunk
   ├── content: str | list[dict]  ← provider raw shape
   └── content_blocks: list[StandardContentBlock]  ← LangChain v1 normalized lazy property
        │
        ▼
StreamEventMapper._handle_messages
   for block in chunk.content_blocks:
       if block.type == "text":      → TextStart / TextDelta / TextEnd
       elif block.type == "reasoning": → ReasoningStart / ReasoningDelta / ReasoningEnd
       (other block types: ignored for now)
        │
        ▼
SSE Serializer (singledispatch)
   ├── TextDelta       → AI SDK v6 "text-delta"
   └── ReasoningDelta  → AI SDK v6 "reasoning-delta"
        │
        ▼
Frontend (useChat from @ai-sdk/react)
   message.parts: [
       { type: "reasoning", text: "...", state: "streaming" | "done" },
       { type: "text", text: "...", state: "streaming" | "done" },
       ...
   ]
        │
        ▼
AssistantMessage (parts.map dispatcher)
   ├── part.type === "text"      → Markdown 渲染（既有）
   ├── part.type === "reasoning" → <ReasoningPart />（新增，collapsible）
   └── part.type === "tool" / "tool-*" → <ToolCard />（既有）
```

## 6. Model Swap Design

### 6.1 Agent Model 切換

5 個 version config 全部改：

| File | 變更 |
|---|---|
| `backend/agent_engine/agents/versions/v1_baseline/orchestrator_config.yaml` | `model.name`: `"gpt-4o-mini"` → `"google_genai:gemini-2.5-flash"` |
| `backend/agent_engine/agents/versions/v2_reader/orchestrator_config.yaml` | `model.name`: `"gpt-4o"` → `"google_genai:gemini-2.5-flash"` |
| `backend/agent_engine/agents/versions/v3_quant/orchestrator_config.yaml` | 同上 |
| `backend/agent_engine/agents/versions/v4_graph/orchestrator_config.yaml` | 同上 |
| `backend/agent_engine/agents/versions/v5_analyst/orchestrator_config.yaml` | 同上 |

`temperature` 與 `constraints.max_tool_calls_per_run` 不變。

**Provider prefix `google_genai:`**：必填，因為 `init_chat_model` 對 `gpt-*` 會 auto-infer 但 `gemini-*` 不會。已透過 LangChain MCP 文件確認此 form：

```python
init_chat_model("google_genai:gemini-2.5-flash", temperature=0.0)
# → ChatGoogleGenerativeAI(model="gemini-2.5-flash")
```

### 6.2 Judge Model 切換

| File | 變更 |
|---|---|
| `backend/evals/scenarios/language_policy/eval_spec.yaml` | `scorers[*].model`: `gpt-4o` → `gpt-5.4-mini` |

判斷依據：

- agent vendor（Google）≠ judge vendor（OpenAI）→ cross-vendor，避免 self-preference bias
- judge tier 至少要 ≥ agent tier；GPT-5.4-mini ≈ Gemini 2.5 Flash 的 cross-family 對等
- 不需更貴的 GPT-5.4 — judge 跑 24 題的 cost 不是瓶頸，但也不必 over-spec

### 6.3 Dependency

`pyproject.toml` `[project.dependencies]` 新增：

```toml
"langchain-google-genai>=2.0.0",
```

放在 `langchain-openai` 之後（字母序）。`uv sync` 會自動帶入 transitive：`google-genai`, `google-auth`, `cryptography`, `pyasn1`, `pyasn1-modules` 等。

### 6.4 Environment Variables

| Var | 用途 | 是否新增 |
|---|---|---|
| `OPENAI_API_KEY` | judge（GPT-5.4-mini）使用 | 已存在 |
| `GOOGLE_API_KEY` | agent（Gemini 2.5 Flash）使用 | **新增** |
| `TAVILY_API_KEY` / `EDGAR_IDENTITY` / `LANGFUSE_*` / `BRAINTRUST_*` | 既有 tools / observability | 不變 |

`backend/.env` 是 gitignored，使用者需手動加上 `GOOGLE_API_KEY`，從 [Google AI Studio](https://aistudio.google.com/apikey) 申請。

PR README / CHANGELOG 須註明此 env var 新增需求。

### 6.5 Model Context Registry

`backend/agent_engine/utils/model_context_registry.yaml` 新增 entry：

```yaml
google_genai:gemini-2.5-flash:
  max_input_tokens: 1048576
  source: manual
```

理由：

- `_render_prompt` 用 model name 查 context window 做 system prompt soft cap；找不到就 fallback default 128k 並 warn-once
- Gemini 2.5 Flash 的 1M context 比 default 大很多，soft cap 會踩錯
- `refresh_model_context_registry.py` 走 litellm 查詢，但 litellm 對 `google_genai:` prefix 形式可能不認得 → 用 `source: manual` 標記，refresh 時保留

既有 `gpt-4o` 與 `gpt-4o-mini` entry **保留不刪**：tests 還在 reference，且未來可能切回。

### 6.6 Code 是否需要動

- `backend/agent_engine/agents/base.py:229` 呼叫 `init_chat_model(config.model.name, temperature=...)` — `config.model.name` 已含 provider prefix，**code 零變動**
- 既有 `Orchestrator` 與 `_render_prompt` 完全不需改

### 6.7 Risks（Model swap 限定）

| ID | 風險 | 處理 |
|---|---|---|
| MS1 | Gemini API quota / rate limit 比 OpenAI 嚴格 | 啟動前先查 quota；eval batch 必要時加 rate limit |
| MS2 | Gemini tool-calling 行為與 OpenAI 不同（function schema 解讀、parallel tool calls 支援） | 要跑既有 integration test 全套；特別注意 `tavily_financial_search` 等多參數 tool |
| MS3 | Gemini 2.5 Flash 對 Markdown 輸出風格與 GPT 不同 | language_policy eval 可能要重新跑、調 rubric |
| MS4 | `gpt-5.4-mini` 是否經由 OpenAI API 直接可用（autoevals.LLMClassifier 走 OpenAI SDK） | 確認 `autoevals` 對 `gpt-5.4-mini` 名稱支援；若不支援需 pin specific dated alias |
| MS5 | Eval task 既有 mock fixture 用 `gpt-4o-mini` 字面值（`test_eval_tasks.py`） | 純測試 fixture，不影響行為，但更新成新名稱比較貼近現實 |

## 7. Streaming Backend Design

### 7.1 New Domain Events

`backend/agent_engine/streaming/domain_events_schema.py`：

```python
@dataclass(frozen=True)
class ReasoningStart:
    reasoning_id: str

@dataclass(frozen=True)
class ReasoningDelta:
    reasoning_id: str
    delta: str

@dataclass(frozen=True)
class ReasoningEnd:
    reasoning_id: str

DomainEvent = (
    MessageStart | TextStart | TextDelta | TextEnd |
    ReasoningStart | ReasoningDelta | ReasoningEnd |  # ← new
    ToolCall | ToolResult | ToolError | ToolProgress |
    StreamError | Finish
)
```

### 7.2 Mapper 改造

**核心改變**：從直接讀 `chunk.content`（一條訊息一個 string）改為遍歷 `chunk.content_blocks`（normalized typed blocks）。

```pseudo
def _handle_messages(chunk):
    msg_chunk, _metadata = chunk["data"]
    if isinstance(msg_chunk, ToolMessage): return []

    if not self._message_started:
        emit MessageStart
        self._message_started = True

    blocks = self._iter_content_blocks(msg_chunk)
    # 注意：streaming chunk 通常單 block，但需處理 multi-block case

    for block in blocks:
        if block.type == "text" and block.text:
            self._switch_to_text_block()
            emit TextDelta(text_id=self._current_text_id, delta=block.text)
        elif block.type == "reasoning" and block.reasoning:
            self._switch_to_reasoning_block()
            emit ReasoningDelta(reasoning_id=self._current_reasoning_id, delta=block.reasoning)

    # tool_call_chunks handling unchanged
    if msg_chunk.tool_call_chunks:
        self._close_open_blocks()
        # ... existing logic
```

State machine 加新狀態：

| State | 進入條件 | 離開時 emit |
|---|---|---|
| `_text_block_open` | 收到 text block 且 reasoning 已關 | 切換到 reasoning / tool-call 時 emit `TextEnd` |
| `_reasoning_block_open` | 收到 reasoning block 且 text 已關 | 切換到 text / tool-call 時 emit `ReasoningEnd` |

block id 計數：text 跟 reasoning 各自獨立的 counter（`text-0`, `text-1`, ..., `reasoning-0`, `reasoning-1`, ...）。

### 7.3 `content_blocks` Lazy Property 風險

LangChain v1 文件主要強調 `AIMessage.content_blocks`。**`AIMessageChunk` 是否有等效 property 需實測**。

實測 plan：
1. 寫一個 minimal repro 用 `ChatGoogleGenerativeAI(model="gemini-2.5-flash")` `.astream()` 拿到 chunk
2. 檢查 `hasattr(chunk, "content_blocks")` 與返回值
3. 同樣對 `ChatOpenAI(use_responses_api=True)` 與 `ChatAnthropic(thinking=...)` 跑一遍

**Fallback**：如果 chunk-level 沒有 lazy property，自寫 normalization helper：

```python
def _iter_content_blocks(chunk) -> Iterator[ContentBlock]:
    content = chunk.content
    if isinstance(content, str):
        yield {"type": "text", "text": content}
        return
    if isinstance(content, list):
        for raw in content:
            if isinstance(raw, str):
                yield {"type": "text", "text": raw}
            elif isinstance(raw, dict):
                # provider-specific 翻譯到 standard:
                # Anthropic: {type: "thinking", thinking, signature} → {type: "reasoning", reasoning}
                # Gemini   : {type: "text", text, extras.signature} → {type: "text", text}
                # Gemini   : {type: "thought", text, ...}            → {type: "reasoning", reasoning}
                # OpenAI Responses: {type: "reasoning", summary[*].text, encrypted_content} → {type: "reasoning", reasoning}
                yield _normalize_block(raw)
```

優先用 LangChain native `content_blocks`，fallback 在 LangChain 沒給的情況才用。

### 7.4 SSE Serializer 擴充

`backend/agent_engine/streaming/sse_serializer.py` 新增三個 `singledispatch` 註冊：

```python
@serialize_event.register
def _(event: ReasoningStart) -> str:
    return _sse({"type": "reasoning-start", "id": event.reasoning_id})

@serialize_event.register
def _(event: ReasoningDelta) -> str:
    return _sse({"type": "reasoning-delta", "id": event.reasoning_id, "delta": event.delta})

@serialize_event.register
def _(event: ReasoningEnd) -> str:
    return _sse({"type": "reasoning-end", "id": event.reasoning_id})
```

### 7.5 Tests

- `test_event_mapper.py`：
  - OpenAI string content → 一條 text-delta（regression）
  - Gemini list-of-blocks（含 `extras.signature`）→ 一條 text-delta，**signature 不外洩到前端**
  - Anthropic `[thinking, text]` → reasoning-* 在前、text-* 在後，順序正確
  - Reasoning → text → reasoning interleave → 多組 block id 正確切換
  - tool_call_chunks 中斷時關閉所有 open blocks
- `test_sse_serializer.py`：3 個新 wire format 測試

## 8. Streaming Frontend Design

### 8.1 New Component

`frontend/src/components/atoms/ReasoningPart.tsx`：

```tsx
interface ReasoningPartProps {
  text: string;
  isStreaming: boolean;
}

export function ReasoningPart({ text, isStreaming }: ReasoningPartProps) {
  // collapsed by default when done; expanded while streaming
  // 灰色斜體 / monospace small / 折疊圖示
  // 顯示 char count when collapsed
}
```

UX 預設行為：

| Phase | 預設展開？ | 顯示內容 |
|---|---|---|
| Streaming | 展開（live append） | "Thinking..." + 逐字顯示 |
| Done | 折疊 | "Thought process (N chars)" + click 展開 |

### 8.2 Dispatcher 改造

`AssistantMessage.tsx` parts.map 加新分支：

```tsx
parts.map((part, i) => {
  if (part.type === "reasoning") {
    return <ReasoningPart key={i} text={part.text} isStreaming={isStreaming && isLast} />;
  }
  if (part.type === "tool" || ...) { /* existing */ }
  return null;
});
```

### 8.3 ReasoningIndicator 互動

既有 `shouldShowReasoningIndicator` 邏輯（pre-response 等待動畫）：

- 改判定條件：只要 last assistant message 有任意 part（含 reasoning），就讓 inline cursor 接手
- Edge case：如果第一個 part 是 reasoning，idle dot → reasoning part 過渡要平順（不閃）

### 8.4 Tests

- `__tests__/AssistantMessage.test.tsx`：reasoning + text 組合 render order
- `__tests__/ReasoningPart.test.tsx`：streaming live append、done 折疊、char count
- `reasoning-indicator-logic.test.ts`：reasoning part 出現後 idle dot 收掉

## 9. Wire Protocol

對齊 AI SDK v6 native types（前端 `useChat` 內建 parser 處理）：

```jsonl
data: {"type":"start","messageId":"msg_xxx","messageMetadata":{"sessionId":"..."}}

data: {"type":"reasoning-start","id":"reasoning-0"}
data: {"type":"reasoning-delta","id":"reasoning-0","delta":"Let me think..."}
data: {"type":"reasoning-delta","id":"reasoning-0","delta":" about this..."}
data: {"type":"reasoning-end","id":"reasoning-0"}

data: {"type":"text-start","id":"text-0"}
data: {"type":"text-delta","id":"text-0","delta":"The answer is"}
data: {"type":"text-delta","id":"text-0","delta":" 42."}
data: {"type":"text-end","id":"text-0"}

data: {"type":"finish",...}
```

訊號順序契約：

- block id 在同類型內遞增、跨 block 不重用
- block 的 `start` 必先於同 id 的 `delta`，`end` 必後於同 id 的最後 `delta`
- reasoning ↔ text 切換允許多次往返（reasoning-0 → text-0 → reasoning-1 → text-1 …）

## 10. Risks & Open Questions

### Streaming 部分

| ID | 風險 | 處理方向 |
|---|---|---|
| R1 | `AIMessageChunk` 是否提供 `content_blocks` lazy property | POC 實測；不提供則寫 fallback normalizer |
| R2 | Gemini `thoughtSignature` 多輪 round-trip 是否被 LangGraph state 正確保存 | E2E test：跑兩輪 thinking，第二輪檢查 model state 含 signature |
| R3 | OpenAI Responses API reasoning summary 內容稀少（不同 model 差異大） | 文件揭露此限制；UI 在 reasoning 為空時不顯示 ReasoningPart |
| R4 | Anthropic `signature` 變動造成 cache invalidation | spec 內不直接處理；待採用 Anthropic 時再評估 |
| R5 | Tool-call interleaving with reasoning（Anthropic 常 thinking → tool_use → thinking）| Mapper state machine 必須把 tool_call_chunks 也視為 block 切換點 |
| R6 | 既有 `shouldShowReasoningIndicator` 命名衝突 | 維持函式名（pre-response idle 動畫），ReasoningPart 是不同概念 |

### Model swap 部分

| ID | 風險 | 處理 |
|---|---|---|
| MS1 | Gemini API quota / rate limit 比 OpenAI 嚴格 | 啟動前先查 quota；eval batch 必要時加 rate limit |
| MS2 | Gemini tool-calling 行為與 OpenAI 不同 | 跑全套 integration test，特別注意 `tavily_financial_search` 多參數 tool |
| MS3 | Gemini 2.5 Flash Markdown 輸出風格與 GPT 不同 | language_policy eval 重跑、必要時調 rubric |
| MS4 | `autoevals.LLMClassifier` 是否支援 `gpt-5.4-mini` | 實測；不支援則 pin dated alias |
| MS5 | Test fixture 用 `gpt-4o-mini` 字面值 | 純 mock，不影響行為，但 PR 一併更新 |

## 11. Implementation Phases

建議分兩階段，每階段獨立可驗收。第一階段是「修 bug」，第二階段才是「新功能」。

### Phase 1 — Model Swap + Streaming Bug Fix（B-minus）

完成「**換 provider 後 chat 還能正常跑**」這個最小可用態。Reasoning 暫時 drop，前端零變動。

**Backend**

| File | 動作 | Lines |
|---|---|---|
| `pyproject.toml` | + `langchain-google-genai>=2.0.0` | +1 |
| `uv.lock` | uv sync 自動更新 | ~+130 |
| 5 個 `orchestrator_config.yaml` | `model.name` → `google_genai:gemini-2.5-flash` | 改 5 |
| `language_policy/eval_spec.yaml` | judge `gpt-4o` → `gpt-5.4-mini` | 改 1 |
| `model_context_registry.yaml` | 加 Gemini entry | +3 |
| `streaming/event_mapper.py` | 改用 `content_blocks` 正規化；reasoning blocks drop | +30 / 改 5 |
| `tests/streaming/test_event_mapper.py` | Gemini list-of-blocks fixture + OpenAI str regression | +30 |

**Env**

- 使用者手動加 `GOOGLE_API_KEY` 到 `backend/.env`

**驗收**

- `uv sync --extra dev` 通過
- `pytest backend/tests/agents/ backend/tests/evals/ backend/tests/streaming/` 全綠
- 啟動 backend + frontend，跑一輪 streaming chat，前端正常顯示文字（不炸 schema 驗證）
- `gpt-4o-mini` 與 `gpt-4o` 在 registry 暫保留以避免 test fixture 不一致

### Phase 2 — Reasoning Streaming（B-full）

在 Phase 1 之上加 reasoning event types、SSE wire、frontend ReasoningPart。

**Backend**

| File | 動作 | Lines |
|---|---|---|
| `streaming/domain_events_schema.py` | 新增 ReasoningStart/Delta/End + union | +15 |
| `streaming/event_mapper.py` | reasoning block 路徑、state machine 擴充 | +20 |
| `streaming/sse_serializer.py` | 3 個 `singledispatch` 註冊 | +15 |
| `tests/streaming/test_event_mapper.py` | reasoning 路徑、interleave、tool-call 切換 | +80 |
| `tests/streaming/test_sse_serializer.py` | 3 個 wire format 測試 | +30 |

**Frontend**

| File | 動作 | Lines |
|---|---|---|
| `components/atoms/ReasoningPart.tsx` | 新增 collapsible reasoning UI | +40 |
| `components/organisms/AssistantMessage.tsx` | parts dispatcher 加 reasoning 分支 | +10 / 改 5 |
| `lib/reasoning-indicator-logic.ts` | idle dot 過渡微調 | 改 ~5 |
| `__tests__/...` | reasoning render、組合、idle dot 收掉 | +40 |

**驗收**

- Anthropic Claude 4.x + Extended Thinking：reasoning 文字逐字顯示在 ReasoningPart，最終 answer 顯示在 text part
- Gemini 2.5 Flash with thinking（手動 enable）：thought summary 顯示在 ReasoningPart（依 tier 內容多寡而定）
- OpenAI o3 / gpt-5 reasoning：summary 顯示，多輪 thinking 透過 LangGraph state 正常 round-trip
- 非 reasoning model（gemini-2.5-flash without thinking）：UI 不顯示空的 ReasoningPart

### 為什麼建議 Phase 1 / 2 在同一個 PR

雖然兩階段獨立可驗收，但**實際 review 與 merge 建議綁同一個 PR**，理由：

- Phase 1 後 streaming 可用，但 reasoning 完全消失（包括既有 OpenAI Responses 場景）— 對使用者觀感是退步
- Phase 2 接上 reasoning 才算「完整 provider 化」交付
- 兩階段都動同一個 mapper，分 PR 會 conflict

如果工作量太大需要 review-friendly 拆分，可拆兩個 commit（Phase 1 commit / Phase 2 commit），同一個 PR 一次合。

## 12. Out of Scope（後續可考慮）

- Reasoning content 的 token usage 拆分顯示
- Reasoning 折疊偏好持久化（user setting）
- Reasoning 引用 / cite 的 inline link
- 從 reasoning 抽取 tool-call rationale 給 ToolCard
- Provider-specific config UI（thinking budget、reasoning effort）
- Judge model whitelist 驗證（`design_reference.md` §8.3）
- 多 vendor 同時並存 — 同一 deployment 中 v1 跑 Gemini、v2 跑 Anthropic 之類的 mix
- Vertex AI 認證路徑（目前只走 Gemini Developer API）

## 13. References

### LangChain Docs

- Standard content blocks: `oss/python/langchain/messages.mdx`
- Reasoning streaming: `oss/python/langchain/streaming.mdx#streaming-thinking-/-reasoning-tokens`
- Frontend reasoning UX: `oss/python/langchain/frontend/reasoning-tokens.mdx`
- `init_chat_model` provider prefix: `oss/python/concepts/providers-and-models.mdx`
- LangChain Google GenAI integration: `langchain-google-genai` (package, `ChatGoogleGenerativeAI`)

### Wire Format

- AI SDK v6 native event types: `text-start` / `text-delta` / `text-end` / `reasoning-start` / `reasoning-delta` / `reasoning-end`

### 本專案相關

- Streaming 既有架構：`backend/agent_engine/streaming/{event_mapper,sse_serializer,domain_events_schema}.py`
- Streaming 觀測性指引：`backend/agent_engine/docs/streaming_observability_guardrails.md`
- 過去設計文件中關於 judge whitelist / cross-vendor 的 design intent：`artifacts/current/design_reference.md` §8.3、§1（Cross-vendor judge recommended）

### Provider API

- Gemini Developer API: <https://aistudio.google.com/apikey>
- OpenAI Models: <https://platform.openai.com/docs/models>
- Anthropic Models: <https://docs.anthropic.com/en/docs/about-claude/models>
