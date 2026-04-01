# S3 Streaming Chat UI — Design Document

> S3 subsystem design。定義前端 streaming chat UI 的 component 職責、行為規格、視覺設計、與介面契約。
> 供 `implementation-planning` skill 作為輸入。

---

## 背景

FinLab-X V1 streaming chat 採 subsystem-first 分解：

| Subsystem | 職責 | 依賴 |
|---|---|---|
| **S1** Backend Streaming | `Orchestrator.astream()` + FastAPI SSE endpoint | — |
| **S2** Frontend Scaffold | 前端專案基礎建設、tooling、boilerplate tests | — |
| **S3** Streaming Chat UI（本文件） | `useChat` 整合、ChatInterface、message rendering | S1 + S2 |

### 上游依賴

- **S1** 提供 `POST /api/v1/chat/stream`，輸出符合 AI SDK UIMessage Stream Protocol v1 的 SSE
- **S2** 提供 Vite + React + TS + Tailwind v4 + shadcn/ui + `ai` + `@ai-sdk/react` + Vitest + Playwright
- **Master Design** 定義介面契約（Event Taxonomy、Lifecycle Rules、Error Classification）

---

## Scope

### S3 包含

1. `useChat` hook 整合 + `DefaultChatTransport` 配置
2. Chat panel UI（MessageList、ChatInput、ChatHeader）
3. Assistant message parts-based rendering（text + tool cards）
4. Tool card component（inline collapsible，AI SDK states + transient progress overlay）
5. Transient tool progress state 管理（`data-tool-progress`）
6. Custom tool error 處理（`data-tool-error`，透過 `onData` callback）
7. Markdown rendering（`react-markdown` + `remark-gfm`）
8. Smart auto-scroll
9. Stream-level error UI（inline error block + Retry）
10. Clear Session 功能
11. Dark/Light mode（跟隨系統 preference）
12. Cool Slate 配色

### S3 不包含

- Chat history list / sidebar
- 不同 tool 的差異化 UI（V1 統一文字呈現）
- Syntax highlighting for code blocks（V2+）
- Generative UI（V2+）
- 任何 backend 變更（S1 scope）

---

## 設計決策

| # | 決策 | 選擇 | 理由 |
|---|---|---|---|
| D1 | Scope boundary | Chat Panel Only + Clear Session button | V1 快速交付，不需 sidebar / chat history list |
| D2 | Markdown rendering | `react-markdown` + `remark-gfm` | React 生態事實標準，安全（無 `dangerouslySetInnerHTML`），`components` prop 可自訂元素 render |
| D3 | Tool card UX | Inline Collapsible | 預設收合不打斷閱讀流，點擊展開看 detail |
| D4 | Auto-scroll | Smart auto-scroll | 在底部自動捲、往上捲停止、顯示 Scroll to bottom button |
| D5 | Stream-level error UI | Inline error block + Retry button | 放在訊息流中有 context，Retry 位置直覺 |
| D6 | Session ID 管理 | `useState(chatId)` + 傳入 `useChat({ id: chatId })` | Clear Session 時換新 id → `useChat` 切換到新的空對話 |
| D7 | Dark/Light mode | 跟隨系統 preference | shadcn/ui 原生支援，不提供手動 toggle |
| D8 | 配色 | Cool Slate（Yahoo Finance 系） | 金融 dashboard 慣例，深色護眼，詳見配色系統章節 |
| D9 | Tool error 處理 | `onData` callback 處理 `data-tool-error` custom event | S1 驗證 AI SDK v5 無標準 `tool-error` type，改用 `data-*` namespace。S3 透過 `onData` 接收，非 AI SDK 原生消費 |
| D10 | Stream error 時的 pending tool cards | Terminated 狀態（灰化），不是 error 狀態（紅色） | Tool 本身沒有 error，只是被 stream 終止連帶取消。用灰色區分「tool 自身失敗」與「被 stream 中斷」，避免錯誤歸因混淆（S1 DD-05） |
| D11 | State management | `useChat` + local `useState`（chatId, toolProgressMap, toolErrorMap） | 不需要 Redux/Zustand。`toolErrorMap` 管理 `data-tool-error` custom events |

---

## 配色系統

參考 Yahoo Finance dark mode、Stripe fintech palette、金融 dashboard best practice。

### Dark Mode（Cool Slate）

| Token | Hex | 用途 |
|---|---|---|
| `--background` | `#101518` | 頁面背景 |
| `--surface` | `#1a1f25` | Card、tool card、input 背景 |
| `--surface-elevated` | `#252b33` | User bubble、hover 狀態 |
| `--border` | `rgba(255,255,255,0.06)` | 分隔線、card 邊框 |
| `--text-primary` | `#eef1f4` | 主要文字 |
| `--text-secondary` | `#c8cdd3` | Assistant 回覆文字 |
| `--text-muted` | `#7c8894` | Tool label、次要資訊 |
| `--text-dim` | `#4a5260` | Placeholder、tool name |
| `--accent` | `#3b8df0` | 連結、Send button、streaming cursor |
| `--success` | `#21d87d` | Tool 成功 |
| `--warning` | `#f0a030` | Tool 執行中 |
| `--error` | `#fc7a6e` | Tool 失敗、error block |
| `--terminated` | `#6b7280` | Tool 被 stream 中斷（灰化） |

