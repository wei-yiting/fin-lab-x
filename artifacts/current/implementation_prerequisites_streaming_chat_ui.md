# Implementation Prerequisites — S3 Streaming Chat UI

## Meta

- Design Reference: `artifacts/current/design_streaming_chat_ui.md`
- BDD Reference: `artifacts/current/bdd_scenarios_streaming_chat_ui.md`
- Verification Reference: `artifacts/current/verification_plan_streaming_chat_ui.md`
- **Implementation Test Cases Reference**: `artifacts/current/implementation_test_cases_streaming_chat_ui.md` ← TDD/BDD spec source 給 coding agent 邊做邊測
- Generated: 2026-04-08

## 文件目的

這份文件是 **`implementation-planning` skill 的第 4 個輸入**。它記錄 design.md 沒定義、但 implementation plan 必須產出的「**架構契約 / before-implementation prerequisites**」。

跟 `implementation_test_cases` 的角色分工很重要：
- **本文件** = 「**before** implementation」必須先存在的東西（DOM contract、MSW infra、library interfaces、V-checks、smart retry / aborted state architecture）
- **implementation_test_cases** = 「**during** implementation」coding agent 邊做 TDD 邊跑的具體 test cases

| Artifact | 角色 | Coding agent 何時讀 |
|---|---|---|
| `design_streaming_chat_ui.md` | What to build（component breakdown、決策、視覺）| Implementation 開始前 |
| `bdd_scenarios_streaming_chat_ui.md` | Behavior spec（user-observable 行為） | reference（TDD 的 source of truth） |
| **本文件 (`implementation_prerequisites`)** | Architecture contracts（DOM、MSW、libraries 介面） | Milestone 0 / 1 |
| `implementation_test_cases_streaming_chat_ui.md` | TDD test case spec（每個 test 的具體 code） | 寫每個 component / hook / lib 時 |
| `verification_plan_streaming_chat_ui.md` | After-impl verification（real backend + visual + UAT）| Milestone 5 |

三類內容：

1. **Test Surface / DOM Observability Contract** — 每個 component 必須提供的 `data-testid` / `data-status` / `data-tool-state` attribute。BDD selector 跟 production debug 共用的穩定 query layer
2. **Test Infrastructure** — MSW + fixture catalog + Browser-Use CLI 整合機制
3. **Implementation Contracts** — V-1/V-2/V-3 pre-coding contract verifications、smart retry classification、aborted tool state、`lib/error-messages.ts` interface

對齊原則：所有 DOM contract entry 都對應 design.md 的 component breakdown（atomic 6 層）。Coding agent 拿到 design.md + 本文件後，每個 component 的 Props + DOM contract + behavior 已經完整，可以直接寫 code。

---

## Section 1: Test Surface / DOM Observability Contract

### 設計原則

1. **ARIA first, testid second**: interactive elements（button、textarea）一律加 `aria-label` 表達語意（同時服務 a11y）。`data-testid` 補在「ARIA 表達不出」的地方 — status indicator、message container、internal state markers
2. **`data-testid` 永久保留在 production**: 不做 add-then-remove，不用 babel plugin 移除。Bundle size impact ~1KB level，gzip 後可忽略；DOM attribute 不影響 rendered output；勝過維護兩條 build pipeline 的成本
3. **`data-status` / `data-tool-state` 雙用途**: testing query selector + CSS state-driven styling（沿用 shadcn `Collapsible` 既有的 `data-state` pattern）
4. **Naming convention**: kebab-case，prefix 對應 component domain（`composer-`, `tool-card-`, `chat-`, `stream-`）

### Atoms (`components/atoms/`)

| Component | DOM contract | 用途 |
|---|---|---|
| `StatusDot` | `<span data-testid="status-dot" data-status-state="running\|success\|error\|aborted">` | tool / error 視覺狀態 query |
| `RefSup` | `<sup data-testid="ref-sup" data-ref-label={label}><a href={href}>` | 找特定 ref（例如 `[data-ref-label="3"]`） |
| `Cursor` | `<span data-testid="cursor">` | streaming cursor 存在性 |
| `TypingIndicator` | `<div data-testid="typing-indicator">` | thinking dots 存在性 |
| `PromptChip` | `<button data-testid="prompt-chip" data-chip-index={index} aria-label={chipText}>` | chip 點擊測試（透過 index） |
| `RegenerateButton` | `<button data-testid="regenerate-btn" aria-label="Regenerate response">` | regenerate flow + a11y |

### Molecules (`components/molecules/`)

| Component | DOM contract | 用途 |
|---|---|---|
| `SourceLink` | `<div data-testid="source-link" data-source-label={label} id={'src-' + label}>` | Sources block 點擊 + RefSup anchor jump target |
| `ToolRow` | _(child of ToolCard, no separate testid)_ | — |
| `ToolDetail` | Root: `<div data-testid="tool-detail">`<br/>INPUT block: `<pre data-testid="tool-input-json">`<br/>OUTPUT block: `<pre data-testid="tool-output-json">`<br/>ERROR block: `<pre data-testid="tool-error-detail">` | 展開後 JSON / error detail 內容檢查 |
| `UserMessage` | `<div data-testid="user-bubble">` | user message 計數 / 內容比對 |
| `Sources` | `<section data-testid="sources-block">` | Sources block 存在性 + 子元素 query |

### Organisms (`components/organisms/`)

