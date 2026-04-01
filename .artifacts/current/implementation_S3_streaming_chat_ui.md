# Implementation Plan: S3 Streaming Chat UI

> 設計參考：[`design_S3_streaming_chat_ui.md`](./design_S3_streaming_chat_ui.md)
> 視覺參考：[`S3_layout_wireframe.html`](./S3_layout_wireframe.html)、[`S3_state_storyboard.html`](./S3_state_storyboard.html)
> 上層規範：[`design_master.md`](./design_master.md)

**目標：** 實作 streaming chat UI，透過 AI SDK v5 `useChat` 消費 S1 的 SSE endpoint，以 parts-based rendering 呈現文字與 tool cards，提供 Cool Slate 主題的完整聊天體驗。

**架構與關鍵決策：** S3 是純前端子系統。所有 state 由 `useChat` hook + 兩個 `useState`（`chatId`、`toolProgressMap`）管理。`DefaultChatTransport` 搭配自訂 `prepareSendMessagesRequest`，只送最新訊息 + session ID 給後端（DR-06）。Tool progress 是 transient（`data-tool-progress` 透過 `onData` callback），獨立於 AI SDK message history 管理。Dark/Light mode 跟隨系統 preference，不提供手動切換。

**技術棧：** React 19 · TypeScript · AI SDK v5（`ai`、`@ai-sdk/react`）· Tailwind CSS v4 · shadcn/ui · `react-markdown` · `remark-gfm` · Vitest + RTL · Playwright

---

## 依賴驗證

| 依賴 | 版本 | 來源 | 驗證內容 | 備註 |
| --- | --- | --- | --- | --- |
| `ai` | v5 (latest) | Context7 `/websites/ai-sdk_dev` | `DefaultChatTransport`、`prepareSendMessagesRequest` API 形式、`UIMessage` type | 送訊息用 `sendMessage({ text })`，不是 `append()` |
| `@ai-sdk/react` | v5 (latest) | Context7 `/websites/ai-sdk_dev` | `useChat` 回傳 `{ messages, status, error, sendMessage, stop, regenerate }`。`status` 值：`submitted` / `streaming` / `ready` / `error`。`onData` callback 接收 transient data parts。Tool part states：`input-streaming` / `input-available` / `output-available` / `output-error`。Tool part type 是 `tool-{toolName}`，用 `part.type.startsWith('tool-')` 匹配。Error text 透過 `part.errorText` 存取 | `regenerate()` 用於 retry |
| `react-markdown` | latest | Context7 `/remarkjs/react-markdown` | 預設匯出 `Markdown`，`remarkPlugins` prop，`components` prop 自訂元素 render。`components.a` 接收 `href`、`children`、`node` props | 無 `dangerouslySetInnerHTML` |
| `remark-gfm` | latest | Context7 `/remarkjs/react-markdown` | 支援 tables、strikethrough、autolinks、tasklists。用法：`remarkPlugins={[remarkGfm]}` | — |
| `lucide-react` | latest | S2 已安裝 | `ChevronRight`、`ChevronDown`、`ArrowDown`、`Send`、`Square`、`Trash2` icons | — |

## 限制條件

- S2 scaffold 必須完成後才能開始 S3（Vite + React + TS + Tailwind v4 + shadcn/ui + AI SDK + Vitest + Playwright 全部可用）
- 不修改任何後端程式碼 — S3 原樣消費 S1 的 `POST /api/v1/chat/stream`
- 不做 chat history sidebar、不做 per-tool 差異化 UI、不做 syntax highlighting、不做 generative UI
- V1 不支援 tool input streaming — `input-streaming` state 防禦性處理為 `input-available`
- Sources 是 inline markdown links，由 `react-markdown` 渲染，不是獨立結構化區塊

---

## 檔案規劃