### Light Mode

由 shadcn/ui CSS variables 系統自動適配，implementation 階段根據 neutral base 微調。

### Typography

- 主字體：`Inter`（fallback：`-apple-system, system-ui, sans-serif`）
- Code/Tool：`JetBrains Mono`（fallback：`monospace`）

---

## Component Architecture

```
App
└── ChatPanel                    ← 頂層容器，管 useChat + local state
    ├── ChatHeader
    │   ├── Brand ("FinLab-X" + "v1" tag)
    │   └── ClearSessionButton
    ├── MessageList
    │   ├── UserMessage          ← 純文字
    │   ├── AssistantMessage     ← parts-based rendering
    │   │   ├── TextPart         → react-markdown
    │   │   └── ToolCard         → inline collapsible
    │   ├── StreamErrorBlock     → inline error + Retry
    │   └── ScrollToBottomButton
    └── ChatInput
        ├── TextArea (auto-resize)
        ├── SendButton (status=ready)
        └── StopButton (status=streaming|submitted)
```

### Component 職責

| Component | 職責 | 不負責 |
|---|---|---|
| **ChatPanel** | 持有 `useChat`、管理 `chatId` / `toolProgressMap` / `toolErrorMap` state、傳遞 props 給子 components | 不知道 rendering 細節 |
| **MessageList** | 按順序 render messages、管理 auto-scroll | 不知道 message 內部結構 |
| **AssistantMessage** | 遍歷 `message.parts`，dispatch 到 TextPart / ToolCard | 不知道 markdown 如何 render、tool card 內部狀態 |
| **ToolCard** | 根據 AI SDK tool part state + transient progress/error 顯示對應 UI | 不知道 SSE 事件如何到達 |
| **ChatInput** | 使用者輸入 + Send/Stop 操作 | 不管 message 送出後的流程 |
| **StreamErrorBlock** | 顯示 stream-level error + Retry button | 不處理 tool-level error |

---

## 行為規格

### Tool Card 狀態

Tool card 有 5 種視覺狀態，由 AI SDK tool part state + transient events 組合決定：

| 狀態 | 觸發條件 | 視覺表現 |
|---|---|---|
| **Executing** | `part.state === 'input-available'`，無 progress | Amber dot +「正在執行...」 |
| **Executing + Progress** | `part.state === 'input-available'` + `data-tool-progress` 有 entry | Amber dot + progress message（如「查詢 2330.TW 股價...」） |
| **Success** | `part.state === 'output-available'` | Green dot + 摘要。展開顯示 input / output |
| **Error** | 收到 `data-tool-error` custom event（透過 `onData`） | Red dot +「查詢失敗」+ error message（已由 S1 sanitize，可直接顯示）。展開顯示 input / error detail |
| **Terminated** | Stream error 發生時，tool 仍在 `input-available` → S3 主動標記 | Grey dot +「已中斷」。不顯示 error detail（error 在 StreamErrorBlock） |

> **Note**: `input-streaming` state 在 V1 不會出現（不支援 tool input streaming）。防禦性處理：同 `input-available`。

> **Note**: `data-tool-error` 透過 `onData` callback 接收，不由 AI SDK 原生解析。S3 需自行維護 `toolErrorMap`，將 `toolCallId` 對應到 error message。

### Tool Progress（transient state）

`data-tool-progress` 是 transient event（AI SDK 不存入 `message.parts`），S3 需獨立管理一個 `toolProgressMap`：

- 收到 `data-tool-progress` → 以 `toolCallId` 為 key 存入 progress message
- Tool part 轉為 `output-available` 或收到 `data-tool-error` → 刪除對應 entry
- Clear Session → 清空整個 map

### Error Paths

| 場景 | 觸發 | UI 行為 | Stream |
|---|---|---|---|
| Tool-level error | `data-tool-error` custom event（透過 `onData`） | ToolCard red dot +「查詢失敗」+ sanitized error message | 繼續 |
| Stream-level error | SSE `error` event | Inline StreamErrorBlock + Retry button，部分文字保留 | 結束 |
| Stream error + pending tools | Stream error 發生時有 tool 仍在 executing | Pending tool cards → terminated（灰化），StreamErrorBlock 顯示在下方 | 結束 |
| Concurrent 409 | 同 session 並發 request → HTTP 409 | 顯示 inline error（「對話正在進行中」），不影響進行中的 stream | — |

### Auto-scroll 規則

1. 使用者在底部 → 新內容到達時自動捲到底部
2. 使用者往上捲 → 停止 auto-scroll
3. 停止時顯示「Scroll to bottom」按鈕
4. 點擊按鈕或手動捲回底部 → 恢復 auto-scroll

### Chat Actions