| Component | DOM contract | 用途 |
|---|---|---|
| `ChatHeader` | Root: `<header data-testid="chat-header">`<br/>Clear button: `<button data-testid="composer-clear-btn" aria-label="Clear conversation" disabled={messages.length === 0}>` | scope query + clear flow |
| `AssistantMessage` | `<article data-testid="assistant-message">` | assistant message 計數 / 區塊定位 |
| `ToolCard` | Root: `<div data-testid="tool-card" data-tool-call-id={toolCallId} data-tool-state={visualState}>`<br/>Expand button: `<button data-testid="tool-card-expand" aria-expanded={isOpen} aria-label="Toggle tool details">`<br/>Status dot: 透過 `StatusDot` atom，已含 testid<br/>Detail: 透過 `ToolDetail` molecule，已含 testid | tool 狀態查詢 + parallel tool 區分 + expand interaction |
| `Markdown` | _(transparent wrapper, no testid; renders into AssistantMessage)_ | — |
| `ErrorBlock` | Pre-stream variant: `<div data-testid="stream-error-block" data-error-source="pre-stream" data-error-class={errorClass}>`<br/>Mid-stream variant: `<div data-testid="inline-error-block" data-error-source="mid-stream" data-error-class={errorClass}>`<br/>Title: `<h3 data-testid="error-title">` _(內容為 friendly English title)_<br/>Detail toggle: `<button data-testid="error-detail-toggle" aria-expanded={isOpen}>`<br/>Detail panel: `<pre data-testid="error-raw-detail">`<br/>Retry button: `<button data-testid="error-retry-btn" aria-label="Retry">` _(只在 retriable=true 時 render)_ | 區分兩條 error 通道 + retry flow + show details toggle |
| `Composer` | Root: `<form data-testid="composer">`<br/>Textarea: `<textarea data-testid="composer-textarea" aria-label="Message input" placeholder="Ask about markets, companies, or filings...">`<br/>Send button: `<button data-testid="composer-send-btn" aria-label="Send message">`<br/>Stop button: `<button data-testid="composer-stop-btn" aria-label="Stop response">` | input + send / stop flow |
| `EmptyState` | `<div data-testid="empty-state">` | EmptyState 存在性檢查 |

### Templates (`components/templates/`)

| Component | DOM contract | 用途 |
|---|---|---|
| `MessageList` | Root: `<div data-testid="message-list" data-status={chatStatus}>` _(`chatStatus ∈ submitted \| streaming \| ready \| error`)_<br/>Viewport: `<div data-testid="message-list-viewport">` _(ScrollArea 內部 div，supplies scroll target)_ | overall page status + scroll target for follow-bottom + RefSup anchor scroll |

### Pages (`components/pages/`)

| Component | DOM contract | 用途 |
|---|---|---|
| `ChatPanel` | `<div data-testid="chat-panel" data-chat-id={chatId}>` _(註：`data-chat-id` 用 `import.meta.env.DEV` gate，prod build 不 render 此 attribute，避免不必要的 data exposure)_ | E2E test 驗 chatId reset 行為 |

### 補充規則

- **`data-status` / `data-tool-state` reactivity**: 兩者必須隨 React state 自動 reflect current value。Implementation 不得為了 perf 緩存舊值
- **`data-tool-state="aborted"`**: 對應第 4 個 frontend-only 視覺狀態（design.md 已補上 state machine），由 ChatPanel 的 `abortedTools: Set<ToolCallId>` 控制（見 Section 6）
- **`data-error-class` 取值**: `pre-stream-422` / `pre-stream-404` / `pre-stream-409` / `pre-stream-500` / `pre-stream-5xx` / `network` / `mid-stream` 等（對應 Section 5 的 ErrorClass enum）
- **所有 UI chrome strings 為 English**：對齊 design.md「UI String Language Policy」V1 決議 — placeholder / disclaimer / button label / `aria-label` / tool state label / welcome text / prompt chip text 全部 hardcoded 英文。Backend-provided content（`data-tool-progress` message、text body、tool output JSON）不翻譯
- **新增 component 時**: DOM contract 是 component spec 的必填欄位之一，跟 props / state / behavior 同等地位

---

## Section 2: MSW Test Infrastructure

### 何時用 MSW、何時用 real backend

| 條件 | 工具 |
|---|---|
| Happy path、自然 HTTP error、可預測 LLM 行為 | Real backend（Vite proxy → S1）|
| 需要特定 SSE event 順序 / 時間 / payload 才能驗的 edge case | MSW |
| Pre-stream HTTP error 中的 409 / network offline | MSW（real backend 難可靠觸發）|
| Mid-stream `error` event（特定時點、特定 errorText）| MSW |
| Security test（XSS、malicious URL）| MSW（real LLM 不會輸出 `javascript:`）|
| Boundary value（500KB JSON、duplicate refs、orphan refs）| MSW |

具體 scenario 對照表見 Section 3 fixture catalog 與 verification plan 各 scenario 的 method 欄位。

### 套件安裝

```bash
pnpm add -D msw
pnpm dlx msw init public/ --save  # 產生 public/mockServiceWorker.js
```

`public/mockServiceWorker.js` 必須 commit 到 git（MSW 官方建議），否則團隊成員 clone 後跑不動。

### 啟用機制 — URL-gated SW

```ts
// frontend/src/main.tsx
async function enableMocking() {
  if (import.meta.env.MODE !== 'development') return
  const params = new URLSearchParams(location.search)
  if (!params.has('msw_fixture')) return

  const { worker } = await import('./__tests__/msw/browser')
  await worker.start({
    serviceWorker: { url: '/mockServiceWorker.js' },
    onUnhandledRequest: 'bypass', // 非 /api/v1/chat 的 request 一律放行（fonts、static assets 等）
    quiet: false, // dev console 顯示攔截 log，方便 debug
  })
}

enableMocking().then(() => {
  ReactDOM.createRoot(document.getElementById('root')!).render(<App />)
})
```

**關鍵設計**：MSW SW 只在 URL 含 `?msw_fixture=xxx` 時註冊。Production build / 一般 dev 開發完全不掛 SW，零污染。

### 檔案結構

```
frontend/
├── public/
│   └── mockServiceWorker.js                    ← MSW CLI 產生，commit
└── src/
    └── __tests__/
        └── msw/
            ├── browser.ts                       ← setupWorker(handlers)
            ├── handlers.ts                      ← http.post('/api/v1/chat', ...)
            ├── README.md                        ← fixture 加 / 改 / 刪流程
            └── fixtures/
                ├── types.ts                     ← SSEFixture / UIMessageChunk types
                ├── index.ts                     ← registry: name → fixture module
                ├── happy-text.ts
                ├── happy-tool-then-text.ts
                ├── transient-progress-first.ts
                ├── ... (見 fixture catalog)
                └── README.md
```

### Browser setup

```ts
// frontend/src/__tests__/msw/browser.ts
import { setupWorker } from 'msw/browser'
import { handlers } from './handlers'

export const worker = setupWorker(...handlers)
```

### Handler 完整實作（reference）