| 操作 | 路徑 | 用途 |
| --- | --- | --- |
| 更新 | `frontend/package.json` | 新增 `react-markdown`、`remark-gfm` |
| 更新 | `frontend/src/index.css` | Cool Slate CSS 變數、dark/light mode、字型 |
| 新增 | `frontend/src/hooks/use-auto-scroll.ts` | Smart auto-scroll 邏輯 |
| 新增 | `frontend/src/hooks/use-auto-scroll.test.ts` | Auto-scroll 單元測試 |
| 新增 | `frontend/src/hooks/use-tool-progress.ts` | Transient tool progress state 管理 |
| 新增 | `frontend/src/hooks/use-tool-progress.test.ts` | Tool progress 單元測試 |
| 新增 | `frontend/src/lib/markdown-components.tsx` | `react-markdown` 自訂 component overrides |
| 新增 | `frontend/src/components/ui/text-part.tsx` | Markdown 文字渲染 + streaming cursor |
| 新增 | `frontend/src/components/ui/text-part.test.tsx` | 文字渲染單元測試 |
| 新增 | `frontend/src/components/ui/tool-card.tsx` | Inline collapsible tool card（所有 states） |
| 新增 | `frontend/src/components/ui/tool-card.test.tsx` | Tool card states + 展開/收合測試 |
| 新增 | `frontend/src/components/ui/user-message.tsx` | User 訊息泡泡 |
| 新增 | `frontend/src/components/ui/assistant-message.tsx` | Parts-based assistant 訊息渲染 |
| 新增 | `frontend/src/components/ui/stream-error-block.tsx` | Inline error block + Retry 按鈕 |
| 新增 | `frontend/src/components/ui/message-list.tsx` | 可捲動訊息列表容器 |
| 新增 | `frontend/src/components/ui/message-list.test.tsx` | 訊息渲染 + error states 測試 |
| 新增 | `frontend/src/components/ui/scroll-to-bottom.tsx` | 條件式 scroll-to-bottom 按鈕 |
| 新增 | `frontend/src/components/ui/chat-input.tsx` | 自動調整高度的 textarea + Send/Stop 按鈕 |
| 新增 | `frontend/src/components/ui/chat-input.test.tsx` | 輸入狀態、送出、停止測試 |
| 新增 | `frontend/src/components/ui/chat-header.tsx` | 品牌文字 + 清除對話按鈕 |
| 新增 | `frontend/src/components/ui/chat-header.test.tsx` | 清除對話測試 |
| 新增 | `frontend/src/components/ui/chat-panel.tsx` | 頂層容器：`useChat` + state + layout |
| 新增 | `frontend/src/components/ui/chat-panel.test.tsx` | ChatPanel 整合測試 |
| 更新 | `frontend/src/App.tsx` | 替換 placeholder 為 `ChatPanel` |
| 新增 | `frontend/e2e/fixtures/sse-sequences.ts` | 預錄的 SSE event sequences（E2E mock 用） |
| 新增 | `frontend/e2e/chat-happy-path.spec.ts` | E2E：happy path streaming 流程 |
| 新增 | `frontend/e2e/chat-error.spec.ts` | E2E：tool-level + stream-level error + retry |
| 新增 | `frontend/e2e/chat-actions.spec.ts` | E2E：clear session、stop、auto-scroll |
| 新增 | `frontend/e2e/chat-theme.spec.ts` | E2E：dark/light mode + Cool Slate 配色 |

**結構概覽：**

```text
frontend/src/
├── components/
│   └── ui/
│       ├── chat-panel.tsx          ← 頂層：useChat + state
│       ├── chat-panel.test.tsx
│       ├── chat-header.tsx         ← header bar + 清除對話
│       ├── chat-header.test.tsx
│       ├── message-list.tsx        ← 可捲動訊息容器
│       ├── message-list.test.tsx
│       ├── user-message.tsx        ← user 泡泡
│       ├── assistant-message.tsx   ← parts-based 渲染
│       ├── text-part.tsx           ← react-markdown wrapper
│       ├── text-part.test.tsx
│       ├── tool-card.tsx           ← collapsible tool card
│       ├── tool-card.test.tsx
│       ├── stream-error-block.tsx  ← error block + retry
│       ├── chat-input.tsx          ← textarea + send/stop
│       ├── chat-input.test.tsx
│       └── scroll-to-bottom.tsx    ← 條件式 scroll 按鈕
├── hooks/
│   ├── use-auto-scroll.ts
│   ├── use-auto-scroll.test.ts
│   ├── use-tool-progress.ts
│   └── use-tool-progress.test.ts
└── lib/
    └── markdown-components.tsx

frontend/e2e/
├── fixtures/
│   └── sse-sequences.ts           ← 預錄 SSE payloads
├── chat-happy-path.spec.ts
├── chat-error.spec.ts
├── chat-actions.spec.ts
└── chat-theme.spec.ts
```

---

### Task 1：依賴安裝 + 主題 + 字型

**檔案：**

- 更新：`frontend/package.json`
- 更新：`frontend/src/index.css`

**內容與理由：** 安裝兩個新的 production dependencies，並以 CSS custom properties 建立 Cool Slate 配色系統。這必須先完成，因為後續所有 component 都依賴這些 design tokens。Dark/light mode 使用 `prefers-color-scheme` media query。

**實作要點：**

- 安裝：`pnpm add react-markdown remark-gfm`
- 在 `:root` 下加入 light mode 預設色值，在 `@media (prefers-color-scheme: dark)` 下加入 Cool Slate 色值
- 字型使用系統 fallback 為主（效能考量），加入 `font-family` tokens：
  - 主字體：`Inter, -apple-system, system-ui, sans-serif`
  - Code/Tool 字體：`'JetBrains Mono', monospace`
- Cool Slate dark palette（來自設計文件）：`--background: #101518`、`--surface: #1a1f25`、`--surface-elevated: #252b33`、`--border: rgba(255,255,255,0.06)`、`--text-primary: #eef1f4`、`--text-secondary: #c8cdd3`、`--text-muted: #7c8894`、`--text-dim: #4a5260`、`--accent: #3b8df0`、`--success: #21d87d`、`--warning: #f0a030`、`--error: #fc7a6e`

**關鍵定義：**

```css
/* Dark mode（Cool Slate） */
@media (prefers-color-scheme: dark) {
  :root {
    --background: #101518;
    --surface: #1a1f25;
    --surface-elevated: #252b33;
    --border: rgba(255,255,255,0.06);
    --text-primary: #eef1f4;
    --text-secondary: #c8cdd3;
    --text-muted: #7c8894;
    --text-dim: #4a5260;
    --accent: #3b8df0;
    --success: #21d87d;
    --warning: #f0a030;
    --error: #fc7a6e;
  }
}
```