| Action | 觸發 | 行為 |
|---|---|---|
| **Send** | Send button 或 Enter | 送出訊息，status → submitted |
| **Stop** | Stop button（streaming 中） | 中斷 streaming，已生成文字保留 |
| **Retry** | StreamErrorBlock 的 Retry button | 重新生成最後回覆（`regenerate()`） |
| **Clear Session** | Header 的 Clear button | 換新 chatId → messages 清空，session 重新開始 |

### 視覺參考

完整的 state-by-state wireframe 存於 `.artifacts/current/S3_state_storyboard.html`，layout wireframe 存於 `.artifacts/current/S3_layout_wireframe.html`。可在瀏覽器中開啟對照。

---

## 介面契約

### S1 → S3

- **Endpoint**: `POST /api/v1/chat/stream`
- **Response header**: `x-vercel-ai-ui-message-stream: v1`

**Request body（新訊息）**:
```json
{ "message": "<plain_text_string>", "id": "<chat_session_id>" }
```
- `message`：純文字 string。S3 的 `prepareSendMessagesRequest` 負責從 UIMessage 提取 text content
- `id`：chat session ID，**必填**（空字串不接受，S1 回 422）

**Request body（Regenerate）**:
```json
{ "id": "<chat_session_id>", "trigger": "regenerate", "messageId": "<msg_id>" }
```
- `messageId` 必須匹配最後一筆 assistant message，否則 S1 回 422

> **Note**: Send 和 Retry 是互斥的 UI path，S3 不會產生同時含 `message` 和 `trigger` 的 request。

**Event taxonomy**（完整定義見 master design，以下為 S3 需特別處理的部分）：

| SSE `type` | 類別 | S3 處理方式 |
|---|---|---|
| `start` | 標準 | 含 `sessionId` confirmation echo。AI SDK 原生處理 |
| `text-*` / `tool-call-*` / `tool-result` | 標準 | AI SDK 原生處理，自動更新 `message.parts` |
| `data-tool-error` | **Custom** | 透過 `onData` callback 接收，寫入 `toolErrorMap` |
| `data-tool-progress` | **Custom** | 透過 `onData` callback 接收，寫入 `toolProgressMap`（transient） |
| `error` | 標準 | AI SDK 原生處理，`status` 變為 `"error"`。S3 額外清理 pending tool cards → terminated |
| `finish` | 標準 | AI SDK 原生處理。`usage` 格式為 `{"inputTokens": N, "outputTokens": N}`，V1 S3 不消費此欄位 |

**HTTP error responses**:

| Status | 場景 | S3 處理 |
|---|---|---|
| 409 Conflict | 同 session 並發 request | 顯示 inline error「對話正在進行中」 |
| 422 Unprocessable | `id` 為空 / regenerate `messageId` 不匹配 | 顯示 error feedback |

**V1 限制**：後端重啟後對話歷史消失（`InMemorySaver`）。使用者繼續在同 session 送訊息會靜默開始新對話，不會收到 error。此為 S1 DD-06 accepted behavior。

### S2 → S3

- Vite + React + TypeScript 專案已初始化
- `ai` + `@ai-sdk/react` 已安裝
- Tailwind CSS v4 + shadcn/ui 可用
- Vitest + RTL + Playwright test 基礎設施可用
- `@/` path alias 可用

### API Base URL

S3 透過 `import.meta.env.VITE_API_BASE_URL` 環境變數配置 API base URL。開發環境預設為空字串（使用 Vite proxy 或同 origin），production 部署時設定實際 URL。

### 新增 Production Dependencies

| Package | 用途 |
|---|---|
| `react-markdown` | Markdown rendering |
| `remark-gfm` | GFM 支援（tables, strikethrough, autolinks） |

---

## 驗收標準

| # | 條件 |
|---|---|
| AC-1 | `useChat` 正確消費 SSE，文字逐字顯示，streaming cursor 可見 |
| AC-2 | Tool card 根據 5 種狀態正確切換視覺表現（executing / progress / success / error / terminated） |
| AC-3 | `data-tool-progress` transient event 驅動 tool card 即時進度更新 |
| AC-4 | `data-tool-error` custom event 正確顯示 tool-level error（sanitized message），stream 繼續 |
| AC-5 | Stream-level error 顯示 inline error block + Retry，pending tools 灰化為 terminated |
| AC-6 | Send / Stop / Retry / Clear Session 四個 action 行為正確 |
| AC-7 | Smart auto-scroll 運作正常（在底部自動捲、往上停止、Scroll to bottom 按鈕） |
| AC-8 | Markdown 正確渲染（bold、list、table、GFM link `target="_blank"`） |
| AC-9 | Dark/Light mode 跟隨系統 preference 自動切換 |
| AC-10 | Cool Slate 配色正確套用 |
| AC-11 | 409 Conflict 正確顯示 inline error |

---

## Must NOT Have（範圍護欄）

- Chat history list / sidebar / session 管理 UI
- 不同 tool 的差異化 UI
- Code syntax highlighting
- Generative UI components
- Backend 變更
- Message persistence（由 S1 conversation store 處理）
- User authentication