```ts
// frontend/src/__tests__/msw/handlers.ts
import { http, HttpResponse, delay } from 'msw'
import { fixtures } from './fixtures'

export const handlers = [
  http.post('/api/v1/chat', async ({ request }) => {
    // 從 referrer URL 拿 active fixture
    // 因為 useChat 的內部 fetch 不會帶 query string，需從 page 的 URL 解析
    const refererUrl = new URL(request.headers.get('referer') ?? globalThis.location.href)
    const fixtureName = refererUrl.searchParams.get('msw_fixture') ?? 'happy-text'

    const fixture = fixtures[fixtureName]
    if (!fixture) {
      return HttpResponse.json(
        { error: `unknown fixture: ${fixtureName}` },
        { status: 500 }
      )
    }

    // 1. Pre-stream HTTP error fixture
    if ('preStreamError' in fixture) {
      return new HttpResponse(fixture.preStreamError.body ?? null, {
        status: fixture.preStreamError.status,
        headers: { 'Content-Type': 'application/json' },
      })
    }

    // 2. Network failure fixture (special)
    if ('networkFailure' in fixture && fixture.networkFailure) {
      return HttpResponse.error() // 模擬 fetch TypeError
    }

    // 3. SSE streaming fixture
    const encoder = new TextEncoder()
    const stream = new ReadableStream({
      async start(controller) {
        // CRITICAL: must honor client-side abort, otherwise S-stop-* BDD scenarios
        // false-fail (V-3 contract test confirmed this — see verification_results).
        // When useChat.stop() aborts the underlying fetch, request.signal fires;
        // close the stream so the SDK consumer sees end-of-stream and transitions
        // status back to 'ready'.
        const onAbort = () => {
          try {
            controller.close()
          } catch {
            /* already closed */
          }
        }
        request.signal.addEventListener('abort', onAbort)

        try {
          for (const chunk of fixture.chunks) {
            if (chunk.delayMs) await delay(chunk.delayMs)
            if (request.signal.aborted) return
            const frame = `data: ${JSON.stringify(chunk.data)}\n\n`
            controller.enqueue(encoder.encode(frame))
          }
          // truncated stream（測 mid-stream connection drop 用）
          if (!fixture.dropConnectionBeforeEnd) {
            controller.close()
          } else {
            controller.error(new Error('simulated connection drop'))
          }
        } catch (err) {
          controller.error(err)
        }
      },
    })

    return new HttpResponse(stream, {
      status: 200,
      headers: {
        'Content-Type': 'text/event-stream',
        'x-vercel-ai-ui-message-stream': 'v1', // S1 contract header
        'Cache-Control': 'no-cache',
      },
    })
  }),
]
```

### Fixture types

```ts
// frontend/src/__tests__/msw/fixtures/types.ts

// 對應 AI SDK v6 uiMessageChunkSchema 的 TypeScript shape
// 完整 schema 應從 AI SDK v6 import；這裡列 V1 用到的子集
export type UIMessageChunk =
  | { type: 'start'; messageId: string }
  | { type: 'text-start'; id: string }
  | { type: 'text-delta'; id: string; delta: string }
  | { type: 'text-end'; id: string }
  | { type: 'tool-input-available'; toolCallId: string; toolName: string; input: object }
  | { type: 'tool-output-available'; toolCallId: string; output: object }
  | { type: 'tool-output-error'; toolCallId: string; errorText: string }
  | { type: 'data-tool-progress'; id: string; data: { message: string }; transient: true }
  | { type: 'error'; errorText: string }
  | { type: 'finish' }

export type SSEStreamFixture = {
  description: string
  scenarios: string[]                              // 對應的 BDD scenario IDs
  chunks: Array<{ delayMs?: number; data: UIMessageChunk }>
  dropConnectionBeforeEnd?: boolean                // 模擬 mid-stream connection drop
}

export type PreStreamErrorFixture = {
  description: string
  scenarios: string[]
  preStreamError: {
    status: number
    body?: string
  }
}

export type NetworkFailureFixture = {
  description: string
  scenarios: string[]
  networkFailure: true
}

export type SSEFixture = SSEStreamFixture | PreStreamErrorFixture | NetworkFailureFixture
```

### Fixture registry

```ts
// frontend/src/__tests__/msw/fixtures/index.ts
import happyText from './happy-text'
import happyToolThenText from './happy-tool-then-text'
import transientProgressFirst from './transient-progress-first'
// ... 其餘 fixtures

import type { SSEFixture } from './types'

export const fixtures: Record<string, SSEFixture> = {
  'happy-text': happyText,
  'happy-tool-then-text': happyToolThenText,
  'transient-progress-first': transientProgressFirst,
  // ... 對應 catalog
}
```

### Browser-Use CLI integration

每個 BDD scenario 直接用 URL 切 fixture：

```bash
# 啟動 dev server (一次)
pnpm dev &
DEV_PID=$!

# 跑 scenario
browser-use open "http://localhost:5173/chat?msw_fixture=mid-stream-error-after-text"
browser-use input {composer-textarea} "anything"
browser-use click {composer-send-btn}
browser-use wait selector "[data-testid='inline-error-block']"
# ... assertions
```

切 fixture = 開新 URL，scenario 之間 clean state 自然產生（每次 page reload 重新 mount React）。

### Real backend 模式

跑 real backend scenarios 時 URL **不**帶 `?msw_fixture` query string。MSW SW 不註冊，request 直接走 Vite proxy 到 S1：

```bash
browser-use open "http://localhost:5173/chat"  # 無 msw_fixture
# ... real backend interactions
```

---

## Section 3: MSW Fixture Catalog

每個 fixture 對應一個或多個 BDD scenario。Fixture 命名為 kebab-case，描述「SSE event 序列特徵」而非 scenario ID。

### Catalog（按使用 fixture 的 scenario 排序）