**驗證：**

| 範圍 | 指令 | 預期結果 | 驗證目的 |
| --- | --- | --- | --- |
| 安裝 | `cd frontend && pnpm add react-markdown remark-gfm` | Exit 0，packages 出現在 `node_modules` | 依賴可用 |
| 建置 | `cd frontend && pnpm run build` | Exit 0，無錯誤 | CSS 變數不破壞建置 |
| 型別檢查 | `cd frontend && pnpm exec tsc --noEmit` | Exit 0 | TypeScript 仍可編譯 |

**執行清單：**

- [ ] 安裝 `react-markdown` 和 `remark-gfm`
- [ ] 在 `frontend/src/index.css` 加入 Cool Slate CSS custom properties（含 light/dark 兩組）
- [ ] 加入 font-family tokens（Inter 主字體、JetBrains Mono code 字體）
- [ ] 確認建置通過
- [ ] Commit：`feat(S3): add dependencies and Cool Slate theme tokens`

---

### Task 2：自訂 Hooks — useAutoScroll + useToolProgress

**檔案：**

- 新增：`frontend/src/hooks/use-auto-scroll.ts`
- 新增：`frontend/src/hooks/use-auto-scroll.test.ts`
- 新增：`frontend/src/hooks/use-tool-progress.ts`
- 新增：`frontend/src/hooks/use-tool-progress.test.ts`

**內容與理由：** 這兩個 hooks 封裝多個 component 都會用到的可重用邏輯。在 UI component 之前先獨立建構與測試，確保基礎穩固。

**實作要點：**

`useAutoScroll(containerRef)`:
- 回傳 `{ isAtBottom: boolean, scrollToBottom: () => void }`
- 使用 scroll event listener：`scrollHeight - scrollTop - clientHeight < threshold`（threshold ≈ 50px）
- `scrollToBottom()` 呼叫 `containerRef.current.scrollTo({ top: scrollHeight, behavior: 'smooth' })`
- 在 scroll 事件和內容變化時更新 `isAtBottom`
- 當 `isAtBottom` 為 true 且內容增長，自動 scroll 到底部

`useToolProgress()`:
- 回傳 `{ toolProgressMap: Map<string, string>, onData: (dataPart) => void, clearProgress: () => void }`
- `onData` callback：收到 `dataPart.type === 'data-tool-progress'` 時，`toolProgressMap.set(dataPart.toolCallId, dataPart.data.message)`
- `clearProgress()`：清空整個 map（Clear Session 時使用）
- 清理時機：tool part 從 `input-available` 轉為 `output-available` / `output-error` 時，渲染端不再讀取 map entry（entry 自然失效）

**測試策略：**

`use-auto-scroll.test.ts`（AC-U12）：
- 在底部時 → `isAtBottom` 為 true
- 往上捲 → `isAtBottom` 為 false
- `scrollToBottom()` 呼叫 `scrollTo` 帶正確參數

`use-tool-progress.test.ts`（AC-U4）：
- `onData` 收到 `data-tool-progress` event → map entry 建立，message 正確
- `onData` 收到非 tool-progress event → map 不變
- `clearProgress()` → map 清空
- 多個不同 `toolCallId` 的 progress events → map 包含所有 entries

**驗證：**

| 範圍 | 指令 | 預期結果 | 驗證目的 |
| --- | --- | --- | --- |
| 單元測試 | `cd frontend && pnpm exec vitest run src/hooks/` | 所有測試通過 | Hooks 獨立運作正確 |
| 型別檢查 | `cd frontend && pnpm exec tsc --noEmit` | Exit 0 | 無型別錯誤 |

**執行清單：**

- [ ] 🔴 撰寫 `useAutoScroll` 的 test cases
- [ ] 🔴 執行測試，確認全部失敗（RED）
- [ ] 🟢 實作 `useAutoScroll` 使測試通過（GREEN）
- [ ] 🔵 審視實作，必要時 refactor
- [ ] 🔵 再次執行測試，確認 refactor 後仍通過
- [ ] 🔴 撰寫 `useToolProgress` 的 test cases
- [ ] 🔴 執行測試，確認全部失敗（RED）
- [ ] 🟢 實作 `useToolProgress` 使測試通過（GREEN）
- [ ] 🔵 審視實作，必要時 refactor
- [ ] 🔵 再次執行所有 hook 測試，確認全部通過
- [ ] Commit：`feat(S3): add useAutoScroll and useToolProgress hooks`

---

### Task 3：葉節點渲染 — TextPart + ToolCard

**檔案：**

- 新增：`frontend/src/lib/markdown-components.tsx`
- 新增：`frontend/src/components/ui/text-part.tsx`
- 新增：`frontend/src/components/ui/text-part.test.tsx`
- 新增：`frontend/src/components/ui/tool-card.tsx`
- 新增：`frontend/src/components/ui/tool-card.test.tsx`

**內容與理由：** 這是 assistant 訊息內部的兩個葉節點 rendering component。TextPart 封裝 `react-markdown`；ToolCard 處理所有 tool 狀態。在組合進 AssistantMessage 之前先獨立測試。

**實作要點：**

`markdown-components.tsx`：
- 匯出 `components` 物件供 `react-markdown` 使用
- 覆寫 `a`：加入 `target="_blank"` + `rel="noopener noreferrer"`
- V1 不覆寫其他元素

`text-part.tsx`：
- Props：`{ text: string, isStreaming: boolean }`
- 渲染 `<Markdown remarkPlugins={[remarkGfm]} components={markdownComponents}>{text}</Markdown>`
- `isStreaming` 時在 markdown 內容後附加閃爍 cursor `<span>`
- Cursor 使用 `--accent` 顏色，CSS `@keyframes blink`

`tool-card.tsx`：
- Props：`{ part: ToolInvocationPart, progress?: string, dimmed?: boolean }`
- 可收合 card，click 切換 detail 區塊
- `dimmed` prop 用於 ERROR 2b 場景：stream error 中斷時，仍在 `input-available` 的 tool card 視覺灰化（`opacity: 0.5`，停止脈衝動畫）
- 狀態渲染（對應 storyboard States 3–5 及 ERROR 1–1b、ERROR 2b）：

| `part.state` | `dimmed` | Dot 顏色 | Label | Detail |
| --- | --- | --- | --- | --- |
| `input-streaming` / `input-available`（無 progress） | false | amber（`--warning`）脈衝動畫 | 「正在執行...」 | — |
| `input-available` + `progress` 字串 | false | amber（`--warning`）脈衝動畫 | progress message | — |
| `input-available`（stream 已中斷） | true | grey（`--text-muted`）無動畫 | progress message 或「正在執行...」 | — |
| `output-available` | — | green（`--success`） | 「已完成」 | 可展開：INPUT（JSON）+ OUTPUT（JSON） |
| `output-error` | — | red（`--error`） | 「執行失敗」+ `part.errorText` | 可展開：INPUT（JSON）+ ERROR detail |

- Tool name 顯示在最右側，monospace 字體（`--text-dim`）
- Chevron icon：`ChevronRight`（收合）/ `ChevronDown`（展開）
- 本地 `useState<boolean>(false)` 管理展開狀態

**測試策略：**

`text-part.test.tsx`（AC-U11）：
- 渲染粗體（`**bold**` → `<strong>`）
- 渲染列表項目
- 渲染表格（GFM）
- 渲染連結帶 `target="_blank"` 和 `rel="noopener noreferrer"`
- `isStreaming=true` 時 cursor 可見，`false` 時隱藏

`tool-card.test.tsx`（AC-U2、AC-U3）：
- `input-available` state → amber dot + 「正在執行...」label
- `input-available` + progress → amber dot + progress message 文字
- `output-available` state → green dot + 「已完成」label
- `output-error` state → red dot + 「執行失敗」+ error 文字
- `dimmed=true` → grey dot、無脈衝動畫、整體 `opacity: 0.5`
- 點擊 card → detail 區塊出現（INPUT/OUTPUT 可見）
- 再次點擊 → detail 區塊收合
- Tool name 顯示在 card 中

**驗證：**

| 範圍 | 指令 | 預期結果 | 驗證目的 |
| --- | --- | --- | --- |
| 單元測試 | `cd frontend && pnpm exec vitest run src/components/ui/text-part.test.tsx src/components/ui/tool-card.test.tsx` | 所有測試通過 | 葉節點 component 渲染正確 |
| 型別檢查 | `cd frontend && pnpm exec tsc --noEmit` | Exit 0 | 無型別錯誤 |

**執行清單：**

- [ ] 建立 `markdown-components.tsx` 的 link override
- [ ] 🔴 撰寫 `TextPart` 的 test cases（markdown 渲染 + cursor）
- [ ] 🔴 執行測試，確認全部失敗（RED）
- [ ] 🟢 實作 `text-part.tsx` 使測試通過（GREEN）
- [ ] 🔵 審視實作，必要時 refactor
- [ ] 🔵 再次執行測試，確認 refactor 後仍通過
- [ ] 🔴 撰寫 `ToolCard` 的 test cases（所有 states + 展開/收合）
- [ ] 🔴 執行測試，確認全部失敗（RED）
- [ ] 🟢 實作 `tool-card.tsx` 使測試通過（GREEN）
- [ ] 🔵 審視實作，必要時 refactor
- [ ] 🔵 再次執行所有測試，確認全部通過
- [ ] Commit：`feat(S3): add TextPart and ToolCard components`

---

### Task 4：訊息組件 — UserMessage + AssistantMessage + StreamErrorBlock + MessageList

**檔案：**

- 新增：`frontend/src/components/ui/user-message.tsx`
- 新增：`frontend/src/components/ui/assistant-message.tsx`
- 新增：`frontend/src/components/ui/stream-error-block.tsx`
- 新增：`frontend/src/components/ui/scroll-to-bottom.tsx`
- 新增：`frontend/src/components/ui/message-list.tsx`
- 新增：`frontend/src/components/ui/message-list.test.tsx`

**內容與理由：** 將葉節點 renderer 組合成訊息流。MessageList 是可捲動的容器，按順序渲染所有訊息。StreamErrorBlock 處理 stream-level error 的 UI 與 Retry。測試聚焦在正確的訊息排序、角色分類渲染、和 error UI。