| Fixture file | Type | Serves scenario(s) | Description / chunks |
|---|---|---|---|
| `transient-progress-first.ts` | SSEStream | S-stream-06 | 第一個 event 是 transient `data-tool-progress`，再來才是 `text-delta` |
| `start-then-error.ts` | SSEStream | S-stream-07 | `start` 之後立即 `error`，無任何 content part |
| `parallel-tools-progress-isolated.ts` | SSEStream | S-tool-05 | 兩個 tool 同時 running，progress 各自路由（id 隔離） |
| `progress-three-rapid.ts` | SSEStream | S-tool-04 | 同 tick 連發 3 個 progress（驗 functional setState） |
| `progress-then-success-no-sustain.ts` | SSEStream | S-tool-06 | tool success 後 progress 不沿用（label 改 generic）|
| `large-output-json-500kb.ts` | SSEStream | S-tool-08 | tool 完成回 ~500KB JSON payload |
| `tool-error-rate-limit.ts` | SSEStream | S-tool-02 | tool error，errorText = `"API rate limit exceeded"`（驗 friendly translation 不顯示 raw）|
| `parallel-tools-mixed-state.ts` | SSEStream | S-tool-03 | 兩個 tool，一個 success 一個 error |
| `duplicate-references.ts` | SSEStream | S-md-02 | markdown 含 `[1]: a` + `[1]: b` duplicate definition |
| `xss-javascript-url.ts` | SSEStream | S-md-03 | markdown 含 `[1]: javascript:alert(1) "Click"` 與 `[2]: mailto:...`（security guard 測試）|
| `orphan-refs.ts` | SSEStream | S-md-05 | body 含 `[3]` 無 def；`[1]: ...` def 存在但 body 未引用 |
| `pre-stream-409.ts` | PreStreamError | S-err-01 (row 3) | HTTP 409 session busy |
| `pre-stream-500.ts` | PreStreamError | S-err-01 (row 4)、S-err-02 base | HTTP 500 server error |
| `pre-stream-5xx-unknown.ts` | PreStreamError | S-err-01 (row 6) | HTTP 503 / 504 等不在 mapping 表的 5xx |
| `pre-stream-network-offline.ts` | NetworkFailure | S-err-01 (row 5)、S-err-09 base | `fetch` TypeError |
| `pre-stream-422-regenerate.ts` | PreStreamError | S-err-04 base、S-err-02 base | HTTP 422，body 含 messageId 錯誤訊息 |
| `mid-stream-error-after-text.ts` | SSEStream | S-err-05、S-err-08 | text-delta × 2（含 `[1]` ref + `[1]` def）→ `error` event |
| `mid-stream-error-after-tool.ts` | SSEStream | S-err-06 | tool-output-available（success）→ `error` event 在 text 開始前 |
| `mid-stream-error-tool-running.ts` | SSEStream | S-err-07 | tool-input-available → text-delta × 2 → `error` event（tool 沒收到 output，應轉 aborted）|
| `tool-running-no-output.ts` | SSEStream | S-stop-03 | tool-input-available 後長 delay 不發 output（給 user stop 機會）|
| `flaky-network-mid-stream.ts` | SSEStream | S-stop-02 | text-delta × 3 後 `dropConnectionBeforeEnd: true` |
| `mock-clear-conversation.ts` | SSEStream | S-clear-03 _(optional)_ | 用 mock context 驗證 chatId 隔離（real backend 為主，這個是 fallback）|

### Fixture file 範例

```ts
// frontend/src/__tests__/msw/fixtures/mid-stream-error-after-text.ts
import type { SSEStreamFixture } from './types'

const fixture: SSEStreamFixture = {
  description: 'Text streams 2 chunks (with [1] ref and def) then error event arrives',
  scenarios: ['S-err-05', 'S-err-08'],
  chunks: [
    { delayMs: 0,   data: { type: 'start', messageId: 'asst-mock-1' } },
    { delayMs: 30,  data: { type: 'text-start', id: 't1' } },
    { delayMs: 80,  data: { type: 'text-delta', id: 't1', delta: 'NVDA Q2 [1] beat estimates' } },
    { delayMs: 130, data: { type: 'text-delta', id: 't1', delta: ', and per [2]' } },
    { delayMs: 180, data: { type: 'text-delta', id: 't1', delta: '\n\n[1]: https://reuters.com/nvda-q2 "Reuters NVDA Q2"' } },
    { delayMs: 220, data: { type: 'error', errorText: 'context length exceeded' } },
  ],
}

export default fixture
```

```ts
// frontend/src/__tests__/msw/fixtures/xss-javascript-url.ts
import type { SSEStreamFixture } from './types'

const fixture: SSEStreamFixture = {
  description: 'Markdown contains javascript: URL — security guard test',
  scenarios: ['S-md-03'],
  chunks: [
    { delayMs: 0,   data: { type: 'start', messageId: 'asst-xss-1' } },
    { delayMs: 30,  data: { type: 'text-start', id: 't1' } },
    { delayMs: 80,  data: { type: 'text-delta', id: 't1', delta: 'See [1] for the report.\n\n' } },
    { delayMs: 130, data: { type: 'text-delta', id: 't1', delta: '[1]: javascript:alert("XSS") "Click me"\n' } },
    { delayMs: 180, data: { type: 'text-delta', id: 't1', delta: '[2]: mailto:ir@nvidia.com "Contact IR"\n' } },
    { delayMs: 230, data: { type: 'finish' } },
  ],
}

export default fixture
```

```ts
// frontend/src/__tests__/msw/fixtures/pre-stream-409.ts
import type { PreStreamErrorFixture } from './types'

const fixture: PreStreamErrorFixture = {
  description: 'HTTP 409 session busy — pre-stream error',
  scenarios: ['S-err-01 (row 3: 409 session busy)'],
  preStreamError: {
    status: 409,
    body: JSON.stringify({ error: 'session busy' }),
  },
}

export default fixture
```

```ts
// frontend/src/__tests__/msw/fixtures/pre-stream-network-offline.ts
import type { NetworkFailureFixture } from './types'

const fixture: NetworkFailureFixture = {
  description: 'Simulated fetch TypeError — network offline',
  scenarios: ['S-err-01 (row 5: network offline)', 'S-err-09 base'],
  networkFailure: true,
}

export default fixture
```

### Maintenance 流程

1. **新增 fixture**: 在 `__tests__/msw/fixtures/` 加一個 `.ts` 檔，import `SSEFixture` 子型別，default export，再到 `index.ts` 註冊。**必填欄位**：`description` 跟 `scenarios`（對應 BDD scenario ID 清單）
2. **修改 fixture**: 直接改檔案內容；TypeScript 會檢查 chunk 結構是否符合 `UIMessageChunk` shape
3. **刪除 fixture**: 必須先確認沒有 BDD scenario 引用（grep verification plan）
4. **Wire format 同步**: fixture chunks 必須符合 S1 的 `uiMessageChunkSchema`（已 align AI SDK v6）。S1 wire format locked，更新可能性極低；但若發生需一併更新所有 fixtures + types 檔
5. **Vitest 共用**: `__tests__/msw/fixtures/` 內的檔案也可在 unit / component test 中以 `setupServer` (msw/node) 共用，single source of truth