**實作要點：**

`user-message.tsx`：
- Props：`{ message: UIMessage }`
- 渲染靠右對齊的 user 泡泡，`--surface-elevated` 背景
- 從 `message.parts.find(p => p.type === 'text')?.text` 取得文字
- 樣式參考 wireframe：`border-radius: 16px 16px 4px 16px`，gradient 背景

`assistant-message.tsx`：
- Props：`{ message: UIMessage, toolProgressMap: Map<string, string>, isStreaming: boolean, isError: boolean }`
- 遍歷 `message.parts.map()`：
  - `part.type === 'text'` → `<TextPart text={part.text} isStreaming={isLastTextPart && isStreaming} />`
  - `part.type.startsWith('tool-')` → `<ToolCard part={part} progress={toolProgressMap.get(part.toolCallId)} dimmed={isError && part.state === 'input-available'} />`
- `isError` 為 true 且 tool part 仍在 `input-available` 時，傳 `dimmed=true`（ERROR 2b 場景）
- Streaming cursor 只出現在最後一個 text part

`stream-error-block.tsx`：
- Props：`{ error: Error, onRetry: () => void }`
- 渲染 error icon（!）+ 「回覆中斷」標題 + error message + Retry 按鈕
- 樣式參考 wireframe：紅色調背景，`--error` 強調色

`scroll-to-bottom.tsx`：
- Props：`{ visible: boolean, onClick: () => void }`
- `visible=true` 時渲染浮動 `ArrowDown` 按鈕
- 定位在訊息列表底部中央

`message-list.tsx`：
- Props：`{ messages: UIMessage[], status: string, error: Error | undefined, toolProgressMap: Map<string, string>, onRetry: () => void }`
- 根據 `message.role` 渲染每個訊息：
  - `user` → `<UserMessage />`
  - `assistant` → `<AssistantMessage isStreaming={isLastAssistant && (status === 'streaming')} isError={isLastAssistant && (status === 'error')} />`
- `isStreaming` 和 `isError` 只傳給最後一個 assistant message（只有最新回覆需要 streaming cursor 或 error 灰化）
- `status === 'submitted'` 且最後訊息為 user → 顯示 loading dots
- `status === 'error'` 且 `error` 存在 → 在最後訊息後顯示 `<StreamErrorBlock />`
- 整合 `useAutoScroll` 管理可捲動容器
- 不在底部時顯示 `<ScrollToBottomButton />`

**測試策略：**

`message-list.test.tsx`（AC-U1、AC-U9）：
- 以正確順序渲染 user 和 assistant messages
- User message 在泡泡中顯示正確文字
- Assistant message 透過 markdown 渲染 text parts
- Assistant message 以 ToolCards 渲染 tool parts
- `status=submitted` → loading dots 在 user message 後可見
- `status=error` → StreamErrorBlock 可見且顯示 error 文字
- Retry 按鈕呼叫 `onRetry`
- 不在底部時 scroll-to-bottom 按鈕出現

**驗證：**

| 範圍 | 指令 | 預期結果 | 驗證目的 |
| --- | --- | --- | --- |
| 單元測試 | `cd frontend && pnpm exec vitest run src/components/ui/message-list.test.tsx` | 所有測試通過 | 訊息流渲染正確 |
| 全部單元測試 | `cd frontend && pnpm exec vitest run` | 所有測試通過 | 無 regression |
| 型別檢查 | `cd frontend && pnpm exec tsc --noEmit` | Exit 0 | 無型別錯誤 |

**執行清單：**

- [ ] 🔴 撰寫 `MessageList` 的 test cases（訊息排序、loading dots、error block、retry）——測試中 import 尚未存在的 sub-components，此時全部 RED
- [ ] 🔴 執行測試，確認全部失敗（RED）
- [ ] 🟢 實作 `user-message.tsx`、`assistant-message.tsx`、`stream-error-block.tsx`、`scroll-to-bottom.tsx`、`message-list.tsx` 使測試通過（GREEN）
- [ ] 🔵 審視實作，必要時 refactor
- [ ] 🔵 再次執行所有單元測試，確認全部通過
- [ ] Commit：`feat(S3): add message components and MessageList`

---

### Task 5：輸入 + Header — ChatInput + ChatHeader

**檔案：**

- 新增：`frontend/src/components/ui/chat-input.tsx`
- 新增：`frontend/src/components/ui/chat-input.test.tsx`
- 新增：`frontend/src/components/ui/chat-header.tsx`
- 新增：`frontend/src/components/ui/chat-header.test.tsx`

**內容與理由：** ChatInput 處理使用者文字輸入，含自動調整高度和 Send/Stop 按鈕切換。ChatHeader 顯示品牌和清除對話。兩者獨立於訊息渲染，可以隔離測試。

**實作要點：**