---

## Section 4: Pre-Coding Contract Verifications (V-1 / V-2 / V-3)

Implementation 開始前必須確認的三個 backend / library 行為。這些是 BDD scenarios + smart retry + aborted state 寫死的假設，若不成立 implementation 路線必須調整。建議列為 **Milestone 0** 任務，在 component implementation 前跑完。

### V-1: S1 對 partial turn regenerate 的回應碼

**為什麼要驗**: BDD scenarios `S-regen-03`、`S-err-04`、Q-USR-7 smart retry 都依賴知道「user stop 後 partial turn 是否能 regenerate」。

**測試方法**:

```bash
SESSION_ID=$(uuidgen)

# 1. 開始一個 long-running stream
curl -s -N -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d "{\"id\":\"$SESSION_ID\",\"message\":\"Write a 2000-word essay about NVIDIA history\"}" > /tmp/partial.sse &
CURL_PID=$!

# 2. 等 2 秒讓 stream 開始
sleep 2

# 3. Kill curl 模擬 user stop
kill $CURL_PID

# 4. 取得 partial messageId（從 partial SSE 解析）
MSG_ID=$(grep '"type":"start"' /tmp/partial.sse | head -1 | jq -r '.messageId')

# 5. 嘗試 regenerate partial turn
curl -s -o /tmp/regen.out -w "HTTP_STATUS=%{http_code}\n" \
  -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d "{\"id\":\"$SESSION_ID\",\"trigger\":\"regenerate\",\"messageId\":\"$MSG_ID\"}"
```

**Possible outcomes**:

| HTTP status | 結論 | 對 BDD / implementation 的影響 |
|---|---|---|
| 200 + new SSE stream | S1 接受 partial turn 的 regenerate | S-err-04 happy path 成立；smart retry 直接 regenerate（不需降級） |
| 422 | S1 拒絕（partial turn 不是 valid target） | smart retry **必須**降級為 `sendMessage(originalUserText)`；S-regen-03 寫法調整 |
| 500 / hang | S1 行為未定義 | 需 S1 owner 釐清；可能是 bug，需追加 backend coordination |

**Action**: 在 implementation milestone 0 跑這個測試，把結果寫入 `verification_results_streaming_chat_ui.md`（implementation 期間生成），然後相應調整 BDD scenarios。

---

### V-2: AI SDK v6 useChat 對 pre-stream HTTP error 的 user message lifecycle

**為什麼要驗**: BDD scenarios `S-err-02` + `Ch-Dev-1` 假設「pre-stream error 時 user bubble 仍在 messages array」。如果 AI SDK 不是 optimistic append（user message 等 response 成功才 append），這個假設不成立 → 需要 ChatPanel 自己 stash/restore。

**測試方法**: Vitest contract test，用 `setupServer` (msw/node) 攔截 fetch：

```ts
// frontend/src/__tests__/contract/use-chat-error-lifecycle.test.ts
// NOTE: Vitest config has globals: false → import test/expect/lifecycle hooks explicitly.
// NOTE: DefaultChatTransport is exported from `ai`, not `@ai-sdk/react`.
import { test, expect, beforeAll, afterEach, afterAll } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { useChat } from '@ai-sdk/react'
import { DefaultChatTransport } from 'ai'
import { setupServer } from 'msw/node'
import { http, HttpResponse } from 'msw'

const server = setupServer(
  http.post('/api/v1/chat', () =>
    HttpResponse.json({ error: 'boom' }, { status: 500 })
  )
)

beforeAll(() => server.listen())
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

test('V-2: user message remains in messages array after pre-stream HTTP 500', async () => {
  const transport = new DefaultChatTransport({ api: '/api/v1/chat' })
  const { result } = renderHook(() => useChat({ transport, id: 'test' }))

  await act(async () => {
    result.current.sendMessage({ text: 'test message' })
  })

  await waitFor(() => expect(result.current.error).toBeTruthy())

  // Critical assertion
  expect(result.current.messages).toHaveLength(1)
  expect(result.current.messages[0].role).toBe('user')
  expect(result.current.messages[0]).toMatchObject({
    parts: expect.arrayContaining([
      expect.objectContaining({ type: 'text', text: 'test message' }),
    ]),
  })
})
```

**Possible outcomes**:

| 結果 | 結論 | 影響 |
|---|---|---|
| Test passes | AI SDK v6 是 optimistic append | S-err-02 直接 implement，無需 stash |
| Test fails (messages.length === 0) | AI SDK 等 response 才 append | ChatPanel 必須在 `onError` callback 中 stash `lastUserText`，retry 時用 stashed 值；S-err-02 需要補一個「retry uses stashed text」步驟 |

**Action**: Milestone 0 跑這個 contract test，記錄結果。

---

### V-3: AI SDK v6 useChat.stop() 的 abort semantic

**為什麼要驗**: BDD scenarios `S-stop-01/02/03` 假設 stop() 立即停止 onData callback、status 立即轉 ready、不會 reject 成 'error' 狀態。

**測試方法**: Vitest contract test 模擬 streaming endpoint：