`chat-input.tsx`：
- Props：`{ status: string, onSend: (text: string) => void, onStop: () => void }`
- 自動調整高度的 `<textarea>`（透過 `scrollHeight` 調整 height）
- `status === 'ready'`：Send 按鈕（accent 藍色），可用。按 Enter（不含 Shift）或點擊按鈕送出
- `status === 'submitted' || status === 'streaming'`：textarea disabled，顯示 Stop 按鈕（方形 icon）取代 Send
- `status === 'error'`：textarea disabled，顯示 Send 按鈕（disabled 狀態）。使用者需透過 error block 的 Retry 按鈕恢復，retry 成功後 `status` 回到 `ready`，input 自然恢復可用
- 送出後清空 textarea
- 輸入區下方免責聲明：「FinLab-X 可能產生不準確的資訊，請自行驗證重要財務數據。」

`chat-header.tsx`：
- Props：`{ onClearSession: () => void }`
- 左側：「FinLab-X」品牌文字 + 「v1」tag badge
- 右側：「清除對話」按鈕（紅色調，參考 wireframe）
- 清除按鈕樣式：`rgba(252,122,110,0.08)` 背景、`--error` 文字/邊框

**測試策略：**

`chat-input.test.tsx`（AC-U5、AC-U6、AC-U7）：
- `status=ready` → textarea 可用、Send 按鈕可見
- `status=streaming` → textarea disabled、Stop 按鈕可見
- 輸入文字 + 點擊 Send → `onSend` 被呼叫且帶正確文字，textarea 清空
- 輸入文字 + 按 Enter → `onSend` 被呼叫（Shift+Enter 不送出）
- 點擊 Stop → `onStop` 被呼叫
- 空輸入 → Send 按鈕 disabled 或 no-op

`chat-header.test.tsx`（AC-U8 部分）：
- 品牌文字「FinLab-X」和「v1」tag 可見
- 點擊「清除對話」→ `onClearSession` 被呼叫

**驗證：**

| 範圍 | 指令 | 預期結果 | 驗證目的 |
| --- | --- | --- | --- |
| 單元測試 | `cd frontend && pnpm exec vitest run src/components/ui/chat-input.test.tsx src/components/ui/chat-header.test.tsx` | 所有測試通過 | 輸入和 header 正確運作 |
| 全部單元測試 | `cd frontend && pnpm exec vitest run` | 所有測試通過 | 無 regression |

**執行清單：**

- [ ] 🔴 撰寫 `ChatInput` 的 test cases（send、stop、disabled states、Enter 鍵）
- [ ] 🔴 執行測試，確認全部失敗（RED）
- [ ] 🟢 實作 `chat-input.tsx` 使測試通過（GREEN）
- [ ] 🔵 審視實作，必要時 refactor
- [ ] 🔵 再次執行測試，確認 refactor 後仍通過
- [ ] 🔴 撰寫 `ChatHeader` 的 test cases（品牌、清除對話）
- [ ] 🔴 執行測試，確認全部失敗（RED）
- [ ] 🟢 實作 `chat-header.tsx` 使測試通過（GREEN）
- [ ] 🔵 審視實作，必要時 refactor
- [ ] 🔵 再次執行所有單元測試，確認全部通過
- [ ] Commit：`feat(S3): add ChatInput and ChatHeader components`

---

### Task 6：ChatPanel 整合 + App.tsx

**檔案：**

- 新增：`frontend/src/components/ui/chat-panel.tsx`
- 新增：`frontend/src/components/ui/chat-panel.test.tsx`
- 更新：`frontend/src/App.tsx`

**內容與理由：** ChatPanel 是頂層容器，連接 `useChat` 與 `DefaultChatTransport`，管理 `chatId` 和 `toolProgressMap`，組合所有子 component。這是整合點。App.tsx 更新為全頁面渲染 ChatPanel。

**實作要點：**

`chat-panel.tsx`：
- 根據設計文件設定 `useChat` 與 `DefaultChatTransport`
- `prepareSendMessagesRequest` 處理兩種 trigger：
  - `submit-user-message` → `{ body: { id, message: messages.at(-1) } }`
  - `regenerate-assistant-message` → `{ body: { id, trigger: 'regenerate', messageId } }`
- `chatId` state：`useState(() => crypto.randomUUID())`
- `useToolProgress()` 管理 transient tool progress
- `handleClearSession()`：新 `chatId` + `clearProgress()`
- 將 `regenerate` 傳給 MessageList 作為 `onRetry`
- 全高 flex layout：ChatHeader（固定）→ MessageList（flex-1 scroll）→ ChatInput（固定）

`App.tsx`：
- 將 placeholder 內容替換為 `<ChatPanel />`
- 全 viewport 高度：`h-screen`，`--background` 背景色

**關鍵定義：**

```tsx
// ChatPanel useChat 接線（DR-06）
const { messages, status, error, sendMessage, stop, regenerate } = useChat({
  id: chatId,
  transport: new DefaultChatTransport({
    api: `${import.meta.env.VITE_API_BASE_URL ?? ''}/api/v1/chat/stream`,
    prepareSendMessagesRequest: ({ id, messages, trigger, messageId }) => {
      if (trigger === 'submit-user-message') {
        return { body: { id, message: messages.at(-1) } };
      }
      if (trigger === 'regenerate-assistant-message') {
        return { body: { id, trigger: 'regenerate', messageId } };
      }
      throw new Error(`Unsupported trigger: ${trigger}`);
    },
  }),
  onError: () => {},
  onData,
});
```

**測試策略：**

`chat-panel.test.tsx`（AC-U8 完整）：
- Mock `@ai-sdk/react` 的 `useChat`，控制 `messages`、`status`、`error`，捕捉 `sendMessage`、`stop`、`regenerate` 呼叫
- 渲染 ChatHeader、MessageList、ChatInput
- 送出訊息 → `sendMessage` 被呼叫且帶 `{ text }`
- 清除對話 → 驗證 mocked `useChat` 收到的 `id` 參數改變（re-render 時傳入新的 `chatId`）、messages 清空
- Error 狀態 → error block 可見、retry 呼叫 `regenerate`
- Stop → `stop` 被呼叫

**驗證：**

| 範圍 | 指令 | 預期結果 | 驗證目的 |
| --- | --- | --- | --- |
| 單元測試 | `cd frontend && pnpm exec vitest run src/components/ui/chat-panel.test.tsx` | 所有測試通過 | 整合接線正確 |
| 全部單元測試 | `cd frontend && pnpm exec vitest run` | 所有測試通過 | 無 regression |
| 建置 | `cd frontend && pnpm run build` | Exit 0 | Production build 成功 |
| Dev server | `cd frontend && pnpm run dev` | Vite 啟動，頁面載入於 localhost:5173 | App 渲染 ChatPanel |

**執行清單：**

- [ ] 🔴 撰寫 `ChatPanel` 的 test cases（mock useChat，測試接線）
- [ ] 🔴 執行測試，確認全部失敗（RED）
- [ ] 🟢 實作 `chat-panel.tsx` 使測試通過（GREEN）
- [ ] 🟢 更新 `App.tsx` 渲染 `<ChatPanel />`
- [ ] 🔵 審視實作，必要時 refactor
- [ ] 🔵 再次執行所有單元測試，確認全部通過
- [ ] 確認建置成功
- [ ] Commit：`feat(S3): add ChatPanel integration and wire App.tsx`

---

### Flow Verification：單元測試套件完成

> Tasks 1–6 完成所有 component 和 hook 的實作與單元測試。
> 所有單元層級的 acceptance criteria（AC-U1 至 AC-U12）應通過。

| # | 方法 | 步驟 | 預期結果 |
| --- | --- | --- | --- |
| 1 | CLI | `cd frontend && pnpm exec vitest run` | 所有單元測試通過（0 failures） |
| 2 | CLI | `cd frontend && pnpm exec tsc --noEmit` | Exit 0，無型別錯誤 |
| 3 | CLI | `cd frontend && pnpm run build` | Exit 0，production build 成功 |
| 4 | Browser | 開啟 `http://localhost:5173`（Vite dev server 運行中） | ChatPanel 渲染：header 含品牌 + 清除按鈕、空的訊息列表、輸入區含 textarea + send 按鈕 |

- [ ] 所有 flow verifications 通過

---

### Task 7：E2E 測試 — Playwright Mock Backend + 全場景

**檔案：**

- 新增：`frontend/e2e/fixtures/sse-sequences.ts`
- 新增：`frontend/e2e/chat-happy-path.spec.ts`
- 新增：`frontend/e2e/chat-error.spec.ts`
- 新增：`frontend/e2e/chat-actions.spec.ts`
- 新增：`frontend/e2e/chat-theme.spec.ts`

**內容與理由：** E2E 測試透過 Playwright 搭配 mocked SSE backend 驗證完整的使用者面向行為。兩個 HTML 視覺參考檔案（`S3_layout_wireframe.html` 和 `S3_state_storyboard.html`）作為 BDD 規格 — 每個 E2E 測試場景對應這兩個檔案中定義的特定 state 和 layout。Playwright `page.route()` 攔截 `/api/v1/chat/stream` 並回傳預錄的 SSE event sequences。

**實作要點：**

`e2e/fixtures/sse-sequences.ts`：
- 匯出輔助函式：`createSSEResponse(events: Array<object>, options?: { delayMs?: number })`，產生含正確 headers（`content-type: text/event-stream`、`x-vercel-ai-ui-message-stream: v1`）的 Playwright route handler
- 預定義 sequences，對應 master design Event Taxonomy：
  - `HAPPY_PATH_EVENTS`：`start` → `text-start/delta/end` → `tool-call-start/end` → `data-tool-progress` → `tool-result` → `text-start/delta/end` → `finish`
  - `TOOL_ERROR_EVENTS`：`start` → `tool-call-start/end` × 2 → `tool-result`（tool 1）→ `tool-error`（tool 2）→ `text-start/delta/end` → `finish`
  - `STREAM_ERROR_EVENTS`：`start` → `text-start/delta` → `error`
  - `STREAM_ERROR_DURING_TOOL_EVENTS`：`start` → `text-start/delta/end` → `tool-call-start/end` → `data-tool-progress` → `error`

`e2e/chat-happy-path.spec.ts`（AC-E1 — 對應 storyboard States 1–7）：
- **BDD 規格參考**：Storyboard `STATE 1` 至 `STATE 7`
- 輸入訊息 → 送出 → loading dots 出現（State 1：`submitted`）
- 文字開始 streaming，帶 cursor（State 2：`streaming` + `text-delta`）
- Tool card 出現，amber dot（State 3：`tool-call-start`）
- Tool card 顯示進度訊息（State 4：`data-tool-progress`）
- Tool card 轉綠色（State 5：`tool-result`）
- 最終文字 streaming（State 6：continuation text + cursor）
- Streaming 完成 → cursor 消失、input 恢復可用（State 7：`ready`）