```ts
// frontend/src/__tests__/contract/use-chat-stop-semantic.test.ts
// NOTE: Vitest config has globals: false → import test/expect/lifecycle hooks explicitly.
// NOTE: DefaultChatTransport is exported from `ai`, not `@ai-sdk/react`.
import { test, expect, beforeAll, afterAll } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { useChat } from '@ai-sdk/react'
import { DefaultChatTransport } from 'ai'
import { setupServer } from 'msw/node'
import { http, HttpResponse, delay } from 'msw'

const server = setupServer(
  http.post('/api/v1/chat', async () => {
    const stream = new ReadableStream({
      async start(controller) {
        const encoder = new TextEncoder()
        controller.enqueue(encoder.encode(`data: ${JSON.stringify({ type: 'start', messageId: 'a1' })}\n\n`))
        await delay(100)
        controller.enqueue(encoder.encode(`data: ${JSON.stringify({ type: 'text-start', id: 't1' })}\n\n`))
        await delay(100)
        controller.enqueue(encoder.encode(`data: ${JSON.stringify({ type: 'text-delta', id: 't1', delta: 'hello' })}\n\n`))
        // Long delay to give test time to call stop()
        await delay(5000)
        controller.close()
      },
    })
    return new HttpResponse(stream, {
      headers: { 'Content-Type': 'text/event-stream', 'x-vercel-ai-ui-message-stream': 'v1' },
    })
  })
)

beforeAll(() => server.listen())
afterAll(() => server.close())

test('V-3: stop() transitions status to ready, not error', async () => {
  const transport = new DefaultChatTransport({ api: '/api/v1/chat' })
  const { result } = renderHook(() => useChat({ transport, id: 'test' }))

  await act(async () => {
    result.current.sendMessage({ text: 'long question' })
  })

  await waitFor(() => expect(result.current.status).toBe('streaming'))

  await act(async () => {
    await result.current.stop()
  })

  await waitFor(() => expect(result.current.status).toBe('ready'))
  // useChat.error is `Error | undefined` — on a clean abort it's never set
  expect(result.current.error).toBeUndefined() // 不能變 'error' 狀態
})
```

**Possible outcomes**:

| 結果 | 結論 | 影響 |
|---|---|---|
| Test passes | stop() resolve normally + status → ready | S-stop-01/02 直接 implement |
| Test fails (status === 'error') | stop() 觸發 error state | ChatPanel handleStop 需要 wrap in try-catch + 強制 setStatus + filter out AbortError |
| Test fails (status === 'streaming') | stop() didn't propagate | 這是 AI SDK bug，需要 escalate |

**Action**: Milestone 0 跑這個 contract test。

---

### V-1/V-2/V-3 Action checklist

- [ ] Milestone 0 跑完 V-1 / V-2 / V-3
- [ ] 結果寫入 `verification_results_streaming_chat_ui.md`（implementation 階段生成）
- [ ] 任一失敗 → 回頭調整 BDD scenarios + smart retry 實作策略
- [ ] 全部 pass → 進入 component implementation milestone

---

## Section 5: Smart Retry Implementation Notes

### 為什麼需要 lastTriggerRef

`useChat.error` 只記錄錯誤本身，不記錄「上一次 trigger 的是 sendMessage 還是 regenerate」。Smart retry 必須兩種資訊都有才能 dispatch。

### Architecture

`ChatPanel` 維護一個 `lastTrigger` ref：

```ts
type LastTrigger =
  | { type: 'send'; userText: string }
  | { type: 'regenerate'; messageId: string; userText: string }

const lastTriggerRef = useRef<LastTrigger | null>(null)
```

每次 sendMessage / regenerate 前 update：

```ts
const handleSend = (text: string) => {
  lastTriggerRef.current = { type: 'send', userText: text }
  sendMessage({ text })
}

const handleRegenerate = (messageId: string) => {
  const userText = findOriginalUserText(messages, messageId) // 從 messages 找對應 user turn
  lastTriggerRef.current = { type: 'regenerate', messageId, userText }
  regenerate({ messageId })
}
```

`findOriginalUserText` helper：

```ts
function findOriginalUserText(messages: UIMessage[], assistantMessageId: string): string {
  const idx = messages.findIndex(m => m.id === assistantMessageId)
  if (idx <= 0) return ''
  // assistant 前面那則必然是 user
  const userMsg = messages[idx - 1]
  if (userMsg.role !== 'user') return ''
  const textPart = userMsg.parts.find(p => p.type === 'text')
  return textPart?.text ?? ''
}
```

### handleRetry dispatch table

```ts
const handleRetry = () => {
  const last = lastTriggerRef.current
  if (!last) return // shouldn't happen, defensive

  const errorClass = classifyError(useChatError) // see classifyError below

  // Smart fallback: 422-on-regenerate → sendMessage
  if (last.type === 'regenerate' && errorClass === 'pre-stream-422') {
    lastTriggerRef.current = { type: 'send', userText: last.userText }
    sendMessage({ text: last.userText })
    return
  }

  // Default: replay original action
  if (last.type === 'send') {
    sendMessage({ text: last.userText })
    return
  }

  if (last.type === 'regenerate') {
    regenerate({ messageId: last.messageId })
    return
  }
}
```

### classifyError helper

```ts
export type ErrorClass =
  | 'pre-stream-422'
  | 'pre-stream-404'
  | 'pre-stream-409'
  | 'pre-stream-500'
  | 'pre-stream-5xx'
  | 'network'
  | 'mid-stream'
  | 'unknown'

function classifyError(err: unknown): ErrorClass {
  // network failure (fetch TypeError)
  if (err instanceof TypeError && /fetch/i.test(err.message)) {
    return 'network'
  }

  // pre-stream HTTP error
  if (err && typeof err === 'object' && 'status' in err) {
    const status = (err as { status: number }).status
    if (status === 422) return 'pre-stream-422'
    if (status === 404) return 'pre-stream-404'
    if (status === 409) return 'pre-stream-409'
    if (status === 500) return 'pre-stream-500'
    if (status >= 500 && status < 600) return 'pre-stream-5xx'
  }

  // mid-stream errors come from message parts (errorPart on AssistantMessage), 
  // handled in AssistantMessage component, not in classifyError
  return 'unknown'
}
```

### Friendly mapping

`ErrorClass` → friendly title 對應見 `design_streaming_chat_ui.md` 的 "Friendly Mapping 表"。Implementation 直接讀 design.md 的表格，把 13 個 entry 翻成 switch case 在 `lib/error-messages.ts`。

---

## Section 6: Aborted ToolCard State Implementation Notes

### State location

`ChatPanel` 維護 `abortedTools: Set<ToolCallId>`：

```ts
const [abortedTools, setAbortedTools] = useState<Set<ToolCallId>>(new Set())
```

### 何時加入 abortedTools

#### Path 1: User stop()

```ts
const handleStop = () => {
  // 找出當前所有 input-available 的 tool（從 messages 走訪 last assistant 的 parts）
  const runningToolIds = collectRunningTools(messages)
  setAbortedTools(prev => new Set([...prev, ...runningToolIds]))
  stop()
}
```

#### Path 2: Mid-stream error

useChat 在收到 `error` event 時會把 error part append 到 last assistant message。ChatPanel 用 `useEffect` 監聽 messages 變化：

```ts
useEffect(() => {
  const lastMsg = messages.at(-1)
  if (!lastMsg || lastMsg.role !== 'assistant') return
  const hasErrorPart = lastMsg.parts.some(p => p.type === 'error')
  if (!hasErrorPart) return

  // mid-stream error 出現 → 把該 message 中所有仍 input-available 的 tool 標 aborted
  const runningToolIds = lastMsg.parts
    .filter(p => p.type === 'tool' && p.state === 'input-available')
    .map(p => p.toolCallId)
  if (runningToolIds.length > 0) {
    setAbortedTools(prev => new Set([...prev, ...runningToolIds]))
  }
}, [messages])
```

### 何時清除 abortedTools

清除時機跟 `toolProgress` Record 一致（atomic cleanup）：

| Trigger | Action |
|---|---|
| 新 user message（sendMessage）| 不清（保留歷史 turn 的 aborted state）|
| Regenerate | 清掉 last assistant turn 對應的 toolCallIds |
| Clear session | 全清 |

```ts
const handleClearSession = () => {
  stop() // 可能正在 streaming
  setChatId(crypto.randomUUID())
  clearProgress() // useToolProgress
  setAbortedTools(new Set()) // 一併清
}
```

### Propagation 到 ToolCard

`AssistantMessage` 接 `abortedTools` props：

```tsx
function AssistantMessage({ message, abortedTools, ... }: Props) {
  return message.parts.map((part, idx) => {
    if (part.type === 'tool') {
      const isAborted =
        part.state === 'input-available' && abortedTools.has(part.toolCallId)
      return (
        <ToolCard
          key={part.toolCallId}
          part={part}
          isAborted={isAborted}
          progressText={toolProgress[part.toolCallId]}
          ...
        />
      )
    }
    // ... 其他 part 類型
  })
}
```

### ToolCard 視覺切換

```tsx
function ToolCard({ part, isAborted, progressText }: Props) {
  // visualState 把 aborted override 進來
  const visualState = isAborted ? 'aborted' : part.state

  return (
    <div
      data-testid="tool-card"
      data-tool-call-id={part.toolCallId}
      data-tool-state={visualState}
    >
      <StatusDot state={visualState} />
      {/* aborted 時 label 顯示「Aborted」，無 progress text */}
      <span>
        {isAborted ? 'Aborted' : labelForState(visualState, progressText, part.toolName)}
      </span>
      {/* 其他 row 元素 */}
    </div>
  )
}
```

### StatusDot 視覺

```tsx
function StatusDot({ state }: { state: 'running' | 'success' | 'error' | 'aborted' }) {
  return (
    <span
      data-testid="status-dot"
      data-status-state={state}
      className={cn(
        'h-2 w-2 rounded-full',
        state === 'running' && 'bg-[var(--status-running)] animate-pulse',
        state === 'success' && 'bg-[var(--status-success)]',
        state === 'error' && 'bg-[var(--status-error)]',
        state === 'aborted' && 'bg-[var(--status-aborted)]', // **無 animate-pulse**
      )}
    />
  )
}
```

關鍵不變量：**aborted 狀態必須無 `animate-pulse`**，否則暗示「仍在進行」會誤導 user。

---

## Section 7: lib/error-messages.ts Implementation Contract

### Interface

```ts
// frontend/src/lib/error-messages.ts

export type ErrorContext = {
  source: 'pre-stream-http' | 'mid-stream-sse' | 'tool-output-error' | 'network'
  status?: number       // for pre-stream-http
  rawMessage?: string   // backend's original errorText (raw English)
}

export type FriendlyError = {
  title: string         // user-facing English text (from mapping table)
  detail?: string       // raw rawMessage for "Show details" expand
  retriable: boolean    // 控制 Retry button visibility
}

export function toFriendlyError(ctx: ErrorContext): FriendlyError
```

### 實作

把 design.md "Friendly Mapping 表" 的 13 個 entry 翻成程式邏輯。Pseudo-code 結構：

```ts
export function toFriendlyError(ctx: ErrorContext): FriendlyError {
  const { source, status, rawMessage } = ctx

  // Pre-stream HTTP errors
  if (source === 'pre-stream-http' && status !== undefined) {
    if (status === 422) return { title: "Couldn't regenerate that message. Please try again.", retriable: true, detail: rawMessage }
    if (status === 404) return { title: 'Conversation not found. Refresh to start a new one.', retriable: false, detail: rawMessage }
    if (status === 409) return { title: 'The system is busy. Please try again in a moment.', retriable: true, detail: rawMessage }
    if (status === 500) return { title: 'Server error. Please try again.', retriable: true, detail: rawMessage }
    if (status >= 500) return { title: 'Something went wrong. Please try again.', retriable: true, detail: rawMessage }
  }

  // Network failure
  if (source === 'network') {
    return { title: 'Connection lost. Check your network and try again.', retriable: true, detail: rawMessage }
  }

  // Tool output error — pattern match on rawMessage
  if (source === 'tool-output-error' && rawMessage) {
    if (/rate limit/i.test(rawMessage)) return { title: 'Too many requests. Please wait a moment and try again.', retriable: true, detail: rawMessage }
    if (/not found|404/i.test(rawMessage)) return { title: "We couldn't find that data.", retriable: false, detail: rawMessage }
    if (/timeout/i.test(rawMessage)) return { title: 'The tool timed out. Please try again.', retriable: true, detail: rawMessage }
    if (/permission|forbidden|401|403/i.test(rawMessage)) return { title: 'Access denied for this resource.', retriable: false, detail: rawMessage }
    return { title: 'The tool failed to run. Please try again.', retriable: true, detail: rawMessage }
  }

  // Mid-stream SSE error — pattern match
  if (source === 'mid-stream-sse' && rawMessage) {
    if (/context.*length|context.*overflow|token.*limit/i.test(rawMessage)) return { title: 'This conversation is too long. Start a new chat to continue.', retriable: false, detail: rawMessage }
    if (/rate limit/i.test(rawMessage)) return { title: 'The system is busy. Please try again in a moment.', retriable: true, detail: rawMessage }
    return { title: 'Something went wrong while generating the response. Please try again.', retriable: true, detail: rawMessage }
  }

  // Fallback
  return { title: 'Something went wrong. Please try again.', retriable: true, detail: rawMessage }
}
```

### 不變量（unit test 必須驗證）