`e2e/chat-error.spec.ts`（AC-E2、AC-E3）：
- **BDD 規格參考**：Storyboard `ERROR 1`、`ERROR 1b`、`ERROR 2`、`ERROR 2b`
- Tool-level error（ERROR 1）：一個 tool 成功（green dot）、一個失敗（red dot + error 文字），stream 繼續顯示部分資料
- Tool error 展開（ERROR 1b）：點擊失敗的 tool card → detail 顯示 INPUT + ERROR
- Stream-level error（ERROR 2）：部分文字可見 + error block 含「回覆中斷」+ Retry 按鈕
- Tool 執行中 stream error（ERROR 2b）：仍在 `input-available` 的 tool card 灰化（`opacity: 0.5`、dot 變 grey、停止脈衝動畫）+ 下方 error block
- Retry：點擊 Retry → mock 回傳成功 sequence → 訊息完成

`e2e/chat-actions.spec.ts`（AC-E4、AC-E5、AC-E6）：
- **BDD 規格參考**：Storyboard States 1–7（lifecycle）+ layout wireframe（輸入區）
- 清除對話（AC-E4）：完成一段對話 → 點擊「清除對話」→ 訊息消失 → 送新訊息 → 正常運作。注意：`page.route()` 的 mock 跨 request 持續有效，不需重新註冊
- 停止（AC-E5）：開始 streaming → 點擊 Stop → streaming 停止，部分文字保留，input 恢復可用
- Auto-scroll（AC-E6）：送多個訊息填滿 viewport → 自動 scroll 到底部 → 往上捲 → scroll-to-bottom 按鈕出現 → 點擊 → 回到底部

`e2e/chat-theme.spec.ts`（AC-E7、AC-E8）：
- **BDD 規格參考**：Layout wireframe（Cool Slate palette）
- Dark mode（AC-E8）：驗證 body `background-color` 匹配 `#101518`、surface 元素匹配 `#1a1f25`
- Light mode（AC-E7）：emulate `prefers-color-scheme: light` → 驗證 light palette 套用
- Dark/light 切換（AC-E7）：emulate scheme 變更 → 驗證 palette 切換

**驗證：**

| 範圍 | 指令 | 預期結果 | 驗證目的 |
| --- | --- | --- | --- |
| E2E 測試 | `cd frontend && pnpm exec playwright test` | 所有 E2E 測試通過 | 完整使用者面向行為已驗證 |
| E2E 報告 | `cd frontend && pnpm exec playwright show-report` | HTML 報告顯示所有場景通過 | 視覺確認 |

**執行清單：**

- [ ] 建立 `sse-sequences.ts`，含 SSE mock helper 和所有預錄 event sequences
- [ ] 撰寫 `chat-happy-path.spec.ts`，對應 storyboard States 1–7
- [ ] 撰寫 `chat-error.spec.ts`，對應 storyboard ERROR 1、1b、2、2b
- [ ] 撰寫 `chat-actions.spec.ts`，測試清除對話、停止、auto-scroll
- [ ] 撰寫 `chat-theme.spec.ts`，測試 dark/light mode 和 Cool Slate 配色
- [ ] 執行所有 E2E 測試並確認通過
- [ ] Commit：`test(S3): add E2E tests with Playwright mock backend`

---

### Flow Verification：完整 E2E 套件

> Task 7 完成所有 E2E 測試。結合 Tasks 1–6，所有 acceptance criteria（AC-U1–U12、AC-E1–E8）應全部滿足。

| # | 方法 | 步驟 | 預期結果 |
| --- | --- | --- | --- |
| 1 | CLI | `cd frontend && pnpm exec vitest run` | 所有單元測試通過 |
| 2 | CLI | `cd frontend && pnpm exec playwright test` | 所有 E2E 測試通過 |
| 3 | CLI | `cd frontend && pnpm run build` | Production build 成功 |
| 4 | CLI | `cd frontend && pnpm exec tsc --noEmit` | 無型別錯誤 |
| 5 | Browser | 開啟 `http://localhost:5173`，送出訊息（搭配真實 S1 backend 運行） | 完整 streaming 流程端對端運作 |

- [ ] 所有 flow verifications 通過

---

## 交付前檢查清單

### 程式碼層級（TDD）

- [ ] 每個 task 的 targeted verification 通過
- [ ] 所有單元測試通過：`pnpm exec vitest run`
- [ ] 所有 E2E 測試通過：`pnpm exec playwright test`
- [ ] Lint 通過：`pnpm exec eslint .`
- [ ] 型別檢查通過：`pnpm exec tsc --noEmit`
- [ ] 建置成功：`pnpm run build`

### 流程層級（行為驗證）

- [ ] 所有 flow verification 步驟已執行並通過
- [ ] Flow：單元測試套件完成 — PASS / FAIL
- [ ] Flow：完整 E2E 套件 — PASS / FAIL

### 總結

- [ ] 兩個層級都通過 → 準備交付
- [ ] 任何失敗已記錄原因和後續行動