- `title` 永遠存在（無 undefined / empty string）
- `title` 永遠是英文，max 60 chars
- `detail` 只在 `rawMessage` 存在時 set
- `retriable` 嚴格遵守 mapping 表（下游不可覆寫）
- 13 個 mapping entry + 至少 5 個 fallback case 必須有 unit test 覆蓋

### Test 範例

```ts
// frontend/src/lib/__tests__/error-messages.test.ts
import { toFriendlyError } from '../error-messages'

describe('toFriendlyError', () => {
  test('pre-stream 422', () => {
    const result = toFriendlyError({ source: 'pre-stream-http', status: 422 })
    expect(result.title).toBe("Couldn't regenerate that message. Please try again.")
    expect(result.retriable).toBe(true)
  })

  test('tool-output-error rate limit pattern', () => {
    const result = toFriendlyError({
      source: 'tool-output-error',
      rawMessage: 'API rate limit exceeded for yfinance',
    })
    expect(result.title).toBe('Too many requests. Please wait a moment and try again.')
    expect(result.retriable).toBe(true)
    expect(result.detail).toBe('API rate limit exceeded for yfinance')
  })

  test('non-retriable: 404', () => {
    const result = toFriendlyError({ source: 'pre-stream-http', status: 404 })
    expect(result.retriable).toBe(false)
  })

  test('fallback for unknown context', () => {
    const result = toFriendlyError({ source: 'pre-stream-http' })
    expect(result.title).toBeTruthy()
    expect(result.retriable).toBe(true)
  })

  // ... 其餘 13+ 個 entry
})
```

---

## Section 8: Implementation Plan 對接 Checklist

`implementation-planning` skill 拿到 design.md + 本文件 + bdd_scenarios + verification_plan 後產出的 task graph 必須包含：

### Milestone 0 — Pre-coding contract verifications

- [ ] V-1: S1 partial turn regenerate 行為（curl script）
- [ ] V-2: AI SDK v6 useChat pre-stream error user message lifecycle（Vitest contract test）
- [ ] V-3: AI SDK v6 useChat.stop() abort semantic（Vitest contract test）
- [ ] 結果寫入 `verification_results_streaming_chat_ui.md`
- [ ] 任一失敗 → 回頭調整 BDD assumptions / implementation 策略

### Milestone 1 — Test infrastructure scaffolding

- [ ] `pnpm add -D msw` + `pnpm dlx msw init public/`
- [ ] 建立 `frontend/src/__tests__/msw/{browser,handlers,fixtures/types,fixtures/index}.ts`
- [ ] `main.tsx` 加 `enableMocking()` URL-gated SW 註冊邏輯
- [ ] 建立 high-priority fixtures（先做 5 個關鍵的）：
  - `xss-javascript-url`（security critical）
  - `duplicate-references`
  - `mid-stream-error-after-text`
  - `pre-stream-409`
  - `pre-stream-network-offline`
- [ ] 其餘 ~15 個 fixtures 在對應 component 實作完成後補上

### Milestone 2 — Foundation libraries

- [ ] `lib/error-messages.ts` + unit tests（13 + 5 cases）
- [ ] `lib/markdown-sources.ts`（已在 design.md 定義 — remark plugin + dedup first-wins + orphan handling + scheme allowlist）+ unit tests
- [ ] `hooks/useFollowBottom.ts` + unit tests
- [ ] `hooks/useToolProgress.ts` + unit tests
- [ ] `models.ts` 補上 `ToolUIState` 加 `'aborted'` enum 值

### Milestone 3 — Component implementation (atomic 6 layers)

每個 component 的 task 必須包含：

- 對應 design.md 的 atomic 層級與責任
- Props interface
- **DOM contract（從本文件 Section 1 複製）**
- 對應的 BDD scenario IDs（從 verification plan 找）
- Unit test 範圍

順序：primitives → atoms → molecules → organisms → templates → pages

### Milestone 4 — ChatPanel orchestration

- [ ] `useState<ChatId>` + `useChat` wiring
- [ ] `useToolProgress` + onData wiring
- [ ] `useFollowBottom` wiring
- [ ] `lastTriggerRef` + `handleRetry` smart dispatch（Section 5）
- [ ] `abortedTools: Set<ToolCallId>` state + propagation（Section 6）
- [ ] `handleStop` / `handleClearSession` / `handleRegenerate` callbacks
- [ ] `handleErrorEvent` useEffect（mid-stream error → mark aborted tools）

### Milestone 5 — BDD verification execution

- [ ] Phase A: Real backend scenarios（~60% scenarios）
- [ ] Phase B: MSW scenarios（~40% scenarios，依 Section 3 catalog）
- [ ] 各 scenario 結果寫入 `verification_results_streaming_chat_ui.md`
- [ ] Manual smoke tests（MBT-01 ~ MBT-07）
- [ ] User acceptance test（UAT-01 ~ UAT-05）

### Milestone 6 — Cleanup + handoff

- [ ] 所有 BDD scenario green
- [ ] All unit / component / contract tests pass
- [ ] Bundle size sanity check
- [ ] 寫 `briefing_streaming_chat_ui.md`（generate-briefing skill）供 human review

---

## Appendix: Cross-Reference Index

### Design.md 章節對應

| 本文件 section | Design.md 對應 |
|---|---|
| Section 1 (DOM contract) | Component Responsibilities (atoms/molecules/organisms/templates/pages) + File Structure |
| Section 2 (MSW infra) | Testing Strategy（補強原本只說「MSW mock SSE」沒展開的部分）|
| Section 5 (Smart retry) | Error 路徑雙通道 + Smart Retry Routing 章節 |
| Section 6 (Aborted state) | Tool Card State Machine 第 4 個 state |
| Section 7 (error-messages) | Error 顯示文字策略 — Friendly Mapping 表 |

### BDD scenario 對應

每個 fixture 的 `scenarios: string[]` 欄位直接連到 `bdd_scenarios_streaming_chat_ui.md` 的 scenario ID。Verification plan 各 scenario entry 的 method 欄位也標明 fixture name（更新後）。

### 與 verification_plan 的關係

verification_plan 使用本文件定義的：
- testid / data-* attribute 為 selector
- Fixture name 為 MSW scenario 切換依據
- V-1/V-2/V-3 為 pre-coding contract 前置條件
