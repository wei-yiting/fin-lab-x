# Implementation Plan: S3 Streaming Chat UI

> Design Reference: [`design_streaming_chat_ui.md`](./design_streaming_chat_ui.md)
> Companion Specs:
> - [`bdd_scenarios_streaming_chat_ui.md`](./bdd_scenarios_streaming_chat_ui.md) — 80 scenarios + Verification Layer Summary
> - [`implementation_prerequisites_streaming_chat_ui.md`](./implementation_prerequisites_streaming_chat_ui.md) — DOM contract、MSW infra、V-1/V-2/V-3、smart retry / aborted state architecture（Section 8 為本 plan 的 milestone backbone）
> - [`implementation_test_cases_streaming_chat_ui.md`](./implementation_test_cases_streaming_chat_ui.md) — 46 個 TDD test cases（unit / component / hook / integration / e2e）
> - [`verification_plan_streaming_chat_ui.md`](./verification_plan_streaming_chat_ui.md) — post-implementation 一次性 Browser-Use CLI verification

**Goal:** 以 atomic 6 層元件樹 + AI SDK v6 `useChat` 整合 + MSW URL-gated test infrastructure，把 S1 backend 的 SSE streaming wire format 渲染成符合 mockup 的 dark-theme chat UI，並滿足 80 個 BDD scenarios。

**Architecture / Key Decisions:**
- 採用 design.md 的 atomic 6 層元件樹（primitives → atoms → molecules → organisms → templates → pages），所有層級扁平放在 `frontend/src/components/` 下，不引入 `features/` 抽象（V1 single feature scope）。
- ChatPanel 為唯一 stateful orchestrator：透過 `useChat({ id, transport, onData })` 取得 messages / status / error，並自行維護 `chatId`、`abortedTools: Set<ToolCallId>`、`lastTriggerRef` 三個本地 state，把 streaming lifecycle、smart retry routing（422-on-regenerate → sendMessage 降級）、aborted tool propagation 統一在 page 層。
- Test surface 雙軌：production code 永久 ship `data-testid` / `data-tool-state` / `data-status` attributes（per prerequisites §1），加上 `data-chat-id`（仅 dev gated）。MSW 採 URL-gated SW（`?msw_fixture=xxx`），dev / prod 預設不掛 SW、零污染。
- TDD 紅綠重構嚴格貫穿，每個 component / hook / lib task 的 🔴 step 直接 reference 對應 TC ID，由 `implementation_test_cases.md` 提供完整 test code。

**Tech Stack:**
- React 19 + TypeScript 5.9 + Vite 8 + Tailwind CSS v4 + shadcn/ui (`radix-nova` style, `neutral` base)
- AI SDK v6（`ai@^6.0.142` + `@ai-sdk/react@^3.0.144`）+ `DefaultChatTransport`
- `react-markdown` + `remark-gfm` + 自家 `lib/markdown-sources.ts` remark plugin
- MSW v2 + Vitest + `@testing-library/react` + jsdom
- Playwright（E2E Tier 0：security / smoke / critical）

---

## Dependencies Verification

| Dependency | Version | Source | What Was Verified | Notes |
| ---------- | ------- | ------ | ----------------- | ----- |
| `@ai-sdk/react` | `^3.0.144` | Context7 `/vercel/ai/ai_6.0.0-beta.128` | `useChat({ transport, id, onData })` 回傳 `{ messages, sendMessage, regenerate, stop, status, error, setMessages }`；status enum `submitted \| streaming \| ready \| error` 跟 design.md `models.ts` 一致；`regenerate({ messageId })` 可指定 message（v6 從 `reload` 改名）；`onData` callback 接 transient data parts | V-2 / V-3 contract test 仍會在 M0 跑一次驗證 user message lifecycle 與 stop() abort semantic |
| `ai` | `^6.0.142` | Context7 同上 | `DefaultChatTransport({ api })` 為 transport 預設實作；header 可由 backend 用 `x-vercel-ai-ui-message-stream: v1` 標示 wire format；`uiMessageChunkSchema` 定義 9 個 chunk types（已被 S1 backend align） | `transport.api` 必須 override 為 `/api/v1/chat`，預設 `/api/chat` 會打到 wrong endpoint |
| `react-markdown` | latest | Design.md（incidental，按官方文件組合 plugin chain） | `<ReactMarkdown remarkPlugins={[remarkGfm, markdownSourcesPlugin]} components={{ a: RefSupOrLink, ... }}>` 支援 component override + plugin chain | reference link override 透過 `components.a` 或自訂 `RefSup` renderer |
| `remark-gfm` | latest | Design.md | GitHub Flavored Markdown extras（tables、strikethrough、autolinks）— 不影響 core wire format | 與 `markdown-sources` plugin 並列傳給 `remarkPlugins` |
| `msw` | `^2.x` | Context7 `/websites/mswjs_io` | `setupWorker(...handlers)` from `msw/browser`；`setupServer(...handlers)` from `msw/node`；`http.post()` handler 可回 `new HttpResponse(stream, { headers })` 的 `ReadableStream` 來模擬 SSE；`mswjs init public/` 產生 `mockServiceWorker.js`；`onUnhandledRequest: 'bypass'` 放行非 mock 的 request | MSW v2 還新增了高階 `sse()` namespace，但 prerequisites §2 鎖定走 `http.post + ReadableStream` 路線（更貼近 raw SSE，便於模擬 chunk delay / connection drop）；`mockServiceWorker.js` 必須 commit |
| `@playwright/test` | `^1.59` | Context7 `/microsoft/playwright/v1.58.2` | `getByTestId('xxx')` 預設讀 `data-testid` attribute；inline `@smoke` tag in title 跟 `tag: ['@smoke']` syntax 都能配合 `--grep @smoke` filter；`testDir` 在 `playwright.config.ts` 設定 | 既有 scaffold 的 `playwright.config.ts` 用 `testDir: "./e2e"`；本 plan 在 M1 移到 `./tests/e2e` 以對齊 test_cases.md §5 的檔案結構 |
| `lucide-react` | `^1.7.0` | Design.md「Shadcn Primitives Usage」 | 提供 `AlertCircle`、`ExternalLink`、`RefreshCw`、`ChevronRight`、`BarChart3`、`Newspaper`、`FileText`、`DollarSign` 等 icons | 已在 `package.json` dependencies |
| `@fontsource-variable/inter` / `jetbrains-mono` / `noto-sans-tc` | latest | Design.md「Font Stack」 | npm 套件提供 `@import` 入口，搭配 Tailwind v4 `@theme` 的 `--font-sans` / `--font-mono` 變數 | 移除既有 `@fontsource-variable/geist` |
| `shadcn` (CLI) | `^4.1.2` | Design.md「Shadcn Primitives Usage」+ existing `components.json` | `pnpm dlx shadcn@latest add textarea scroll-area collapsible empty alert badge` 會把 source code 複製到 `components/primitives/`，並自動安裝 `@radix-ui/*` peer deps | `components.json` 既有設定 `style: radix-nova`、`baseColor: neutral`、`ui` alias 為 `@/components/primitives` ✓ |

> **Untrusted-source guard**：所有 Context7 結果在納入 plan 前已檢視，無 prompt injection / 不安全步驟。Backend wire format 對齊已由 S1 commit `7f505be` lock，本 plan 不重新驗證。

---

## Constraints

- **Backend 不可改動**：S1 (`backend/agent_engine/`) 的 SSE wire format、`Orchestrator.astream_run()`、`/api/v1/chat` endpoint、SQLite checkpointer 全 lock。**唯一例外**：system prompt 補強 reference link `title` attribute 要求（已在 design.md 標為 backend coordination point），由 backend owner 在 separate PR 處理；frontend 仍實作 hostname fallback 確保 missing title 時不崩潰。
- **S2 scaffold 不可拆**：已存在的 `frontend/src/main.tsx`、`vitest.config.ts`、`tsconfig.*`、`eslint.config.js`、`components.json`、`prettier`、`pnpm-lock.yaml` 為 SoT，本 plan 只**修改**其中需更新的檔案，不重新生成。
- **既有 `frontend/src/components/primitives/button.tsx` 不可手動編輯** — shadcn primitive immutability 原則（design.md 已定義），未來 `pnpm dlx shadcn@latest add` upgrade 時會 overwrite。
- **`pnpm` 為唯一 package manager**：`frontend/pnpm-lock.yaml` 是 SoT，禁用 npm / yarn。
- **語言政策**：所有 user-facing string 依 design.md「UI String Language Policy」統一為 **English**（placeholder、disclaimer、clear button label、tool state label、error title、welcome text、prompt chip text、所有 `aria-label` 全部 English hardcoded）。所有 friendly error title 走 `lib/error-messages.ts` 集中翻譯，**禁止** UI 直接顯示 backend `rawMessage`。完整 canonical string 表見 design.md 該 section。Exception：`data-tool-progress` message、assistant text body、tool output JSON 為 backend-provided，frontend 原樣顯示不翻譯。
- **Test layer 鎖定**：BDD scenario 對應的 test layer 在 `bdd_scenarios.md` Verification Layer Summary 已 lock，不得「升級」unit test 為 component test、或「降級」integration test 為 unit test。
- **6 個 E2E Tier 0 tests 為上限**：CI 跑量受控；後續 regression test 走 per-bug 補上，不在本 plan 提前加 E2E。
- **`data-testid` 永久 ship 到 production**：bundle size impact 可忽略；不引入 babel plugin 移除。
- **設計決策 Q1–Q12 + Q-USR-1..11 為 lock**：本 plan 不再 relitigate，遇到衝突一律以 design.md / bdd_scenarios.md 為準（Q-USR-11 即 markdown reference scheme allowlist 的 security 決議）。

---

## File Plan

### Structure sketch

```text
frontend/
├── index.html                              (UPDATE: <html class="dark">)
├── vite.config.ts                          (UPDATE: server.proxy /api → :8000)
├── vercel.json                             ★ NEW (production rewrites)
├── playwright.config.ts                    (UPDATE: testDir → ./tests/e2e)
├── package.json                            (UPDATE: deps swap, see Dependencies)
├── public/
│   └── mockServiceWorker.js                ★ NEW (MSW CLI generated, commit it)
├── src/
│   ├── main.tsx                            (UPDATE: enableMocking() URL gate)
│   ├── App.tsx                             (UPDATE: mount <ChatPanel/>)
│   ├── index.css                           (UPDATE: font imports + .dark scope full S3 vars)
│   ├── models.ts                           ★ NEW
│   ├── lib/
│   │   ├── utils.ts                        (existing cn helper, untouched)
│   │   ├── error-messages.ts               ★ NEW
│   │   ├── error-classifier.ts             ★ NEW
│   │   ├── message-helpers.ts              ★ NEW
│   │   ├── markdown-sources.ts             ★ NEW (remark plugin)
│   │   ├── typing-indicator-logic.ts       ★ NEW (pure function)
│   │   └── __tests__/
│   │       ├── error-messages.test.ts
│   │       ├── error-classifier.test.ts
│   │       ├── message-helpers.test.ts
│   │       └── markdown-sources.test.ts
│   ├── hooks/
│   │   ├── useFollowBottom.ts              ★ NEW
│   │   ├── useToolProgress.ts              ★ NEW
│   │   └── __tests__/
│   │       ├── useFollowBottom.test.ts
│   │       └── useToolProgress.test.ts
│   ├── components/
│   │   ├── primitives/                     (shadcn raw, do not edit)
│   │   │   ├── button.tsx                  (existing)
│   │   │   ├── textarea.tsx                ★ NEW (shadcn add)
│   │   │   ├── scroll-area.tsx             ★ NEW (shadcn add)
│   │   │   ├── collapsible.tsx             ★ NEW (shadcn add)
│   │   │   ├── empty.tsx                   ★ NEW (shadcn add)
│   │   │   ├── alert.tsx                   ★ NEW (shadcn add)
│   │   │   └── badge.tsx                   ★ NEW (shadcn add)
│   │   ├── atoms/
│   │   │   ├── StatusDot.tsx
│   │   │   ├── RefSup.tsx
│   │   │   ├── Cursor.tsx
│   │   │   ├── TypingIndicator.tsx
│   │   │   ├── PromptChip.tsx
│   │   │   ├── RegenerateButton.tsx
│   │   │   └── __tests__/                  (TC-comp-typing-01 lives in MessageList tests)
│   │   ├── molecules/
│   │   │   ├── SourceLink.tsx
│   │   │   ├── ToolRow.tsx
│   │   │   ├── ToolDetail.tsx
│   │   │   ├── UserMessage.tsx
│   │   │   ├── Sources.tsx
│   │   │   └── __tests__/
│   │   │       └── Sources.test.tsx
│   │   ├── organisms/
│   │   │   ├── ChatHeader.tsx
│   │   │   ├── AssistantMessage.tsx
│   │   │   ├── ToolCard.tsx
│   │   │   ├── Markdown.tsx
│   │   │   ├── ErrorBlock.tsx
│   │   │   ├── Composer.tsx
│   │   │   ├── EmptyState.tsx
│   │   │   └── __tests__/
│   │   │       ├── ChatHeader.test.tsx
│   │   │       ├── AssistantMessage.test.tsx
│   │   │       ├── ToolCard.test.tsx
│   │   │       ├── ErrorBlock.test.tsx
│   │   │       ├── Composer.test.tsx
│   │   │       └── EmptyState.test.tsx
│   │   ├── templates/
│   │   │   ├── MessageList.tsx
│   │   │   └── __tests__/
│   │   │       └── MessageList.test.tsx
│   │   └── pages/
│   │       ├── ChatPanel.tsx
│   │       └── __tests__/
│   │           └── ChatPanel.integration.test.tsx
│   └── __tests__/
│       ├── contract/
│       │   ├── use-chat-error-lifecycle.test.ts        ★ TC-int-v2-01
│       │   └── use-chat-stop-semantic.test.ts          ★ TC-int-v3-01
│       └── msw/
│           ├── browser.ts
│           ├── handlers.ts
│           ├── README.md
│           └── fixtures/
│               ├── types.ts
│               ├── index.ts
│               └── *.ts                                (~21 fixtures)
└── tests/
    └── e2e/
        ├── security/
        │   └── xss-source-link.spec.ts                 ★ TC-e2e-xss-01
        ├── smoke/
        │   ├── chat-tool.spec.ts                       ★ TC-e2e-smoke-tool-01
        │   ├── clear-session.spec.ts                   ★ TC-e2e-smoke-clear-01
        │   └── app-shell.spec.ts                       (migrated from e2e/app.spec.ts)
        └── critical/
            ├── error-recovery.spec.ts                  ★ TC-e2e-smoke-error-01
            ├── stop-preserves-partial.spec.ts          ★ TC-e2e-stop-01
            └── refresh-invariant.spec.ts               ★ TC-e2e-refresh-01

artifacts/current/
└── verification_results_streaming_chat_ui.md           ★ NEW (M0 起逐步寫入)
```

### Operations table

| Operation | Path | Purpose |
|---|---|---|
| Update | `frontend/index.html` | `<html lang="en" class="dark">` 強制 dark theme |
| Update | `frontend/vite.config.ts` | 加 `server.proxy['/api'] = { target: 'http://localhost:8000', changeOrigin: true }` |
| Update | `frontend/playwright.config.ts` | `testDir: "./tests/e2e"` |
| Update | `frontend/package.json` | 移除 `@fontsource-variable/geist`，加入 fonts、`react-markdown`、`remark-gfm`、`msw`（dev）、shadcn primitives 帶進的 `@radix-ui/*` peer deps |
| Update | `frontend/src/main.tsx` | 加 `enableMocking()` URL-gated MSW SW 啟用邏輯 |
| Update | `frontend/src/App.tsx` | 從 placeholder 改為 `<ChatPanel />` |
| Update | `frontend/src/index.css` | 改字型 import；`.dark` scope 寫入 design.md 完整 CSS variables（含 `--chat-brand-accent` / `--status-*` / `--chat-fg-*`） |
| Move | `frontend/e2e/app.spec.ts` → `frontend/tests/e2e/smoke/app-shell.spec.ts` | 對齊新 testDir；test 內容保留 |
| Delete | `frontend/e2e/` | 空 dir 刪除 |
| Create | `frontend/vercel.json` | production rewrite `/api/:path* → ${BACKEND_HOST}/api/:path*` |
| Create | `frontend/public/mockServiceWorker.js` | `pnpm dlx msw init public/ --save` 產生 |
| Create | `frontend/src/models.ts` | domain types 單檔（`ChatMessage` / `ToolCallId` / `SourceRef` / `ExtractedSources` / `ToolUIState`） |
| Create | `frontend/src/lib/error-messages.ts` | `toFriendlyError(ctx) → FriendlyError`；14 mapping rows（5 pre-stream-http + 1 network + 5 tool-output + 3 mid-stream-sse） |
| Create | `frontend/src/lib/error-classifier.ts` | `classifyError(err) → ErrorClass` |
| Create | `frontend/src/lib/message-helpers.ts` | `findOriginalUserText(messages, assistantMessageId)` |
| Create | `frontend/src/lib/markdown-sources.ts` | pure function `extractSources(text)`：first-wins dedup + scheme allowlist + orphan handling + numeric label sort（**streaming 期間不執行**，由 AssistantMessage 在 `isStreaming === false` 時 `useMemo` 觸發一次）|
| Create | `frontend/src/lib/typing-indicator-logic.ts` | `shouldShowTypingIndicator({ status, lastMessage })` pure function |
| Create | `frontend/src/hooks/useToolProgress.ts` | `Record<ToolCallId, string>` state + `handleData` + `clearProgress` |
| Create | `frontend/src/hooks/useFollowBottom.ts` | 100px threshold + `forceFollowBottom()` |
| Create | `frontend/src/components/atoms/*.tsx` | 6 atoms |
| Create | `frontend/src/components/molecules/*.tsx` | 5 molecules |
| Create | `frontend/src/components/organisms/*.tsx` | 7 organisms |
| Create | `frontend/src/components/templates/MessageList.tsx` | 1 template |
| Create | `frontend/src/components/pages/ChatPanel.tsx` | 1 page，集中所有 hook 與 state |
| Create | `frontend/src/__tests__/contract/*.test.ts` | V-2 / V-3 contract tests（M0 跑） |
| Create | `frontend/src/__tests__/msw/{browser,handlers}.ts` + `fixtures/*` | MSW infra + 21 fixtures |
| Create | `frontend/tests/e2e/{security,smoke,critical}/*.spec.ts` | 6 E2E Tier 0 tests + migrated app shell |
| Create | `artifacts/current/verification_results_streaming_chat_ui.md` | 跨 milestone 累積寫 V-1/V-2/V-3 結果 + post-impl verification 結果 |

---

## Milestone 0 — Pre-coding Contract Verifications（BLOCKING gate）

> 這 3 個 contract check 是 BDD assumption 的根基。任一失敗都必須先回頭調整 BDD scenarios + smart retry 策略，**不可直接寫 component 程式碼**。結果寫進 `artifacts/current/verification_results_streaming_chat_ui.md`。
>
> 在這個階段允許存在以下最小 scaffold：MSW dev dependency、`__tests__/contract/` 目錄、最小可跑 Vitest setup（既有 `vitest.config.ts` 已 OK）。其他 component / hook / lib 一律**等 M0 全綠**才開始。

### Task 0.1: V-1 — S1 partial-turn regenerate 行為探測

**Files:**

- Create: `artifacts/current/verification_results_streaming_chat_ui.md`（初始化空骨架）

**What & Why:** 用 curl 模擬「user 開 long stream → 中途 kill curl → 對 partial messageId 發 `trigger=regenerate`」的流程，記錄 S1 回 200 / 422 / 500 / hang 中的哪一種。BDD `S-regen-03`、`S-err-04` 與 Q-USR-7 smart retry strategy 都依賴這個答案，若 S1 回 422 則 smart retry 必須降級為 `sendMessage(originalUserText)`（已是 default 假設）；若 S1 回 200 可以走更直接的 regenerate retry。

**Implementation Notes:**

- Backend 必須先 running：`cd backend && uv run uvicorn agent_engine.app:app --port 8000`
- Script 來源見 `implementation_prerequisites_streaming_chat_ui.md` §4 V-1（curl + jq + kill PID）
- 把實際 HTTP status、response body、實際 partial messageId 抄進 verification_results 文件

**Test Strategy:** 不寫 automated test — 這是「對 backend 行為的一次性觀測」。結果為事實紀錄（不是 assertion）。

**Verification:**

| Scope | Command | Expected Result | Why |
|---|---|---|---|
| Targeted | `bash scripts/v1-partial-regen-probe.sh`（內容見 prerequisites §4）| 印出 `HTTP_STATUS=...` 並且 stdout 含 partial messageId | 確認可重複執行、結果可記錄 |
| Recorded | 開 `artifacts/current/verification_results_streaming_chat_ui.md` | 含 `## V-1 Result: <status code> + <interpretation>` 段落 | 後續 milestone 引用 |

**Execution Checklist:**

- [ ] 建立 `artifacts/current/verification_results_streaming_chat_ui.md`，開頭寫入「V-1 / V-2 / V-3」三個小節骨架
- [ ] Backend running 確認（`curl http://localhost:8000/health` 回 200，或文件列出對應 health endpoint）
- [ ] 跑 V-1 curl script，把 raw output + interpretation 寫入 verification_results
- [ ] 若 status ≠ 422：回頭檢視 `lib/error-classifier.ts` mapping、smart retry routing 是否需調整（理論上 design 已預設 422，若 S1 回 200 可改更直接的 regenerate retry）
- [ ] Commit 結果：`git commit -m "test(s3): record V-1 S1 partial-turn regenerate behavior"`

---

### Task 0.2: V-2 — useChat pre-stream HTTP error 的 user message lifecycle（TC-int-v2-01）

**Files:**

- Create: `frontend/src/__tests__/contract/use-chat-error-lifecycle.test.ts`
- Update: `frontend/package.json`（先把 `msw` 加進 devDependencies，因為 contract test 用 `msw/node` 攔截 fetch）
- Update: `artifacts/current/verification_results_streaming_chat_ui.md`

**What & Why:** BDD `S-err-02` + dev challenge `Ch-Dev-1` 假設「pre-stream HTTP 500 後 user bubble 仍在 messages array」。如果 AI SDK v6 是「等 response 成功才 append」，這個假設不成立 → ChatPanel 必須自行 stash/restore `lastUserText`。先跑 contract test 鎖死 SDK 行為。

**Implementation Notes:**

- 完整 test code 見 `implementation_test_cases_streaming_chat_ui.md` TC-int-v2-01（也即 `implementation_prerequisites_streaming_chat_ui.md` §4 V-2）— **直接 copy 進 file，不要重寫**
- Test 用 `setupServer` (msw/node) 攔 `http.post('/api/v1/chat')` 回 HTTP 500
- 關鍵 assertion：`expect(result.current.messages).toHaveLength(1)` + `messages[0].role === 'user'`

**Critical Contract / Snippet:**

```ts
// 摘自 TC-int-v2-01 的核心 assertion
test('V-2: user message remains in messages array after pre-stream HTTP 500', async () => {
  const transport = new DefaultChatTransport({ api: '/api/v1/chat' })
  const { result } = renderHook(() => useChat({ transport, id: 'test' }))
  await act(async () => { result.current.sendMessage({ text: 'test message' }) })
  await waitFor(() => expect(result.current.error).toBeTruthy())
  expect(result.current.messages).toHaveLength(1)
  expect(result.current.messages[0].role).toBe('user')
})
```

**Test Strategy:** 此 test **本身** 就是 contract verification — 不需要再上一層 wrapper。它驗的是 AI SDK v6 而非自家 code，所以無 RED → GREEN cycle（test passes from day 1，如果 fails 表示 SDK 行為跟 design.md 假設衝突，需要重新設計）。

**Verification:**

| Scope | Command | Expected Result | Why |
|---|---|---|---|
| Targeted | `cd frontend && pnpm test -- src/__tests__/contract/use-chat-error-lifecycle.test.ts` | 1 test passed | TC-int-v2-01 預期 PASS（design 預設 SDK 是 optimistic append） |
| Recorded | append `## V-2 Result: PASS — useChat is optimistic append` 到 verification_results | — | 後續 ChatPanel implementation 不必加 stash/restore |

**Execution Checklist:**

- [ ] `pnpm add -D msw` （只加 dep，先不跑 init public，那是 M1 的事）
- [ ] Copy TC-int-v2-01 的 test code 到 `frontend/src/__tests__/contract/use-chat-error-lifecycle.test.ts`
- [ ] Run `pnpm test -- src/__tests__/contract/use-chat-error-lifecycle.test.ts` → expect PASS
- [ ] **若 FAIL（messages.length === 0）** → STOP，回頭把「ChatPanel onError stash lastUserText」加回 design / 本 plan，再繼續
- [ ] 把結果（PASS / FAIL + 解釋）寫入 verification_results
- [ ] Commit：`git commit -m "test(s3): V-2 useChat pre-stream error user message lifecycle contract"`

---

### Task 0.3: V-3 — useChat.stop() abort semantic（TC-int-v3-01）

**Files:**

- Create: `frontend/src/__tests__/contract/use-chat-stop-semantic.test.ts`
- Update: `artifacts/current/verification_results_streaming_chat_ui.md`

**What & Why:** BDD `S-stop-01/02/03` 全部假設「stop() 後 status 立即轉 ready，且 error 維持 null（不會被 AbortError 污染）」。先用 contract test lock 死 — 若 SDK stop() 把 status 推進 'error'，ChatPanel 的 `handleStop` 必須包 try-catch + filter AbortError + 強制 setStatus，這會大幅改變 implementation 路線。

**Implementation Notes:**

- 完整 test code 見 `implementation_prerequisites_streaming_chat_ui.md` §4 V-3（msw/node 用 5 秒長 stream + `await result.current.stop()` 後 assert `status === 'ready'` 且 `error === null`）
- **不要** 從記憶寫 — copy verbatim

**Critical Contract / Snippet:**

```ts
// 摘自 V-3 的核心 assertion
// NOTE: useChat.error is `Error | undefined` (not `Error | null`) — see V-3 post-mortem in verification_results.
await act(async () => { await result.current.stop() })
await waitFor(() => expect(result.current.status).toBe('ready'))
expect(result.current.error).toBeUndefined()
```

**Test Strategy:** 同 TC-int-v2-01 的角色：contract verification，pass 就是 design 假設成立。

**Verification:**

| Scope | Command | Expected Result | Why |
|---|---|---|---|
| Targeted | `cd frontend && pnpm test -- src/__tests__/contract/use-chat-stop-semantic.test.ts` | 1 test passed，duration 約 0.5–1.5s（因為 5s stream 在 stop 後早終止） | 鎖定 stop() 為 graceful，非 error transition |

**Execution Checklist:**

- [ ] Copy TC-int-v3-01 完整 test code（含 setupServer 模擬長 stream）
- [ ] Run test → expect PASS
- [ ] **若 status === 'error'** → 在 verification_results 紀錄，並把「ChatPanel handleStop wrap try-catch + 強制 setStatus」加進 M5 ChatPanel 任務
- [ ] **若 status === 'streaming'** → 這是 SDK bug，escalate 給 user，停止後續 milestone
- [ ] 把結果寫入 verification_results
- [ ] Commit：`git commit -m "test(s3): V-3 useChat.stop() abort semantic contract"`

---

### Flow Verification: Milestone 0 contract gates

> Tasks 0.1 / 0.2 / 0.3 共同完成 pre-coding contract verification。**任一 task 結果與 design 假設衝突 → 必須先回頭調整 design / plan，後續 milestone 全 block。**

| #   | Method                        | Step                                                                                                                              | Expected Result                                                                                  |
| --- | ----------------------------- | --------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| 1   | curl                          | 跑 V-1 partial-regen probe                                                                                                        | 印出 HTTP status + partial messageId，結果 record 進 verification_results                          |
| 2   | Vitest contract               | `pnpm test -- src/__tests__/contract/`                                                                                            | 2 passed, 0 failed                                                                              |
| 3   | Document inspection           | 開 `artifacts/current/verification_results_streaming_chat_ui.md`                                                                  | 含 V-1 / V-2 / V-3 三個 sections，每個有 PASS / FAIL + 解釋                                       |
| 4   | Conditional design adjustment | 若任何 result 跟 design 假設衝突 → 在 plan 對應 milestone 加 task 修正；否則直接進 M1                                                 | 衝突已被處理或不存在                                                                              |

- [ ] All Milestone 0 verifications pass（或任何 conflict 已被處理）

---

## Milestone 1 — Test Infrastructure Scaffolding

### Task 1.1: 安裝 deps、重整 e2e 目錄、建立 MSW infrastructure 與 5 個高優先 fixtures

**Files:**

- Update: `frontend/package.json` — 移除 `@fontsource-variable/geist`；加 `react-markdown`、`remark-gfm`、`@fontsource-variable/inter`、`@fontsource-variable/jetbrains-mono`、`@fontsource-variable/noto-sans-tc`；shadcn CLI 自動帶入 `@radix-ui/react-textarea`（無此 prim 直接 textarea）、`@radix-ui/react-scroll-area`、`@radix-ui/react-collapsible` 等
- Update: `frontend/playwright.config.ts` — `testDir: "./tests/e2e"`
- Move: `frontend/e2e/app.spec.ts` → `frontend/tests/e2e/smoke/app-shell.spec.ts`
- Delete: `frontend/e2e/`（空 dir 移除）
- Create: `frontend/public/mockServiceWorker.js`（pnpm dlx msw init public/ --save 產生，commit）
- Create: `frontend/src/__tests__/msw/browser.ts`
- Create: `frontend/src/__tests__/msw/handlers.ts`
- Create: `frontend/src/__tests__/msw/README.md`
- Create: `frontend/src/__tests__/msw/fixtures/types.ts`
- Create: `frontend/src/__tests__/msw/fixtures/index.ts`
- Create: `frontend/src/__tests__/msw/fixtures/xss-javascript-url.ts` — security critical
- Create: `frontend/src/__tests__/msw/fixtures/duplicate-references.ts`
- Create: `frontend/src/__tests__/msw/fixtures/mid-stream-error-after-text.ts`
- Create: `frontend/src/__tests__/msw/fixtures/pre-stream-409.ts`
- Create: `frontend/src/__tests__/msw/fixtures/pre-stream-network-offline.ts`
- Update: `frontend/src/main.tsx` — 加 `enableMocking()` URL-gated SW 註冊邏輯
- Update: `frontend/index.html` — `<html lang="en" class="dark">`
- Update: `frontend/vite.config.ts` — `server.proxy['/api'] = { target: 'http://localhost:8000', changeOrigin: true }`
- Create: `frontend/vercel.json` — production rewrites（`<backend-paas-host>` 留 placeholder + comment 提醒部署前要改）

**What & Why:** Test infra 是後續所有 layer 的前置條件。把 MSW + Playwright dir + 5 個 highest-priority fixtures + Vite proxy + dark class 一次到位，後續 component task 才能寫 component test 並用 dev server 看到實際 dark theme（即使 components 還沒寫完）。

**Implementation Notes:**

- `enableMocking()` 嚴格 gate 在 `import.meta.env.MODE === 'development' && URL.searchParams.has('msw_fixture')` — production build 與一般 dev 都不掛 SW
- `handlers.ts` 從 `referer` URL 解析 `msw_fixture` query string（因為 `useChat` 的 fetch 不會帶 query）
- **CRITICAL — abort signal handling**: streaming branch 必須監聽 `request.signal.addEventListener('abort', ...)` 並 `controller.close()`，否則 `S-stop-*` 系列 BDD scenarios 會 false-fail（V-3 contract test 已證實 — 詳見 verification_results §V-3 plan-defect post-mortem）。直接 copy prerequisites §2 handlers.ts 的 reference snippet 即可（已含 abort handler）。
- **CRITICAL — text-delta payload field**: 所有 `text-delta` chunk 一律使用 `delta` field（與 AI SDK v6 wire format 一致），絕不使用 `textDelta`（plan defect，已批次修正）。
- 5 個 priority fixtures 對應的 BDD scenarios：
  - `xss-javascript-url` → S-md-03（security critical，e2e 必跑）
  - `duplicate-references` → S-md-02（first-wins dedup unit test 需要的 reference fixture）
  - `mid-stream-error-after-text` → S-err-05、S-err-08（mid-stream error 行為）
  - `pre-stream-409` → S-err-01 row 3（409 session busy）
  - `pre-stream-network-offline` → S-err-01 row 5、S-err-09（fetch TypeError）
- 其餘 ~16 個 fixtures 在後續對應 component 完成後**逐步補上**，不在這個 task 一次寫完
- `vercel.json` 因為 backend host 還沒定，使用 `https://REPLACE_ME_BEFORE_DEPLOY/api/:path*` placeholder 並在檔案頂部加 JSON-comment-friendly README markdown 說明

**Critical Contract / Snippet:**

```ts
// frontend/src/main.tsx — enableMocking 結構
import { StrictMode } from "react"
import { createRoot } from "react-dom/client"
import "./index.css"
import App from "./App.tsx"

async function enableMocking() {
  if (import.meta.env.MODE !== "development") return
  if (!new URLSearchParams(location.search).has("msw_fixture")) return
  const { worker } = await import("./__tests__/msw/browser")
  await worker.start({
    serviceWorker: { url: "/mockServiceWorker.js" },
    onUnhandledRequest: "bypass",
    quiet: false,
  })
}

enableMocking().then(() => {
  createRoot(document.getElementById("root")!).render(
    <StrictMode>
      <App />
    </StrictMode>,
  )
})
```

**Test Strategy:** Infra-only task — 沒有 production-logic test。改用 build / type-check / dev server smoke 驗證，加 1 個既有 app shell smoke 確認 playwright 新 testDir 可運作。

**Verification:**

| Scope | Command | Expected Result | Why |
|---|---|---|---|
| Build | `cd frontend && pnpm build` | 0 errors, 0 warnings | Vite + tsc 通過 |
| Type check | `cd frontend && pnpm tsc -b --noEmit` | 0 errors | MSW handler types 與 fixtures 對齊 |
| Dev server smoke | `cd frontend && pnpm dev`，browser 開 `http://localhost:5173/` | Page load 無 console error；`<html>` 含 `class="dark"` | Vite proxy + dark class 生效 |
| MSW gated check | Browser 開 `http://localhost:5173/?msw_fixture=xss-javascript-url` | DevTools console 顯示 `[MSW] Mocking enabled`；但因為 ChatPanel 還沒掛，不會 render chat UI | URL gate 與 SW 註冊鏈路正常 |
| Playwright smoke | `cd frontend && pnpm playwright test` | 至少 app-shell.spec.ts 通過 | testDir 重整正確 |
| Vercel config sanity | `cat frontend/vercel.json` | rewrites 包含 `/api/:path*` + `REPLACE_ME_BEFORE_DEPLOY` placeholder | 部署前需要被改、但不會在 dev 影響 |

**Execution Checklist:**

- [ ] `pnpm remove @fontsource-variable/geist`
- [ ] `pnpm add @fontsource-variable/inter @fontsource-variable/jetbrains-mono @fontsource-variable/noto-sans-tc react-markdown remark-gfm`
- [ ] `pnpm dlx shadcn@latest add textarea scroll-area collapsible empty alert badge`（會更新 `package.json` + 寫入 `components/primitives/*.tsx` + 自動安裝 radix peer deps）
- [ ] `pnpm dlx msw init public/ --save`，confirm `public/mockServiceWorker.js` 產生
- [ ] 建 `frontend/src/__tests__/msw/{browser,handlers,README}.ts` + `fixtures/{types,index}.ts`
- [ ] 建 5 個 priority fixtures（依 `implementation_prerequisites_streaming_chat_ui.md` §3 範例 + §3 catalog 的 chunks 序列）
- [ ] 改 `main.tsx`、`index.html`、`vite.config.ts`、`playwright.config.ts`
- [ ] Move `frontend/e2e/app.spec.ts` → `frontend/tests/e2e/smoke/app-shell.spec.ts`，rmdir 空的 `frontend/e2e/`
- [ ] 建 `frontend/vercel.json` placeholder
- [ ] 跑 build / type check / dev server smoke / playwright smoke
- [ ] Commit：`git commit -m "feat(s3): scaffold test infrastructure (MSW, playwright dir, vite proxy, dark theme switch)"`

---

### Flow Verification: M1 dev environment ready

> Task 1.1 完成代表 dev environment + test infra 可運作。在進入 M2 之前必須通過 dev server smoke 與 playwright smoke。

| #   | Method                    | Step                                                                                              | Expected Result                                              |
| --- | ------------------------- | ------------------------------------------------------------------------------------------------- | ------------------------------------------------------------ |
| 1   | Build                     | `cd frontend && pnpm build`                                                                       | Build 通過 0 errors                                          |
| 2   | Browser                   | 開 `http://localhost:5173/`                                                                       | Page render placeholder + dark theme，無 console error      |
| 3   | Browser (MSW gated)       | 開 `http://localhost:5173/?msw_fixture=xss-javascript-url`                                        | DevTools console 顯示 `[MSW] Mocking enabled`                |
| 4   | Playwright                | `cd frontend && pnpm playwright test --grep app-shell`                                            | 1 test passed in `tests/e2e/smoke/app-shell.spec.ts`         |
| 5   | curl proxy                | `curl -i http://localhost:5173/api/v1/chat`（dev server proxy）                                    | Status 405 / 422 / 200 — 任何來自 backend 的 response（非 404） |

- [ ] All M1 flow verifications pass

---

## Milestone 2 — Foundation Libraries + Hooks（pure logic, fastest TDD）

> 這層全部是 pure function 或 hook，速度最快、最容易紅綠。先建好 `models.ts` 讓所有後續層共享 type，再做 lib/hook。順序可微調但 `models.ts` 必須先做。
>
> **TDD ground rule**：對每個 task，先 copy `implementation_test_cases.md` 對應 TC 的 test code 到 test file，跑 → 紅 → 寫 production code → 綠 → refactor → 仍綠。

### Task 2.1: `models.ts` — domain types 單檔

**Files:**

- Create: `frontend/src/models.ts`

**What & Why:** 集中所有 domain types — `ChatMessage` (re-export `UIMessage`)、`ChatStatus`、`ChatId`、`ToolCallId`、`ToolProgressMessage`、`ToolProgressRecord`、`ToolUIState`（含 `'aborted'`）、`SourceRef`、`ExtractedSources`。後續所有 lib / hook / component import 自此單檔，避免散亂。

**Implementation Notes:**

- 完整 type definitions 見 design.md「Models (`src/models.ts`)」段落
- `ToolUIState` 必須包含 `'aborted'` 作為 frontend-only 第 4 個視覺狀態（per prerequisites §6）
- `ChatStatus` 必須跟 AI SDK v6 status enum 完全一致：`'submitted' | 'streaming' | 'ready' | 'error'`

**Critical Contract / Snippet:**

```ts
import type { UIMessage } from "@ai-sdk/react"

export type ChatMessage = UIMessage
export type ChatStatus = "submitted" | "streaming" | "ready" | "error"
export type ChatId = string

export type ToolCallId = string
export type ToolProgressMessage = string
export type ToolProgressRecord = Record<ToolCallId, ToolProgressMessage>
export type ToolUIState =
  | "input-streaming"
  | "input-available"
  | "output-available"
  | "output-error"
  | "aborted"

export type SourceRef = {
  label: string
  url: string
  title?: string
  hostname: string
}
export type ExtractedSources = ReadonlyArray<SourceRef>
```

**Test Strategy:** Type-only file — 沒有 runtime test。透過後續任務 import 並 build pass 確認。

**Verification:**

| Scope | Command | Expected Result | Why |
|---|---|---|---|
| Type check | `cd frontend && pnpm tsc -b --noEmit` | 0 errors | Type 定義正確且可被 import |

**Execution Checklist:**

- [ ] 建 `frontend/src/models.ts`，貼上 design.md 對應 type 定義 + 補 `'aborted'`
- [ ] `pnpm tsc -b --noEmit` 通過
- [ ] Commit：`git commit -m "feat(s3): add domain models for chat, tool, source"`

---

### Task 2.2: `lib/error-messages.ts`（TC-unit-err-01..05）

**Files:**

- Create: `frontend/src/lib/error-messages.ts`
- Create: `frontend/src/lib/__tests__/error-messages.test.ts`

**What & Why:** `toFriendlyError(ctx) → FriendlyError` — 集中把所有 error class 翻成 user-friendly English title + retriable flag + raw detail。所有 user-facing error string 都走這個 function，禁止 component 自行寫 hardcoded error string 或顯示 backend rawMessage。14 個 mapping rows 來自 design.md「Friendly Mapping 表」（5 pre-stream-http + 1 network + 5 tool-output-error + 3 mid-stream-sse）。

**Implementation Notes:**

- Interface 完整定義見 `implementation_prerequisites_streaming_chat_ui.md` §7
- 實作為大 switch / pattern-match 函式；不做任何 i18n framework
- 不變量：`title` 永遠 ASCII printable + ≤ 80 chars + non-empty；`detail` 只在 `rawMessage` 存在時 set；`retriable` 嚴格遵守 mapping 表

**Critical Contract / Snippet:**

```ts
export type ErrorContext = {
  source: "pre-stream-http" | "mid-stream-sse" | "tool-output-error" | "network"
  status?: number
  rawMessage?: string
}
export type FriendlyError = {
  title: string
  detail?: string
  retriable: boolean
}
export function toFriendlyError(ctx: ErrorContext): FriendlyError
```

**Test Strategy:** Pure function 是最容易測的 layer — 直接表格驅動。Coverage 目標：14 個 mapping rows 各自至少 1 個 test case + 5 個 invariant tests。

| TC ID | 對應 BDD scenario | 證明什麼 |
|---|---|---|
| TC-unit-err-01 | S-err-01 (all rows) | pre-stream HTTP 422/404/409/500/5xx fallback 對應到正確 friendly title + retriable |
| TC-unit-err-02 | S-err-01 (network row) | network failure → connection lost message |
| TC-unit-err-03 | S-tool-02 | tool output rate limit / not found / timeout / permission / unknown 各自 pattern match |
| TC-unit-err-04 | S-err-05/06/07 | mid-stream context overflow / rate limit / unknown |
| TC-unit-err-05 | invariants | title 為 ASCII、≤ 80 chars、detail 只在 rawMessage 存在時 set |

**Verification:**

| Scope | Command | Expected Result | Why |
|---|---|---|---|
| Targeted | `cd frontend && pnpm test -- src/lib/__tests__/error-messages.test.ts` | All TC-unit-err-01..05 passed | Mapping table 對齊 design |
| Coverage | `pnpm test -- --coverage src/lib/error-messages.ts` | ≥ 90% statement | Pure function 應該逼近 100% |

**Execution Checklist:**

- [ ] 🔴 從 `implementation_test_cases_streaming_chat_ui.md` §1 copy TC-unit-err-01..05 完整 test code 到 `error-messages.test.ts`
- [ ] 🔴 跑 `pnpm test -- error-messages` → 確認 5 個 test groups 全部 RED（function 還沒實作）
- [ ] 🟢 寫 `lib/error-messages.ts` 把 14 個 mapping rows 翻成 switch / regex pattern；export `toFriendlyError`
- [ ] 🟢 跑 test → 全綠
- [ ] 🔵 Refactor：若 pattern match 重複，抽 helper（例如 `matchToolError(rawMessage)`）；保持 14 個 mapping rows 一目了然，邏輯來源於 design.md「Friendly Mapping 表」（SoT）
- [ ] 🔵 Re-run test → 仍綠
- [ ] Commit：`git commit -m "feat(s3): friendly error messaging library with 13-entry mapping table"`

---

### Task 2.3: `lib/error-classifier.ts`（TC-unit-classify-01）

**Files:**

- Create: `frontend/src/lib/error-classifier.ts`
- Create: `frontend/src/lib/__tests__/error-classifier.test.ts`

**What & Why:** `classifyError(err: unknown) → ErrorClass`。Smart retry routing 必須能從 `useChat.error` 物件 dispatch 到正確的 retry 路徑（422-on-regenerate 要降級為 sendMessage）。把 classification logic 放單獨 lib 避免在 ChatPanel 內 inline。

**Implementation Notes:**

- `ErrorClass` enum：`'pre-stream-422' | 'pre-stream-404' | 'pre-stream-409' | 'pre-stream-500' | 'pre-stream-5xx' | 'network' | 'mid-stream' | 'unknown'`
- 完整實作見 `implementation_prerequisites_streaming_chat_ui.md` §5
- mid-stream errors 來自 message parts，不在這個 classifier 處理（由 AssistantMessage 偵測 error part 直接走 friendly translation path）

**Critical Contract / Snippet:**

```ts
export type ErrorClass =
  | "pre-stream-422" | "pre-stream-404" | "pre-stream-409"
  | "pre-stream-500" | "pre-stream-5xx" | "network" | "mid-stream" | "unknown"

export function classifyError(err: unknown): ErrorClass
```

**Test Strategy:**

| TC ID | 證明什麼 |
|---|---|
| TC-unit-classify-01 | TypeError/fetch → 'network'；status 422/404/409/500/503 → 對應 enum；unknown → 'unknown' |

**Verification:**

| Scope | Command | Expected Result | Why |
|---|---|---|---|
| Targeted | `cd frontend && pnpm test -- src/lib/__tests__/error-classifier.test.ts` | TC-unit-classify-01 passed | Smart retry 依賴正確 classification |

**Execution Checklist:**

- [ ] 🔴 Copy TC-unit-classify-01 → `error-classifier.test.ts`，跑 → RED
- [ ] 🟢 寫 `error-classifier.ts`（pseudo-code 已在 prerequisites §5）
- [ ] 🟢 Test → 綠
- [ ] 🔵 Refactor / 🔵 Re-run → 綠
- [ ] Commit：`git commit -m "feat(s3): error classification helper for smart retry dispatch"`

---

### Task 2.4: `lib/message-helpers.ts`（TC-unit-helpers-01）

**Files:**

- Create: `frontend/src/lib/message-helpers.ts`
- Create: `frontend/src/lib/__tests__/message-helpers.test.ts`

**What & Why:** `findOriginalUserText(messages, assistantMessageId): string` — smart retry 422→sendMessage 降級時要從 message history 取回原 user text，否則 retry 不知道送什麼。獨立成 helper 是因為 ChatPanel 邏輯已經很重，這種 pure traversal 應該外移。

**Implementation Notes:**

- 邏輯：找到 assistant message 在 array 中的 index，回傳前一筆 user message 的 text part
- 完整 implementation 已在 prerequisites §5
- Edge cases：assistant 是第 0 筆 / 前一筆不是 user / messages 為空 → 回 `''`

**Test Strategy:**

| TC ID | 證明什麼 |
|---|---|
| TC-unit-helpers-01 | 正確找到 user text；邊界 case 不 throw |

**Verification:**

| Scope | Command | Expected Result | Why |
|---|---|---|---|
| Targeted | `cd frontend && pnpm test -- src/lib/__tests__/message-helpers.test.ts` | TC-unit-helpers-01 passed | Smart retry depends on this |

**Execution Checklist:**

- [ ] 🔴 Copy TC-unit-helpers-01 → test file，跑 → RED
- [ ] 🟢 實作 `findOriginalUserText`
- [ ] 🟢 Test → 綠
- [ ] 🔵 Refactor / Re-run → 綠
- [ ] Commit：`git commit -m "feat(s3): message-helpers for retrieving original user text"`

---

### Task 2.5: `lib/markdown-sources.ts` — pure function（TC-unit-md-01..07）

**Files:**

- Create: `frontend/src/lib/markdown-sources.ts`
- Create: `frontend/src/lib/__tests__/markdown-sources.test.ts`

**What & Why:** 純函式 `extractSources(text: string) → ExtractedSources`，走訪 markdown AST 把 reference definition `[1]: url "title"` 抽出為 `ExtractedSources`。**僅在 streaming 結束後由 AssistantMessage 用 `useMemo` 呼叫一次**（per defer-to-ready 策略）— streaming 期間完全不 parse，reference 在文字內顯示為純 `[1]` 字面文字。

> **策略變更說明**：原設計想把 extraction 做成 unified plugin 掛到 react-markdown plugin chain，但 react-markdown 不暴露 `file.data`，無法 propagate extracted sources 回 React 層。新策略不再寫 unified plugin，而是 standalone pure function：streaming 期間 `<Markdown>` 只掛 `remarkGfm` 做純 render、不碰 sources；stream 結束後 AssistantMessage 對 concatenated text 算一次 `extractSources` 拿到結果。這個方案同時解掉「雙 parse perf」與「AssistantMessage stateless 違反」兩個 delta。

**Implementation Notes:**

- Pure function 簽名：`export function extractSources(markdown: string): ExtractedSources`
- **不需要**寫 unified plugin — 單一純函式 + 自己用 `remark-parse` 或 `mdast-util-from-markdown` 走一次 AST 即可
- **核心不變量**（design.md / Q-USR-8/9/11）：
  1. **First-wins dedup**：同 label 多個 def 時保留第一個（避免兩個 `id="src-1"` collision）
  2. **Scheme allowlist**：只放行 `http(s):`，過濾 `javascript:` / `data:` / `mailto:` / `file:` / `vbscript:`（**security critical**）
  3. **Orphan handling**：def orphan（無 body ref）保留；body orphan（無 def）不出現在 result
  4. **Numeric label sort**：依 `parseInt(label)` 排序，不是 arrival order
  5. **Robust to malformed input**：partial / malformed URL / missing scheme / open quote 不 throw（防守邏輯，即使 stream 中斷 text 不完整也能安全 parse）

**Critical Contract / Snippet:**

```ts
import type { ExtractedSources, SourceRef } from "@/models"

export function extractSources(markdown: string): ExtractedSources
```

**Test Strategy:** 7 個 unit tests 各自 cover 一個 invariant：

| TC ID | 對應 BDD scenario | 證明什麼 |
|---|---|---|
| TC-unit-md-01 | S-md-01 row 1 | 抽取單一 reference + title 屬性 |
| TC-unit-md-02 | S-md-01 row 2 | hostname fallback when title missing |
| TC-unit-md-03 | S-md-02 | first-wins dedup |
| TC-unit-md-04 | S-md-03 | **security**: scheme allowlist 拒絕 javascript/data/mailto/file/vbscript |
| TC-unit-md-05 | _internal invariant_ | malformed / partial URL 不 throw（defensive，防 stream 中斷時 text 不完整）|
| TC-unit-md-06 | S-md-05 | orphan body ref 不出現；orphan def 仍出現 |
| TC-unit-md-07 | _internal invariant_ | numeric label sort（stable final ordering）|

**Verification:**

| Scope | Command | Expected Result | Why |
|---|---|---|---|
| Targeted | `cd frontend && pnpm test -- src/lib/__tests__/markdown-sources.test.ts` | All 7 TC-unit-md-* passed | 7 個不變量都成立 |
| Security | `pnpm test -- markdown-sources --grep "security: scheme allowlist"` | 5 個 evil scheme 全被 filter | XSS 第一道防線 |

**Execution Checklist:**

- [ ] 🔴 Copy TC-unit-md-01..07 完整 test code（從 `implementation_test_cases_streaming_chat_ui.md` §1）→ test file，跑 → RED
- [ ] 🟢 建 `markdown-sources.ts`：實作 `extractSources` 純函式（**無 unified plugin**）
  - 用 `remark-parse` 解析 markdown 為 AST
  - 走訪 `definition` nodes
  - First-wins dedup 用 `Map<label, SourceRef>` 配合 `if (!map.has(label)) map.set(...)`
  - Scheme allowlist 用 `try { new URL(url) }` + `urlObj.protocol === 'http:' || 'https:'`
  - Numeric sort：`Array.from(map.values()).sort((a,b) => parseInt(a.label) - parseInt(b.label))`
  - Body orphan filter：先 collect body 中的 ref labels，再 intersect with def labels
- [ ] 🟢 Test → 7 個全綠
- [ ] 🔵 Refactor：抽 helper functions（`isAllowedUrl`、`parseDefinitionTitle`），保持每個 invariant 邏輯獨立可讀
- [ ] 🔵 Re-run → 仍綠
- [ ] Commit：`git commit -m "feat(s3): markdown-sources pure function extractor with security guards (XSS, dedup, orphan)"`

---

### Task 2.6: `lib/typing-indicator-logic.ts`（TC-comp-typing-01 truth table）

**Files:**

- Create: `frontend/src/lib/typing-indicator-logic.ts`
- Create: `frontend/src/components/templates/__tests__/MessageList.test.tsx`（partial — 只先寫 truth table 測試；其他 MessageList tests 在 M4 補）

> **Note**：TC-comp-typing-01 從 test cases 文件看像是 component test，但實際上是 pure function truth table。Test file 物理位置可放在 `MessageList.test.tsx` 內或自家 `lib/__tests__/typing-indicator-logic.test.ts`。Test cases doc 註明「位置取決於 visibility logic 在哪一層」— 本 plan 採前者：function 在 lib，test 從 MessageList test file 用 import 呼叫。原因是 MessageList 是唯一 consumer，集中在它的 test file 內 reader 一目了然 visibility 邏輯歸屬。

**What & Why:** TypingIndicator visibility 是 derived state — 由 `(status, lastMessage)` 決定。把它寫成 pure function 而不是 inline 在 component 內，便於 truth table 測試 + 重用。

**Implementation Notes:**

- 完整 truth table 與 derivation 邏輯見 design.md「Thinking Indicator Trigger」flowchart
- 邏輯精簡：
  - status === 'ready' / 'error' → false
  - lastMessage 不存在或 role !== 'assistant' → true
  - assistant message has any rendered part (text / tool / error) → false
  - assistant message no parts → true

**Critical Contract / Snippet:**

```ts
import type { ChatStatus } from "@/models"
import type { UIMessage } from "@ai-sdk/react"

export function shouldShowTypingIndicator(args: {
  status: ChatStatus
  lastMessage: UIMessage | null
}): boolean
```

**Test Strategy:** Single test file 含 1 個 `describe` + 1 個 `test.each(cases)` truth table。

| TC ID | 對應 BDD scenarios | 證明什麼 |
|---|---|---|
| TC-comp-typing-01 | S-stream-06/07/08, Rule 1.2 | Truth table 7 cases 全綠 |

**Verification:**

| Scope | Command | Expected Result | Why |
|---|---|---|---|
| Targeted | `cd frontend && pnpm test -- typing-indicator` | 7 個 truth table cases 全綠 | 對應 7 個邏輯分支 |

**Execution Checklist:**

- [ ] 🔴 從 test cases doc copy TC-comp-typing-01 truth table → 暫放 `lib/__tests__/typing-indicator-logic.test.ts`（M4 MessageList 測試完成後再決定是否合併）
- [ ] 🔴 跑 → RED（function 還沒寫）
- [ ] 🟢 寫 `typing-indicator-logic.ts` derivation 函式
- [ ] 🟢 Test → 綠
- [ ] 🔵 Refactor / Re-run → 綠
- [ ] Commit：`git commit -m "feat(s3): TypingIndicator visibility derivation pure function"`

---

### Task 2.7: `hooks/useToolProgress.ts`（TC-hook-progress-01..03）

**Files:**

- Create: `frontend/src/hooks/useToolProgress.ts`
- Create: `frontend/src/hooks/__tests__/useToolProgress.test.ts`

**What & Why:** Hook 維護 `Record<ToolCallId, ToolProgressMessage>` state，提供 `handleData` callback（給 useChat `onData` 用）+ `clearProgress` 方法（清空 state，給 ChatPanel clear/regenerate 使用）。獨立 hook 讓 ChatPanel 不必直接管 progress map state，也讓單元測試容易。

**Implementation Notes:**

- 用 `useState<Record<ToolCallId, string>>({})`，更新時 `setProgress(prev => ({ ...prev, [id]: msg }))` — **必須用 functional setState** 防止 stale closure（TC-hook-progress-02 專測這點）
- `handleData` 接受 `{ id, data: { message } }` shape（對應 `data-tool-progress` chunk）
- 不訂閱 chatId — reset 由 ChatPanel 顯式呼叫 `clearProgress`（per design.md）

**Critical Contract / Snippet:**

```ts
export function useToolProgress() {
  const [toolProgress, setProgress] = useState<ToolProgressRecord>({})
  const handleData = useCallback((chunk: { id: string; data: { message: string } }) => {
    setProgress(prev => ({ ...prev, [chunk.id]: chunk.data.message }))
  }, [])
  const clearProgress = useCallback(() => setProgress({}), [])
  return { toolProgress, handleData, clearProgress }
}
```

**Test Strategy:**

| TC ID | 對應 BDD scenario | 證明什麼 |
|---|---|---|
| TC-hook-progress-01 | S-tool-05 + Dev #5 | parallel routing isolation：tc-A 不污染 tc-B |
| TC-hook-progress-02 | S-tool-04 + Dev #7 | functional setState：rapid 3 updates 結果是第 3 次（防 stale closure） |
| TC-hook-progress-03 | S-clear-01 | clearProgress 把 record 清空 |

**Verification:**

| Scope | Command | Expected Result | Why |
|---|---|---|---|
| Targeted | `cd frontend && pnpm test -- src/hooks/__tests__/useToolProgress.test.ts` | 3 tests passed | parallel isolation + stale-closure guard |

**Execution Checklist:**

- [ ] 🔴 Copy TC-hook-progress-01..03 → test file，跑 → RED
- [ ] 🟢 寫 hook（functional setState 不可遺漏）
- [ ] 🟢 Test → 綠
- [ ] 🔵 Refactor / Re-run → 綠
- [ ] Commit：`git commit -m "feat(s3): useToolProgress hook with functional setState isolation"`

---

### Task 2.8: `hooks/useFollowBottom.ts`（TC-hook-followbottom-01）

**Files:**

- Create: `frontend/src/hooks/useFollowBottom.ts`
- Create: `frontend/src/hooks/__tests__/useFollowBottom.test.ts`

**What & Why:** Hook 維護 `shouldFollowBottom: boolean` + 提供 `handleScroll` (依 100px threshold 決定是否貼底) + `forceFollowBottom` (Send 按鈕觸發強制貼底，per Q-USR-10)。獨立 hook 是為了把 scroll 純邏輯從 MessageList 分離 + 易於測試。

**Implementation Notes:**

- 100px threshold：`distance = scrollHeight - scrollTop - clientHeight`，`distance < 100` → following
- `forceFollowBottom()` setter 一律設 `true`（user 主動 send 時 prevailing intent，per Q-USR-10）
- Hook 接受 `ref: RefObject<HTMLElement | null>`，內部讀 ref.current 的 scroll metrics
- 不要直接 attach scroll listener — 把 `handleScroll` return 出去由 MessageList 在 `onScroll` prop 上掛上

**Critical Contract / Snippet:**

```ts
export function useFollowBottom(ref: RefObject<HTMLElement | null>) {
  const [shouldFollowBottom, setShouldFollow] = useState(true)
  const handleScroll = useCallback(() => {
    const el = ref.current
    if (!el) return
    const distance = el.scrollHeight - el.scrollTop - el.clientHeight
    setShouldFollow(distance < 100)
  }, [ref])
  const forceFollowBottom = useCallback(() => setShouldFollow(true), [])
  return { shouldFollowBottom, handleScroll, forceFollowBottom }
}
```

**Test Strategy:**

| TC ID | 對應 BDD scenario | 證明什麼 |
|---|---|---|
| TC-hook-followbottom-01 | S-scroll-01..04 | within 100px → true；> 100px → false；forceFollowBottom 強制 true |

**Verification:**

| Scope | Command | Expected Result | Why |
|---|---|---|---|
| Targeted | `cd frontend && pnpm test -- src/hooks/__tests__/useFollowBottom.test.ts` | 3 cases passed | 100px threshold + force override |

**Execution Checklist:**

- [ ] 🔴 Copy TC-hook-followbottom-01 → test file，跑 → RED
- [ ] 🟢 寫 hook
- [ ] 🟢 Test → 綠
- [ ] 🔵 Refactor / Re-run → 綠
- [ ] Commit：`git commit -m "feat(s3): useFollowBottom hook with 100px threshold + force override"`

---

### Flow Verification: M2 foundation libraries ready

> Tasks 2.1–2.8 完成後，所有 pure logic + hooks 都有 test 守護。後續 M3+ 的 component layer 可以放心 import 這些 lib / hook。

| #   | Method  | Step                                               | Expected Result                                                       |
| --- | ------- | -------------------------------------------------- | --------------------------------------------------------------------- |
| 1   | Vitest  | `cd frontend && pnpm test -- src/lib src/hooks`    | 全部 unit + hook tests 通過                                             |
| 2   | Coverage | `pnpm test -- --coverage src/lib src/hooks`        | lib ≥ 90%、hooks ≥ 80% statement                                       |
| 3   | Type check | `pnpm tsc -b --noEmit`                            | 0 errors                                                                |

- [ ] All M2 flow verifications pass

---

## Milestone 3 — Atoms + Molecules + Theme Rewrite

### Task 3.1: `index.css` 主題與字型完整重寫

**Files:**

- Update: `frontend/src/index.css` — fonts imports、`.dark` scope full S3 vars

**What & Why:** S2 scaffold 的 `.dark` 是 shadcn neutral default，跟 mockup S3 設計差距大。把字型 import 換掉、`.dark` scope 改成 design.md 指定的完整 oklch 變數（含 `--chat-brand-accent` / `--status-*` / `--chat-fg-*` 一系列 chat-specific extension）。`:root` 保留 shadcn light 預設不動（為 V2 toggle 預留結構）。

**Implementation Notes:**

- 完整 CSS 變數值見 design.md「CSS Variables 完整定義」
- 字型 imports：`@import "@fontsource-variable/inter"; @import "@fontsource-variable/jetbrains-mono"; @import "@fontsource-variable/noto-sans-tc";`（移除 geist）
- Tailwind v4 `@theme` 區塊新增 `--font-sans`、`--font-mono` 對應 Inter / JetBrains Mono / Noto Sans TC fallback chain
- 既有 `:root` light theme values 保留不動（design 決議 A2）

**Test Strategy:** CSS-only — 沒有 unit test。靠 dev server visual inspection + 後續 atoms / molecules 測試的 className matchers 間接驗證。

**Verification:**

| Scope | Command | Expected Result | Why |
|---|---|---|---|
| Build | `pnpm build` | Build 通過，無 unknown CSS variable warning | Tailwind v4 解析正確 |
| Browser | `pnpm dev`，開 `http://localhost:5173/` | Body bg 明顯為深藍黑色（不是純黑或白），fonts 不再是 Geist | `.dark` scope 與字型生效 |

**Execution Checklist:**

- [ ] 改 `src/index.css` font imports + `.dark` scope
- [ ] Build + dev server smoke
- [ ] Commit：`git commit -m "feat(s3): rewrite dark theme CSS variables and font stack"`

---

### Task 3.2: Atoms（StatusDot / RefSup / Cursor / TypingIndicator / PromptChip / RegenerateButton）

**Files:**

- Create: `frontend/src/components/atoms/StatusDot.tsx`
- Create: `frontend/src/components/atoms/RefSup.tsx`
- Create: `frontend/src/components/atoms/Cursor.tsx`
- Create: `frontend/src/components/atoms/TypingIndicator.tsx`
- Create: `frontend/src/components/atoms/PromptChip.tsx`
- Create: `frontend/src/components/atoms/RegenerateButton.tsx`

**What & Why:** 6 個 atoms 是 leaf or trivial wrappers — 結構單純，但每個都有強制的 DOM contract（per prerequisites §1）。把 6 個放同一個 task 是因為彼此獨立、無 cross-component test 需求；分太細會堆 commit overhead。

**Implementation Notes — DOM Contracts**（必填，per prerequisites §1）:

| Component | DOM contract |
|---|---|
| `StatusDot` | `<span data-testid="status-dot" data-status-state="running\|success\|error\|aborted">`；`aborted` 必須**沒有** `animate-pulse` class（不變量） |
| `RefSup` | `<sup data-testid="ref-sup" data-ref-label={label}><a href={href}>` |
| `Cursor` | `<span data-testid="cursor">` |
| `TypingIndicator` | `<div data-testid="typing-indicator">` 含 3 個 pulsing dots |
| `PromptChip` | `<button data-testid="prompt-chip" data-chip-index={index} aria-label={chipText}>`；trivial wrapper of shadcn `Button` + lucide icon + text |
| `RegenerateButton` | `<button data-testid="regenerate-btn" aria-label="Regenerate response">`；trivial wrapper of `Button` (ghost variant) + `RefreshCw` icon + text |

**Critical Contract / Snippet:**

```tsx
// StatusDot.tsx — 不變量 demo
import { cn } from "@/lib/utils"
export function StatusDot({ state }: { state: "running" | "success" | "error" | "aborted" }) {
  return (
    <span
      data-testid="status-dot"
      data-status-state={state}
      className={cn(
        "h-2 w-2 rounded-full",
        state === "running" && "bg-[var(--status-running)] animate-pulse",
        state === "success" && "bg-[var(--status-success)]",
        state === "error" && "bg-[var(--status-error)]",
        state === "aborted" && "bg-[var(--status-aborted)]", // **無 animate-pulse**
      )}
    />
  )
}
```

**Test Strategy:** 6 個 atoms 大多 trivial — 不為每個 atom 寫獨立 test file。它們的 behavior 在 ToolCard / Composer / EmptyState / AssistantMessage 的 component test 中**間接驗證**（透過 DOM contract assertion）。**例外**：StatusDot 的「aborted 不 pulse」不變量在 TC-comp-toolcard-01 的「isAborted=true」case 已被驗。

> **此 task 不寫獨立 atom test**。Test discipline 由 M4 organism tests 反向 enforce — 若 atom DOM contract 寫錯，組裝它的 organism 一定 RED。

**Verification:**

| Scope | Command | Expected Result | Why |
|---|---|---|---|
| Type check | `pnpm tsc -b --noEmit` | 0 errors | Atoms props types 正確 |
| Build | `pnpm build` | 0 errors | tree-shaking 後 atoms 都被使用 |

**Execution Checklist:**

- [ ] 寫 6 個 atoms，**嚴格遵守上方 DOM contract 表**（每個 testid / data-* attr 都要對）
- [ ] StatusDot 的 `aborted` className 不可含 `animate-pulse`（人工 review 一次）
- [ ] PromptChip / RegenerateButton 是 trivial wrappers — 不重新做 shadcn Button styling，直接 `<Button variant="ghost" {...props}>...`
- [ ] Type check + build
- [ ] Commit：`git commit -m "feat(s3): 6 atoms (StatusDot, RefSup, Cursor, TypingIndicator, PromptChip, RegenerateButton)"`

---

### Task 3.3: Molecules（SourceLink / ToolRow / ToolDetail / UserMessage / Sources）

**Files:**

- Create: `frontend/src/components/molecules/SourceLink.tsx`
- Create: `frontend/src/components/molecules/ToolRow.tsx`
- Create: `frontend/src/components/molecules/ToolDetail.tsx`
- Create: `frontend/src/components/molecules/UserMessage.tsx`
- Create: `frontend/src/components/molecules/Sources.tsx`
- Create: `frontend/src/components/molecules/__tests__/Sources.test.tsx`

**What & Why:** 5 個 molecules 全部是 stateless 結構性組合（無 hook、無 logic）— `(props) => JSX`。Sources molecule 因為涉及到 sources block 的 anchor id 生成 + scheme defense（雙層 XSS guard），單獨寫 component test。其餘 4 個 molecules 在 organism layer test 間接驗證。

**Implementation Notes — DOM Contracts:**

| Component | DOM contract |
|---|---|
| `SourceLink` | `<div data-testid="source-link" data-source-label={label} id={'src-' + label}>...<a>` — anchor 必須有 `id="src-{label}"` 供 RefSup 跳轉 |
| `ToolRow` | (child of ToolCard, no separate testid) |
| `ToolDetail` | Root `<div data-testid="tool-detail">`；INPUT `<pre data-testid="tool-input-json">`；OUTPUT `<pre data-testid="tool-output-json">`；ERROR `<pre data-testid="tool-error-detail">` |
| `UserMessage` | `<div data-testid="user-bubble">` |
| `Sources` | `<section data-testid="sources-block">` 包多個 `SourceLink` |

**Critical Contract / Snippet:**

```tsx
// Sources.tsx — anchor id 與 XSS 第二道防線
import type { ExtractedSources } from "@/models"
export function Sources({ sources }: { sources: ExtractedSources }) {
  const safe = sources.filter(s => /^https?:/.test(s.url)) // defensive 第二層
  return (
    <section data-testid="sources-block" className="mt-4 ...">
      <h4>SOURCES</h4>
      <ul>
        {safe.map(s => (
          <li key={s.label} data-testid="source-link" data-source-label={s.label} id={`src-${s.label}`}>
            <a href={s.url} target="_blank" rel="noopener noreferrer">
              {s.title ?? s.hostname}
            </a>
          </li>
        ))}
      </ul>
    </section>
  )
}
```

**Test Strategy:**

| TC ID | 對應 BDD scenario | Subject | 證明什麼 |
|---|---|---|---|
| TC-comp-sources-01 | S-md-01 | Sources molecule | title / hostname fallback；anchor `id="src-{label}"` 存在 |
| TC-comp-sources-02 | S-md-03 (security) | Sources molecule | XSS 第二道防線：javascript: URL 不出現在 DOM |

**Verification:**

| Scope | Command | Expected Result | Why |
|---|---|---|---|
| Targeted | `cd frontend && pnpm test -- src/components/molecules/__tests__/Sources.test.tsx` | 2 tests passed | Sources fallback + XSS defensive layer |

**Execution Checklist:**

- [ ] 🔴 寫 5 個 molecules（嚴守 DOM contract）；先 stub 內容讓 type check 通過
- [ ] 🔴 Copy TC-comp-sources-01/02 → `Sources.test.tsx`，跑 → RED
- [ ] 🟢 完成 `Sources.tsx` 實作（含 scheme filter）
- [ ] 🟢 Test → 綠
- [ ] 🔵 Refactor 5 個 molecules，確保 SourceLink anchor id 對齊 + ToolDetail 的 pre code 用 mono font
- [ ] 🔵 Re-run Sources test → 綠
- [ ] Commit：`git commit -m "feat(s3): 5 molecules (Sources with XSS defensive layer + anchor ids)"`

---

### Flow Verification: M3 atoms + molecules dev preview

> M3 完成後 atoms / molecules 還無法獨立 render（需要 organism wire），但 type check 與部分 component test 已能跑。可以用一個 ad hoc dev playground page 渲染幾個 atom / molecule 做 visual smoke。

| #   | Method     | Step                                                                | Expected Result                                  |
| --- | ---------- | ------------------------------------------------------------------- | ------------------------------------------------ |
| 1   | Type check | `pnpm tsc -b --noEmit`                                              | 0 errors                                         |
| 2   | Vitest     | `pnpm test -- src/components/molecules/__tests__/Sources.test.tsx`  | TC-comp-sources-01/02 passed                     |
| 3   | Browser    | `pnpm dev`，開 `http://localhost:5173/`（仍 placeholder shell）        | Page render + dark theme，無 console error      |

- [ ] All M3 flow verifications pass

---

## Milestone 4 — Organisms + Template

### Task 4.1: `ChatHeader` organism（TC-comp-header-01）

**Files:**

- Create: `frontend/src/components/organisms/ChatHeader.tsx`
- Create: `frontend/src/components/organisms/__tests__/ChatHeader.test.tsx`

**What & Why:** 品牌標題 + v1 badge + `"Clear conversation"` button（empty state 時 disabled）。最簡單的 organism — 沒有 hook，只接 `{ onClear, messagesEmpty }` props。

**DOM contract:**

- Root: `<header data-testid="chat-header">`
- Clear button: `<button data-testid="composer-clear-btn" aria-label="Clear conversation" disabled={messagesEmpty}>`
- 用 shadcn `Button` + `Badge` primitives

**Test Strategy:**

| TC ID | 證明什麼 |
|---|---|
| TC-comp-header-01 | empty 時 disabled、非 empty 時 enabled、click 觸發 onClear |

**Verification:**

| Scope | Command | Expected Result | Why |
|---|---|---|---|
| Targeted | `pnpm test -- ChatHeader` | TC-comp-header-01 passed | empty-state guard |

**Execution Checklist:**

- [ ] 🔴 Copy TC-comp-header-01 → test file，跑 → RED
- [ ] 🟢 寫 `ChatHeader.tsx`（用 shadcn Button + Badge，接 props）
- [ ] 🟢 Test → 綠
- [ ] 🔵 Refactor / Re-run → 綠
- [ ] Commit：`git commit -m "feat(s3): ChatHeader organism with disabled-when-empty clear button"`

---

### Task 4.2: `Markdown` organism

**Files:**

- Create: `frontend/src/components/organisms/Markdown.tsx`

**What & Why:** Wrap `react-markdown` 接 `remarkGfm`，接收 **pre-extracted sources** prop，提供 component override 把 reference link 轉成 `<RefSup>`（僅在 sources 已就位時；streaming 期間 sources 為空、reference 保留為純 `[N]` 字面文字）。Streaming cursor 以 sibling `<Cursor />` 渲染。Markdown 不寫獨立 component test — 行為由 AssistantMessage component test (TC-comp-assistant-01) 涵蓋。

> **策略變更**：原設計在 Markdown 內部自己 `extractSources(text)` 再 callback up。新策略把 extraction 上移到 AssistantMessage（透過 `useMemo` 只在 `isStreaming === false` 時算一次），Markdown 退化為純 presentational component — 無 state、無 effect、無 callback。這解掉 design.md「Markdown 無 state」的違反、省掉 streaming 中雙 parse overhead。

**Implementation Notes:**

- Props: `{ text: string; isStreaming: boolean; sources: ExtractedSources }`
- 不再 call `extractSources`，也不再有 `onExtractedSources` callback
- 不再需要「minimal plugin 移除 definition node」— streaming 期間 definition line 本來就會 render 出來；但因為 LLM 的 reference definition 是放在 text 末尾（per Q3 markdown format），streaming 中短暫 render 成 raw 文字是可接受的。stream 結束 AssistantMessage 算出 sources 後，Markdown 拿到 `sources.length > 0` 的 prop，component override `a` 會把 `[N]` 升級為 `<RefSup>`；此時 definition 文字仍會顯示 — 需要額外處理（見下）
- **Definition 隱藏機制**：當 `sources.length > 0` 時，AssistantMessage 把原始 text 的 definition 行 strip 掉再 pass 給 Markdown（簡單 regex `/^\[[0-9]+\]:\s+\S+.*$/gm` 即可；或者 split by line 過濾）。streaming 中不 strip（text 還沒完成），所以 definition 暫時以純文字顯示
- Component override：`{ a: ({ href, children }) => /* 若 href 對應 sources 裡的 label → <RefSup label={...} href={#src-${label}} /> 否則一般 anchor */ }`
- Streaming 中的 cursor 為 `{isStreaming && <Cursor />}` sibling 渲染（block-level placement，user 已 V1 接受 — 偏離 design「inline at end of text」但實作簡單，視覺差異侷限於 streaming 中含 table 的 case）

**Critical Contract / Snippet:**

```tsx
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import { RefSup } from "@/components/atoms/RefSup"
import { Cursor } from "@/components/atoms/Cursor"
import type { ExtractedSources } from "@/models"

export function Markdown({
  text,
  isStreaming,
  sources,
}: {
  text: string
  isStreaming: boolean
  sources: ExtractedSources
}) {
  const labelToSource = useMemo(
    () => new Map(sources.map((s) => [s.label, s])),
    [sources],
  )

  return (
    <div className="prose prose-invert ...">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          a: ({ href, children }) => {
            const label = labelToSource.has(String(children)) ? String(children) : null
            return label
              ? <RefSup label={label} href={`#src-${label}`} />
              : <a href={href}>{children}</a>
          },
        }}
      >
        {text}
      </ReactMarkdown>
      {isStreaming && <Cursor />}
    </div>
  )
}
```

**Test Strategy:** 不寫獨立 test — 行為由 lib unit test + AssistantMessage component test 涵蓋。

**Verification:**

| Scope | Command | Expected Result | Why |
|---|---|---|---|
| Type check | `pnpm tsc -b --noEmit` | 0 errors | Markdown prop types 正確 |

**Execution Checklist:**

- [ ] 寫 `Markdown.tsx`（stateless presentational component）
- [ ] Type check
- [ ] Commit：`git commit -m "feat(s3): Markdown organism as stateless renderer with pre-extracted sources"`

---

### Task 4.3: `ToolCard` organism（TC-comp-toolcard-01..02）

**Files:**

- Create: `frontend/src/components/organisms/ToolCard.tsx`
- Create: `frontend/src/components/organisms/__tests__/ToolCard.test.tsx`

**What & Why:** 4 狀態 card（running / success / error / aborted）+ expand/collapse via shadcn `Collapsible`。`isAborted` 是來自 ChatPanel 的 frontend-only 第 4 個視覺狀態 override（per prerequisites §6）。

**DOM contract:**

- Root: `<div data-testid="tool-card" data-tool-call-id={toolCallId} data-tool-state={visualState}>`
- Expand: `<button data-testid="tool-card-expand" aria-expanded={isOpen} aria-label="Toggle tool details">`
- Status dot: 透過 `StatusDot` atom（已含 testid）
- Detail: 透過 `ToolDetail` molecule（已含 testid）

**Implementation Notes:**

- Props: `{ part: ToolUIPart; isAborted: boolean; progressText?: string }`
- `visualState = isAborted && part.state === 'input-available' ? 'aborted' : part.state`
- 用 shadcn `Collapsible` (Trigger + Content)，state 由 `Collapsible` 內部處理 — 不要自行 `useState<boolean>`
- Tool error 顯示時 **不** 顯示 backend rawMessage，改 call `toFriendlyError({ source: 'tool-output-error', rawMessage: part.errorText })` 取 friendly title
- aborted 狀態：StatusDot 自動無 pulse（atom 處理）；label 顯示 `Aborted`，無 progress text；INPUT 仍可展開
- expand state 依賴 `Collapsible` 內部 state — re-render 時要 stable，所以 ToolCard 在 parent 中必須用 `key={toolCallId}` 確保 re-mount-free

**Critical Contract / Snippet:**

```tsx
import { Collapsible, CollapsibleTrigger, CollapsibleContent } from "@/components/primitives/collapsible"
import { StatusDot } from "@/components/atoms/StatusDot"
import { ToolRow } from "@/components/molecules/ToolRow"
import { ToolDetail } from "@/components/molecules/ToolDetail"
import { toFriendlyError } from "@/lib/error-messages"

export function ToolCard({ part, isAborted, progressText }: ToolCardProps) {
  const visualState =
    isAborted && part.state === "input-available" ? "aborted" : part.state

  const friendly =
    part.state === "output-error"
      ? toFriendlyError({ source: "tool-output-error", rawMessage: part.errorText })
      : null

  return (
    <Collapsible asChild>
      <div
        data-testid="tool-card"
        data-tool-call-id={part.toolCallId}
        data-tool-state={visualState}
      >
        <ToolRow visualState={visualState} toolName={part.toolName} progressText={progressText} friendlyTitle={friendly?.title} />
        <CollapsibleTrigger
          data-testid="tool-card-expand"
          aria-label="Toggle tool details"
        >
          {/* chevron */}
        </CollapsibleTrigger>
        <CollapsibleContent>
          <ToolDetail
            input={part.input}
            output={"output" in part ? part.output : undefined}
            errorDetail={part.state === "output-error" ? part.errorText : undefined}
          />
        </CollapsibleContent>
      </div>
    </Collapsible>
  )
}
```

**Test Strategy:**

| TC ID | 對應 BDD scenario | 證明什麼 |
|---|---|---|
| TC-comp-toolcard-01 | S-tool-01/02, S-err-07 | 4 個視覺狀態 reflect 在 `data-tool-state` 與 status dot；error 顯示 friendly text 而非 raw |
| TC-comp-toolcard-02 | S-tool-07/09, Dev #8 | expand state 在 parent re-render 中穩定（Collapsible 內部 state，stable key） |

**Verification:**

| Scope | Command | Expected Result | Why |
|---|---|---|---|
| Targeted | `pnpm test -- ToolCard` | TC-comp-toolcard-01/02 passed | 4-state machine + expand stability |

**Execution Checklist:**

- [ ] 🔴 Copy TC-comp-toolcard-01/02 → test file，跑 → RED
- [ ] 🟢 寫 `ToolCard.tsx`（用 Collapsible + ToolRow + ToolDetail，friendly error inline）
- [ ] 🟢 Test → 全綠
- [ ] 🔵 Refactor：把 visualState derivation 抽 helper 提升可讀性
- [ ] 🔵 Re-run → 綠
- [ ] Commit：`git commit -m "feat(s3): ToolCard organism with 4 visual states (incl. aborted override)"`

---

### Task 4.4: `AssistantMessage` organism（TC-comp-assistant-01..03）

**Files:**

- Create: `frontend/src/components/organisms/AssistantMessage.tsx`
- Create: `frontend/src/components/organisms/__tests__/AssistantMessage.test.tsx`

**What & Why:** AssistantMessage 是 parts dispatcher — 走訪 `UIMessage.parts` 把每個 part dispatch 到對應子元件（Markdown / ToolCard / ErrorBlock / Sources）。同時控制 RegenerateButton visibility（last + status=ready 時顯示，per Q-USR-1）。

**DOM contract:**

- Root: `<article data-testid="assistant-message">`
- 內含 `<sections>` 給 markdown / tool cards / sources / error block / regenerate button

**Implementation Notes:**

- Props: `{ message: UIMessage; isLast: boolean; status: ChatStatus; abortedTools: Set<ToolCallId>; toolProgress: ToolProgressRecord; onRegenerate: (messageId: string) => void }`
- Parts dispatch：
  - `text` → 累積成 single Markdown render（避免每個 text part 各自 render 造成多段 markdown）
  - `tool` → ToolCard with `isAborted = abortedTools.has(part.toolCallId)`
  - `error` → inline ErrorBlock（mid-stream variant）；保留前面 partial 的 text / tool parts（per S-err-05/06/07）
- Sources block：用 Markdown `onExtractedSources` callback 收到的 sources 渲染在 markdown 後面
- RegenerateButton 顯示條件：`isLast && status === 'ready'`（per TC-comp-assistant-03）
- aborted only 影響 `input-available` tools — terminal state 不該被 override（per TC-comp-assistant-02）

**Critical Contract / Snippet:**

```tsx
export function AssistantMessage({
  message,
  isLast,
  status,
  abortedTools,
  toolProgress,
  onRegenerate,
}: AssistantMessageProps) {
  // 串流期間把 text parts 串起來
  const concatenatedText = message.parts
    .filter(p => p.type === "text")
    .map(p => (p as TextUIPart).text)
    .join("")

  // streaming 為 true 時 stream 還沒結束；任何非 streaming 狀態視為可 extract（包含 error 終態）
  const isStreaming = status === "streaming" && isLast

  // Defer-to-ready extraction：streaming 中不碰 sources，stream 結束才算一次
  const extractedSources = useMemo<ExtractedSources>(
    () => (isStreaming ? [] : extractSources(concatenatedText)),
    [isStreaming, concatenatedText],
  )

  // 若已抽出 sources，strip 掉 text 中的 definition 行，避免 Markdown render 出來
  const displayText = useMemo(
    () =>
      extractedSources.length > 0
        ? concatenatedText.replace(/^\[[0-9]+\]:\s+\S+.*$/gm, "").replace(/\n{3,}/g, "\n\n")
        : concatenatedText,
    [concatenatedText, extractedSources.length],
  )

  return (
    <article data-testid="assistant-message">
      {message.parts.map((part, idx) => {
        if (part.type === "tool") {
          const isAborted =
            part.state === "input-available" && abortedTools.has(part.toolCallId)
          return (
            <ToolCard
              key={part.toolCallId}
              part={part}
              isAborted={isAborted}
              progressText={toolProgress[part.toolCallId]}
            />
          )
        }
        if (part.type === "error") {
          return <ErrorBlock key={idx} ... source="mid-stream" />
        }
        return null // text 由 displayText 統一 render
      })}
      {displayText && (
        <Markdown
          text={displayText}
          isStreaming={isStreaming}
          sources={extractedSources}
        />
      )}
      {extractedSources.length > 0 && <Sources sources={extractedSources} />}
      {isLast && status === "ready" && (
        <RegenerateButton onRegenerate={() => onRegenerate(message.id)} />
      )}
    </article>
  )
}
```

**Defer-to-ready extraction 策略說明**：

- Streaming 期間 `isStreaming === true`，`extractedSources` 為 `[]`，`displayText === concatenatedText`，Markdown render 原始 text（含 `[1]: url "title"` 定義行）；reference `[N]` 為純文字不是 RefSup
- Stream 結束（status 從 `streaming` 轉為 `ready`，或 mid-stream error 使 streaming 停止）時 `isStreaming` 變 `false`，`useMemo` recomputes sources，`displayText` strip 掉 definition 行，Markdown 重 render — reference `[N]` 升級為可點 RefSup、底部出現 Sources block
- 一次性 extraction 直接解掉「雙 parse perf」與「AssistantMessage stateless 違反」兩個 delta
- Mid-stream error 場景（S-err-05）：已接收的 partial text + 已抽到的 sources 都會在 error 到達時一次性 extract — 保留 S-err-05 的「preserve partial sources」行為
- Stop 場景（S-stop-01）：使用者按 stop 後 status → `ready`，同樣觸發 extraction，partial text 中已完整的 reference 會變 clickable

**Test Strategy:**

| TC ID | 對應 BDD scenario | 證明什麼 |
|---|---|---|
| TC-comp-assistant-01 | S-stream-02, S-md-01, S-tool-01, S-err-05 | parts dispatch：text → Markdown、tool → ToolCard、error → inline ErrorBlock；parallel tools 順序穩定 |
| TC-comp-assistant-02 | S-err-07 | abortedTools 只 override `input-available`，不蓋 terminal state |
| TC-comp-assistant-03 | S-regen-02, S-regen-03 | RegenerateButton：isLast + ready → show；isLast + streaming → hide；非 last → 永遠 hide |

**Verification:**

| Scope | Command | Expected Result | Why |
|---|---|---|---|
| Targeted | `pnpm test -- AssistantMessage` | TC-comp-assistant-01/02/03 passed | parts dispatch + aborted override + regenerate visibility |

**Execution Checklist:**

- [ ] 🔴 Copy TC-comp-assistant-01/02/03 → test file，跑 → RED
- [ ] 🟢 寫 `AssistantMessage.tsx`
- [ ] 🟢 Test → 全綠
- [ ] 🔵 Refactor：parts dispatch 可抽 helper `dispatchPart(part)` 提升可讀性
- [ ] 🔵 Re-run → 綠
- [ ] Commit：`git commit -m "feat(s3): AssistantMessage organism (parts dispatch + aborted + regenerate gating)"`

---

### Task 4.5: `ErrorBlock` organism（TC-comp-error-01）

**Files:**

- Create: `frontend/src/components/organisms/ErrorBlock.tsx`
- Create: `frontend/src/components/organisms/__tests__/ErrorBlock.test.tsx`

**What & Why:** Pre-stream HTTP error 與 mid-stream SSE error 共用同一個 organism。顯示 friendly title、可選展開 raw detail、可選 Retry button（依 `friendly.retriable` gating）、長 detail 自動截斷（Q-USR-6）。

**DOM contract:**

- Pre-stream variant: `<div data-testid="stream-error-block" data-error-source="pre-stream" data-error-class={errorClass}>`
- Mid-stream variant: `<div data-testid="inline-error-block" data-error-source="mid-stream" data-error-class={errorClass}>`
- Title: `<h3 data-testid="error-title">`（friendly English title）
- Detail toggle: `<button data-testid="error-detail-toggle" aria-expanded={isOpen}>`
- Detail panel: `<pre data-testid="error-raw-detail">`
- Retry button: `<button data-testid="error-retry-btn" aria-label="Retry">`（**只在 retriable 時 render**）

**Implementation Notes:**

- Props: `{ friendly: FriendlyError; onRetry: () => void; source: 'pre-stream' | 'mid-stream'; errorClass: ErrorClass }`
- 用 shadcn `Alert` + `AlertTitle` + `AlertDescription` + `Button` + lucide `AlertCircle`
- 內部 `useState<boolean>` for show-details toggle
- 內部 `useState<boolean>` for "show more" 截斷展開（detail > 200 chars 時）
- 不直接顯示 backend rawMessage — 永遠 friendly title，detail 走 expand

**Test Strategy:**

| TC ID | 證明什麼 |
|---|---|
| TC-comp-error-01 | friendly title 顯示、detail 預設隱藏、show-details toggle、retriable=false 時 retry 隱藏、長 detail 截斷 |

**Verification:**

| Scope | Command | Expected Result | Why |
|---|---|---|---|
| Targeted | `pnpm test -- ErrorBlock` | TC-comp-error-01 passed | distinct messaging + truncation + retry gating |

**Execution Checklist:**

- [ ] 🔴 Copy TC-comp-error-01 → test file，跑 → RED
- [ ] 🟢 寫 `ErrorBlock.tsx`
- [ ] 🟢 Test → 綠
- [ ] 🔵 Refactor：把 truncation logic 抽 helper（200 chars threshold）
- [ ] 🔵 Re-run → 綠
- [ ] Commit：`git commit -m "feat(s3): ErrorBlock organism with friendly title and retriable gating"`

---

### Task 4.6: `Composer` organism（TC-comp-composer-01..03）

**Files:**

- Create: `frontend/src/components/organisms/Composer.tsx`
- Create: `frontend/src/components/organisms/__tests__/Composer.test.tsx`

**What & Why:** Textarea + send/stop button toggle + disclaimer。內含 textarea state，必須**永不**因 status transition 清空 user in-progress input（TC-comp-composer-02 反 pattern protection）。也要對 rapid double-submit 做 status guard（TC-comp-composer-01）。

**DOM contract:**

- Root: `<form data-testid="composer">`
- Textarea: `<textarea data-testid="composer-textarea" aria-label="Message input" placeholder="Ask about markets, companies, or filings...">`
- Send: `<button data-testid="composer-send-btn" aria-label="Send message">`
- Stop: `<button data-testid="composer-stop-btn" aria-label="Stop response">`

**Implementation Notes:**

- Props: `{ sendMessage: (m: { text: string }) => void; stop: () => void; status: ChatStatus; defaultValue?: string }` + `forwardRef` 暴露 `setValue` for chip click integration（TC-comp-composer-03）
- Internal `useState<string>` for textarea content — **禁止** `useEffect([status], () => setText(''))`（會破壞 in-progress input）
- Send 邏輯：`if (status !== 'ready' || text.trim().length === 0) return`；避免 double-submit
- Submit on Enter（無 Shift）；`Enter+Enter` 第二次必須被 status guard 擋下（status 已 transition 為 'submitted'）
- Send/Stop button toggle：status === 'ready' 顯示 send，status === 'submitted' / 'streaming' 顯示 stop
- Placeholder、disclaimer、button labels 全部 hardcoded 英文（per design.md「UI String Language Policy」）

**Critical Contract / Snippet:**

```tsx
import { forwardRef, useImperativeHandle, useRef, useState } from "react"
import { Button } from "@/components/primitives/button"
import { Textarea } from "@/components/primitives/textarea"
import type { ChatStatus } from "@/models"

export type ComposerHandle = { setValue: (v: string) => void }
type Props = {
  sendMessage: (m: { text: string }) => void
  stop: () => void
  status: ChatStatus
}

export const Composer = forwardRef<ComposerHandle, Props>(
  ({ sendMessage, stop, status }, ref) => {
    const [text, setText] = useState("")
    useImperativeHandle(ref, () => ({ setValue: setText }), [])

    const handleSubmit = (e: React.FormEvent) => {
      e.preventDefault()
      if (status !== "ready") return // double-submit guard
      const trimmed = text.trim()
      if (!trimmed) return
      sendMessage({ text: trimmed })
      setText("")
    }

    return (
      <form data-testid="composer" onSubmit={handleSubmit}>
        <Textarea
          data-testid="composer-textarea"
          aria-label="Message input"
          placeholder="Ask about markets, companies, or filings..."
          value={text}
          onChange={e => setText(e.target.value)}
          onKeyDown={e => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault()
              handleSubmit(e as unknown as React.FormEvent)
            }
          }}
        />
        {status === "submitted" || status === "streaming" ? (
          <Button data-testid="composer-stop-btn" aria-label="Stop response" onClick={stop}>
            {/* stop icon */}
          </Button>
        ) : (
          <Button data-testid="composer-send-btn" aria-label="Send message" type="submit">
            {/* send icon */}
          </Button>
        )}
        <p>AI-generated responses may be inaccurate. Please verify important information.</p>
      </form>
    )
  },
)
```

**Test Strategy:**

| TC ID | 對應 BDD scenario | 證明什麼 |
|---|---|---|
| TC-comp-composer-01 | S-stream-05 | rapid Enter twice → sendMessage 1 次；submitted 狀態無 send button |
| TC-comp-composer-02 | S-stream-04, S-regen-04 | textarea value 不因 status transition 清空（防 useEffect anti-pattern） |
| TC-comp-composer-03 | S-empty-02 | chip click overwrites textarea (last-wins via setValue ref API) |

**Verification:**

| Scope | Command | Expected Result | Why |
|---|---|---|---|
| Targeted | `pnpm test -- Composer` | TC-comp-composer-01/02/03 passed | double-submit guard + textarea preservation + chip overwrite |

**Execution Checklist:**

- [ ] 🔴 Copy TC-comp-composer-01/02/03 → test file，跑 → RED
- [ ] 🟢 寫 `Composer.tsx`（forwardRef + useImperativeHandle + status guard）
- [ ] 🟢 Test → 全綠
- [ ] 🔵 Refactor / Re-run → 綠
- [ ] Commit：`git commit -m "feat(s3): Composer organism with double-submit guard and ref API"`

---

### Task 4.7: `EmptyState` organism（TC-comp-empty-01）

**Files:**

- Create: `frontend/src/components/organisms/EmptyState.tsx`
- Create: `frontend/src/components/organisms/__tests__/EmptyState.test.tsx`

**What & Why:** Welcome card + 4 個 prompt chips（per Q5、Q-USR-2）。chip click 觸發 `onPickPrompt(text)`，**不**自動 send。

**DOM contract:**

- Root: `<div data-testid="empty-state">`
- 4 個 chips: 各自 `<button data-testid="prompt-chip" data-chip-index={i} aria-label={text}>`

**Implementation Notes:**

- Props: `{ onPickPrompt: (text: string) => void }`
- 用 shadcn `Empty` + `EmptyHeader` + `EmptyTitle` + `EmptyDescription` + `EmptyContent`
- 4 個 chip texts（per design Q5 英文）：
  - "Latest market news for NVDA"
  - "Show AAPL stock quote"
  - "Compare NVDA and AMD financials"
  - "Summarize the latest 10-K of MSFT"
- 對應 lucide icons：`Newspaper`、`DollarSign`、`BarChart3`、`FileText`
- Welcome title 用 mockup 文案 "What would you like to know?" 28px bold

**Test Strategy:**

| TC ID | 證明什麼 |
|---|---|
| TC-comp-empty-01 | 4 個 chip render；chip click 觸發 onPickPrompt 而非 send |

**Verification:**

| Scope | Command | Expected Result | Why |
|---|---|---|---|
| Targeted | `pnpm test -- EmptyState` | TC-comp-empty-01 passed | chip click 不 auto send |

**Execution Checklist:**

- [ ] 🔴 Copy TC-comp-empty-01 → test file，跑 → RED
- [ ] 🟢 寫 `EmptyState.tsx`
- [ ] 🟢 Test → 綠
- [ ] 🔵 Refactor / Re-run → 綠
- [ ] Commit：`git commit -m "feat(s3): EmptyState organism with 4 prompt chips (no auto-send)"`

---

### Task 4.8: `MessageList` template（TC-comp-typing-02 + 整合 typing-indicator-logic）

**Files:**

- Create: `frontend/src/components/templates/MessageList.tsx`
- Update: `frontend/src/components/templates/__tests__/MessageList.test.tsx`（補 TC-comp-typing-02；TC-comp-typing-01 truth table 已在 M2 Task 2.6 寫好）

**What & Why:** 可 scroll messages viewport（用 shadcn `ScrollArea`）+ 訊息迭代（dispatch user/assistant message 到對應 component）+ TypingIndicator phantom slot + follow-bottom 行為（透過 `useFollowBottom` hook）。**完全不知道 useChat 存在** — 接 props 即可 mock data。

**DOM contract:**

- Root: `<div data-testid="message-list" data-status={chatStatus}>`
- Viewport: `<div data-testid="message-list-viewport">`（為了 follow-bottom 與 RefSup anchor scroll）

**Implementation Notes:**

- Props: `{ messages: UIMessage[]; status: ChatStatus; toolProgress: ToolProgressRecord; abortedTools: Set<ToolCallId>; onRegenerate: (id: string) => void; emptyContent?: ReactNode }`
- 用 shadcn `ScrollArea` 包 viewport；ref 給 useFollowBottom
- 迭代 messages：`role === 'user'` → UserMessage、`role === 'assistant'` → AssistantMessage
- TypingIndicator 顯示 derive 自 `shouldShowTypingIndicator({ status, lastMessage })`
- Empty state：messages 為空時 render `emptyContent`（由 ChatPanel 傳 `<EmptyState onPickPrompt={...} />`）
- `useEffect([messages], () => { if (shouldFollowBottom) scrollToBottom() })` — 在 messages 變化時 conditional auto-scroll
- 暴露 `forceFollowBottom` ref 給 ChatPanel send button 觸發（per Q-USR-10）

**Test Strategy:**

| TC ID | 對應 BDD scenario | 證明什麼 |
|---|---|---|
| TC-comp-typing-01 (relocated) | S-stream-06/07/08 | typing visibility truth table（已在 M2 Task 2.6 寫的 logic 在這裡 import） |
| TC-comp-typing-02 | S-stream-06 | transient toolProgress 變化但 messages 沒新 part → TypingIndicator 仍顯示，無 ghost ToolCard |

**Verification:**

| Scope | Command | Expected Result | Why |
|---|---|---|---|
| Targeted | `pnpm test -- MessageList` | TC-comp-typing-01 + TC-comp-typing-02 passed | typing 邏輯 + ghost ToolCard 不出現 |

**Execution Checklist:**

- [ ] 🔴 Copy TC-comp-typing-02 → `MessageList.test.tsx`，跑 → RED
- [ ] 🟢 寫 `MessageList.tsx`
- [ ] 🟢 Test → 綠（含 typing-01 truth table + typing-02）
- [ ] 🔵 Refactor / Re-run → 綠
- [ ] Commit：`git commit -m "feat(s3): MessageList template with follow-bottom + typing indicator dispatch"`

---

### Flow Verification: M4 component layer ready

> M4 完成後所有 organism + template + dependent atoms / molecules 都有 test 守護。可以在 dev playground 用 mock data 渲染整個 message list 做 visual smoke。

| #   | Method  | Step                                                                                                          | Expected Result                                           |
| --- | ------- | ------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------- |
| 1   | Vitest  | `cd frontend && pnpm test -- src/components/{atoms,molecules,organisms,templates}`                            | 全部 component / template tests 通過                        |
| 2   | Coverage | `pnpm test -- --coverage src/components`                                                                      | component layer ≥ 80% statement                            |
| 3   | Type check | `pnpm tsc -b --noEmit`                                                                                       | 0 errors                                                    |

- [ ] All M4 flow verifications pass

---

## Milestone 5 — ChatPanel Page + Integration Tests

### Task 5.1: ChatPanel basic wiring + App.tsx mount

**Files:**

- Create: `frontend/src/components/pages/ChatPanel.tsx`
- Update: `frontend/src/App.tsx` — mount `<ChatPanel />`

**What & Why:** ChatPanel 是唯一的 stateful orchestrator。把 useChat、useToolProgress、useFollowBottom、chatId state、abortedTools state、lastTriggerRef、handleRetry / handleStop / handleClearSession / handleRegenerate / handleSend 全部組起來。Task 5.1 先做 happy-path wiring，5.2/5.3/5.4 各自加 smart retry / aborted / stop+clear race + 對應 integration test。

**DOM contract:**

- Root: `<div data-testid="chat-panel" data-chat-id={chatId}>` （`data-chat-id` 用 `import.meta.env.DEV` gate，prod 不 render）

**Implementation Notes:**

- 完整 architecture 見 design.md「State Management Architecture」+ prerequisites §5/§6
- Props: 無（page 是 top-level orchestrator）
- 三層 hook + state：
  - `chatId: useState<ChatId>(() => crypto.randomUUID())`
  - `transport: useMemo(() => new DefaultChatTransport({ api: '/api/v1/chat' }), [])`
  - `useToolProgress()` → `{ toolProgress, handleData, clearProgress }`
  - `useChat({ id: chatId, transport, onData: handleData })` → `{ messages, sendMessage, regenerate, stop, status, error }`
  - `abortedTools: useState<Set<ToolCallId>>(() => new Set())`（M5.3 補實作）
  - `lastTriggerRef: useRef<LastTrigger | null>(null)`（M5.2 補實作）
  - `useFollowBottom(viewportRef)` → `{ shouldFollowBottom, handleScroll, forceFollowBottom }`
- handlers (本 task 先做基本版，5.2-5.4 補完):
  - `handleSend(text)`: `lastTriggerRef.current = { type: 'send', userText: text }; forceFollowBottom(); sendMessage({ text })`
  - `handleRegenerate(messageId)`: `lastTriggerRef.current = { type: 'regenerate', messageId, userText: findOriginalUserText(messages, messageId) }; regenerate({ messageId })`
  - `handleClearSession()`: `stop(); setChatId(crypto.randomUUID()); clearProgress(); setAbortedTools(new Set())`
  - `handleStop()`: `stop()`（M5.3 補加 collectRunningTools 邏輯）
  - `handleRetry()`: M5.2 完整實作

**Critical Contract / Snippet:**

```tsx
import { useChat } from "@ai-sdk/react"
import { DefaultChatTransport } from "ai"
import { useState, useMemo, useRef } from "react"
import { useToolProgress } from "@/hooks/useToolProgress"
import { useFollowBottom } from "@/hooks/useFollowBottom"
import type { ChatId, ToolCallId } from "@/models"
import { ChatHeader } from "@/components/organisms/ChatHeader"
import { Composer, type ComposerHandle } from "@/components/organisms/Composer"
import { MessageList } from "@/components/templates/MessageList"
import { EmptyState } from "@/components/organisms/EmptyState"
import { findOriginalUserText } from "@/lib/message-helpers"

type LastTrigger =
  | { type: "send"; userText: string }
  | { type: "regenerate"; messageId: string; userText: string }

export function ChatPanel() {
  const [chatId, setChatId] = useState<ChatId>(() => crypto.randomUUID())
  const transport = useMemo(() => new DefaultChatTransport({ api: "/api/v1/chat" }), [])
  const { toolProgress, handleData, clearProgress } = useToolProgress()
  const { messages, sendMessage, regenerate, stop, status, error } = useChat({
    id: chatId,
    transport,
    onData: handleData,
  })
  const [abortedTools, setAbortedTools] = useState<Set<ToolCallId>>(() => new Set())
  const lastTriggerRef = useRef<LastTrigger | null>(null)
  const viewportRef = useRef<HTMLDivElement>(null)
  const { shouldFollowBottom, handleScroll, forceFollowBottom } = useFollowBottom(viewportRef)
  const composerRef = useRef<ComposerHandle>(null)

  // handlers ... (詳見後續 task)

  const dataTestProps =
    import.meta.env.DEV ? { "data-chat-id": chatId } : {}

  return (
    <div data-testid="chat-panel" {...dataTestProps} className="flex h-screen flex-col bg-background">
      <ChatHeader onClear={handleClearSession} messagesEmpty={messages.length === 0} />
      <MessageList
        ref={viewportRef}
        messages={messages}
        status={status}
        toolProgress={toolProgress}
        abortedTools={abortedTools}
        onRegenerate={handleRegenerate}
        emptyContent={
          <EmptyState onPickPrompt={text => composerRef.current?.setValue(text)} />
        }
        // ... follow-bottom wiring
      />
      <Composer ref={composerRef} sendMessage={({ text }) => handleSend(text)} stop={handleStop} status={status} />
      {/* pre-stream error block 渲染（messages 為空時且 error 存在）*/}
    </div>
  )
}
```

**Test Strategy:** 本 task 是 wiring — 不寫獨立 test。後續 5.2/5.3/5.4 的 integration test 會驗整個 flow。

**Verification:**

| Scope | Command | Expected Result | Why |
|---|---|---|---|
| Type check | `pnpm tsc -b --noEmit` | 0 errors | 全部 hook + 子元件 wiring 對齊 |
| Build | `pnpm build` | 0 errors | bundle 成功 |
| Browser smoke | `pnpm dev` 開 `http://localhost:5173/` | EmptyState 顯示、可在 Composer 輸入 | basic UI render，但無 backend 不會真的 stream |

**Execution Checklist:**

- [ ] 寫 `ChatPanel.tsx`（基本 wiring + EmptyState）
- [ ] 改 `App.tsx` 為 `<ChatPanel />`
- [ ] Build + dev server smoke
- [ ] Commit：`git commit -m "feat(s3): ChatPanel page with basic useChat wiring and dev playground mount"`

---

### Task 5.2: Smart retry dispatch（TC-int-retry-01）

**Files:**

- Update: `frontend/src/components/pages/ChatPanel.tsx` — 補 `handleRetry` smart dispatch
- Create: `frontend/src/components/pages/__tests__/ChatPanel.integration.test.tsx`（先建 file 並寫第一個 integration test）

**What & Why:** Per V-1 result (verification_results_streaming_chat_ui.md): S1 actually **accepts** partial-turn regenerate with HTTP 200. The smart retry primary path is therefore `regenerate({ messageId: lastAssistantMessage.id })` (the ID is already the backend-issued `lc_run--...` because AI SDK v6 propagates `start.messageId` into `state.message.id` — see `frontend/node_modules/ai/dist/index.js:5814-5815`, no manual stashing needed). The `sendMessage(originalUserText)` fallback remains as an **exception handler** for the race window where the client disconnected before LangGraph committed any AIMessage to its checkpoint — backend may then return 404 ("no assistant message to regenerate") or 422 ("messageId does not match"). The fallback must trigger on **any 4xx**, not just 422.

**Implementation Notes:**

- `handleRetry` 邏輯詳見 prerequisites §5（注意：本 plan 已根據 V-1 結果把 fallback condition 從 `pre-stream-422` 放寬到「任何 pre-stream 4xx」，prerequisites §5 的 pseudo-code 仍寫 422，請以本 task 的 snippet 為準）：
  - 從 `lastTriggerRef` + `classifyError(error)` 取得「上次 trigger 類型」與「當前 error class」
  - 若 `last.type === 'regenerate'` && `errorClass` 是任何 4xx (`'pre-stream-422'` / `'pre-stream-404'` / `'pre-stream-409'`) → 切換為 sendMessage(last.userText)
  - 否則 replay 原 action
- ChatPanel 必須把 `handleRetry` 傳給 ErrorBlock 的 `onRetry` prop
- Pre-stream error 渲染位置：messages 為空 / 或最後一筆 user message 之後 → 渲染獨立 ErrorBlock；mid-stream 由 AssistantMessage 內嵌 ErrorBlock 處理（M4 已做）
- **No manual stash**: `regenerate({ messageId: assistantMessage.id })` works because `assistantMessage.id` is already the backend-issued `lc_run--...` ID after the start chunk arrives. Verified empirically in V-1 (HTTP 200 + new SSE stream) and by reading the AI SDK v6 store reducer.

**Critical Contract / Snippet:**

```ts
// Helper: any pre-stream 4xx that should trigger sendMessage fallback.
const PRE_STREAM_4XX: ReadonlySet<ErrorClass> = new Set([
  'pre-stream-422',
  'pre-stream-404',
  'pre-stream-409',
])

const handleRetry = useCallback(() => {
  const last = lastTriggerRef.current
  if (!last) return
  const errClass = classifyError(error)
  // Race-window fallback: regenerate hit a 4xx because the partial AIMessage
  // wasn't yet in LangGraph checkpoint when the client disconnected.
  // Replay the original user text via sendMessage instead.
  if (last.type === "regenerate" && PRE_STREAM_4XX.has(errClass)) {
    lastTriggerRef.current = { type: "send", userText: last.userText }
    sendMessage({ text: last.userText })
    return
  }
  if (last.type === "send") return sendMessage({ text: last.userText })
  if (last.type === "regenerate") return regenerate({ messageId: last.messageId })
}, [error, sendMessage, regenerate])
```

**Test Strategy:**

| TC ID | 對應 BDD scenario | 證明什麼 |
|---|---|---|
| TC-int-retry-01 | S-err-04 + Q-USR-7 | regenerate → 422 → click Retry → sendMessage 被呼叫；regenerate count 不再上升（無無限 loop） |

**Verification:**

| Scope | Command | Expected Result | Why |
|---|---|---|---|
| Targeted | `pnpm test -- ChatPanel.integration --grep "smart retry"` | TC-int-retry-01 passed；regenerateCallCount === 1, sendMessageCallCount === 2 | smart retry dispatch 正確 |

**Execution Checklist:**

- [ ] 🔴 Copy TC-int-retry-01 → `ChatPanel.integration.test.tsx`，跑 → RED
- [ ] 🟢 補 ChatPanel `handleRetry` 邏輯 + 把 onRetry 傳給 ErrorBlock；在 messages.length === 0 或 error 存在時 render pre-stream ErrorBlock
- [ ] 🟢 Test → 綠
- [ ] 🔵 Refactor / Re-run → 綠
- [ ] Commit：`git commit -m "feat(s3): ChatPanel smart retry dispatch (422-on-regenerate fallback)"`

---

### Task 5.3: Aborted tools propagation（TC-int-aborted-01）+ handleStop 邏輯

**Files:**

- Update: `frontend/src/components/pages/ChatPanel.tsx` — abortedTools state + Path 1 (stop) + Path 2 (mid-stream error useEffect)
- Update: `frontend/src/components/pages/__tests__/ChatPanel.integration.test.tsx` — 加 TC-int-aborted-01

**What & Why:** Mid-stream error / user stop 時，仍處於 `input-available` 的 tool 必須立即 mark 為 aborted（per Q-USR-3 + prerequisites §6）。完整邏輯（Path 1 stop / Path 2 mid-stream error useEffect）見 prerequisites §6。

**Implementation Notes:**

- Path 1 — `handleStop`：
  ```ts
  const handleStop = useCallback(() => {
    const lastMsg = messages.at(-1)
    const runningIds: ToolCallId[] = []
    if (lastMsg?.role === "assistant") {
      for (const p of lastMsg.parts) {
        if (p.type === "tool" && p.state === "input-available") {
          runningIds.push(p.toolCallId)
        }
      }
    }
    setAbortedTools(prev => new Set([...prev, ...runningIds]))
    stop()
  }, [messages, stop])
  ```
- Path 2 — `useEffect([messages], ...)` 監測 mid-stream error part：
  ```ts
  useEffect(() => {
    const lastMsg = messages.at(-1)
    if (!lastMsg || lastMsg.role !== "assistant") return
    if (!lastMsg.parts.some(p => p.type === "error")) return
    const ids = lastMsg.parts
      .filter(p => p.type === "tool" && (p as ToolUIPart).state === "input-available")
      .map(p => (p as ToolUIPart).toolCallId)
    if (ids.length) setAbortedTools(prev => new Set([...prev, ...ids]))
  }, [messages])
  ```
- 把 abortedTools propagate 到 MessageList → AssistantMessage → ToolCard

**Test Strategy:**

| TC ID | 對應 BDD scenario | 證明什麼 |
|---|---|---|
| TC-int-aborted-01 | S-err-07 | mid-stream error 後仍 input-available 的 tool card → `data-tool-state="aborted"` |

**Verification:**

| Scope | Command | Expected Result | Why |
|---|---|---|---|
| Targeted | `pnpm test -- ChatPanel.integration --grep "aborted"` | TC-int-aborted-01 passed | abortedTools propagation through layers |

**Execution Checklist:**

- [ ] 🔴 Copy TC-int-aborted-01 → integration test file，跑 → RED
- [ ] 🟢 補 handleStop + useEffect mid-stream error path
- [ ] 🟢 Test → 綠
- [ ] 🔵 Refactor：抽 helper `collectRunningTools(message)` 提升可讀性
- [ ] 🔵 Re-run → 綠
- [ ] Commit：`git commit -m "feat(s3): ChatPanel aborted tools propagation (stop + mid-stream error)"`

---

### Task 5.4: Stop+clear race + remaining MSW fixtures（TC-int-stop-clear-01）

**Files:**

- Update: `frontend/src/components/pages/ChatPanel.tsx` — handleClearSession 確保 stop + setChatId + clearProgress + setAbortedTools(new Set()) atomic
- Update: `frontend/src/components/pages/__tests__/ChatPanel.integration.test.tsx` — 加 TC-int-stop-clear-01
- Create: 剩餘 ~16 個 MSW fixtures（per prerequisites §3 catalog）— 不在 M1 已建的 5 個之內

**What & Why:** Stop + immediate clear 在 streaming 中觸發 → 必須立即回到 EmptyState、無 leak。也補上其他 fixtures 讓後續 E2E 任務可直接用。

**Implementation Notes:**

- handleClearSession 已在 Task 5.1 寫好 — 此 task 主要驗證 race condition + 加 MSW fixture coverage
- 剩餘 MSW fixtures（per prerequisites §3 catalog 所列 19 個減 M1 已建的 5 個 = 14 個，原 21 個中 `url-chunk-boundary` 與 `streaming-sources-incremental` 已隨 defer-to-ready 策略移除）：
  - `transient-progress-first.ts`、`start-then-error.ts`、`parallel-tools-progress-isolated.ts`、`progress-three-rapid.ts`、`progress-then-success-no-sustain.ts`、`large-output-json-500kb.ts`、`tool-error-rate-limit.ts`、`parallel-tools-mixed-state.ts`、`orphan-refs.ts`、`pre-stream-500.ts`、`pre-stream-5xx-unknown.ts`、`pre-stream-422-regenerate.ts`、`mid-stream-error-after-tool.ts`、`mid-stream-error-tool-running.ts`、`tool-running-no-output.ts`、`flaky-network-mid-stream.ts`、`mock-clear-conversation.ts`
  - 其中 `pre-stream-500-then-success.ts` 是 TC-e2e-smoke-error-01 用的「第一次 500、第二次 success」sequential fixture，需要 handler 額外支援 call-count 切換
  - `long-text-stream.ts` + `slow-start-stream.ts` 是 TC-e2e-stop-01 用的 — 需新增

**Test Strategy:**

| TC ID | 對應 BDD scenario | 證明什麼 |
|---|---|---|
| TC-int-stop-clear-01 | S-clear-04 + Q-USR-5 | streaming 中 click clear → EmptyState、無 user/assistant message 殘留、late chunks 不洩漏 |

**Verification:**

| Scope | Command | Expected Result | Why |
|---|---|---|---|
| Targeted | `pnpm test -- ChatPanel.integration --grep "stop \\+ clear"` | TC-int-stop-clear-01 passed | atomic reset |
| Fixture sanity | `cd frontend && pnpm tsc -b --noEmit` | 0 errors | 21 個 fixture types 對齊 SSEFixture |

**Execution Checklist:**

- [ ] 🔴 Copy TC-int-stop-clear-01 → integration test file，跑 → RED
- [ ] 🟢 確認 handleClearSession 行為符合 spec（已在 Task 5.1 寫好）；補任何缺漏的 reset 動作
- [ ] 🟢 Test → 綠
- [ ] 建剩餘 16 個 MSW fixtures（依 prerequisites §3 catalog 範例 + chunks 序列）
- [ ] 補 handler 對 `pre-stream-500-then-success` 的 call-count 邏輯
- [ ] Type check
- [ ] 🔵 Refactor / Re-run integration test → 綠
- [ ] Commit：`git commit -m "feat(s3): ChatPanel stop+clear race handling and remaining MSW fixture catalog"`

---

### Flow Verification: M5 ChatPanel + integration tests ready

> M5 完成後 ChatPanel 已全部 wire 起來、所有 integration test 通過。可以用 dev server + MSW URL fixture 做 manual smoke。

| #   | Method      | Step                                                                                           | Expected Result                                                                  |
| --- | ----------- | ---------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| 1   | Vitest      | `cd frontend && pnpm test`                                                                     | All unit / component / hook / integration tests passed                            |
| 2   | Type check  | `pnpm tsc -b --noEmit`                                                                         | 0 errors                                                                           |
| 3   | Build       | `pnpm build`                                                                                   | Build success                                                                      |
| 4   | Browser MSW | 開 `http://localhost:5173/?msw_fixture=happy-tool-then-text`，用 textarea 送個訊息 → click send | MSW handler intercept；ToolCard running → success → text 出現 → status ready；無 console error |
| 5   | Browser MSW | 開 `http://localhost:5173/?msw_fixture=mid-stream-error-after-text`，送訊息                      | 看到 partial text → ErrorBlock inline 出現、tool 維持 success state                |
| 6   | Browser real | 開 `http://localhost:5173/`（無 fixture）+ backend running → 送訊息                              | Real backend SSE stream 順利渲染                                                    |

- [ ] All M5 flow verifications pass

---

## Milestone 6 — E2E Tier 0（Playwright）

### Task 6.1: 6 個 E2E Tier 0 tests

**Files:**

- Create: `frontend/tests/e2e/security/xss-source-link.spec.ts`（TC-e2e-xss-01，tag `@security`）
- Create: `frontend/tests/e2e/smoke/chat-tool.spec.ts`（TC-e2e-smoke-tool-01，tag `@smoke`）
- Create: `frontend/tests/e2e/smoke/clear-session.spec.ts`（TC-e2e-smoke-clear-01，tag `@smoke`）
- Create: `frontend/tests/e2e/critical/error-recovery.spec.ts`（TC-e2e-smoke-error-01，tag `@critical`）
- Create: `frontend/tests/e2e/critical/stop-preserves-partial.spec.ts`（TC-e2e-stop-01，tag `@critical`）
- Create: `frontend/tests/e2e/critical/refresh-invariant.spec.ts`（TC-e2e-refresh-01，tag `@critical`）

**What & Why:** 6 個 Tier 0 是 user brief lock 的 CI bloat protection 上限。每個 test 都 deterministic（用 MSW fixture）— 無 real LLM 隨機性。Tag 對應 `--grep` filter，CI 跑 `@smoke|@critical|@security`。

**Implementation Notes:**

- 完整 test code 直接 copy 自 `implementation_test_cases_streaming_chat_ui.md` §5（**verbatim，不重寫**）
- Tag 用 inline title 寫法 `'@smoke'` 在 test name（per Playwright v1.58 docs）— 與 `tag: ['@smoke']` 屬性 syntax 二擇一，inline 寫法跟 test_cases doc 已對齊
- Playwright 會自動使用 Vite dev server（webServer config 已設定 reuseExistingServer）
- 每個 test 開頭 `await page.goto('/?msw_fixture=xxx')` → 進入 ChatPanel + MSW fixture
- TC-e2e-xss-01 必須 listen `dialog` event 確保 `javascript:` URL 不會被執行
- TC-e2e-smoke-error-01 用 `pre-stream-500-then-success` fixture（M5.4 已建，handler 對 call-count 切換）
- 各 spec 都用 `getByTestId` / locator filter — 無需 `getByText` brittle selector
- chip-tool / clear / stop / refresh 的 fixture 需求：`happy-tool-then-text`, `happy-text`, `long-text-stream`, `slow-start-stream` — 已在 M5.4 建好

**Test Strategy:**

| TC ID | Tag | 對應 BDD | 證明什麼 |
|---|---|---|---|
| TC-e2e-xss-01 | `@security` | S-md-03 | `javascript:` / `mailto:` 不出現在 DOM；無 alert dialog |
| TC-e2e-smoke-tool-01 | `@smoke` | J-stream-02 | 完整 SSE pipeline 健全 |
| TC-e2e-smoke-clear-01 | `@smoke` | J-clear-01 | clear 後 EmptyState 出現、chatId 換新 |
| TC-e2e-smoke-error-01 | `@critical` | J-err-01 | pre-stream error → Retry → success |
| TC-e2e-stop-01 | `@critical` | S-stop-01 + S-stop-04 | stop 保留 partial、Composer reset |
| TC-e2e-refresh-01 | `@critical` | S-cross-01 | refresh = new chatId, EmptyState |

**Verification:**

| Scope | Command | Expected Result | Why |
|---|---|---|---|
| Targeted | `cd frontend && pnpm playwright test --grep "@smoke\|@critical\|@security"` | 6 tests passed | E2E Tier 0 全綠 |
| Sanity | `pnpm playwright test --grep @security` | TC-e2e-xss-01 passed alone | tag filter 正確 |

**Execution Checklist:**

- [ ] 🔴 Copy TC-e2e-xss-01 → `tests/e2e/security/xss-source-link.spec.ts`
- [ ] 🔴 Copy TC-e2e-smoke-tool-01 → `tests/e2e/smoke/chat-tool.spec.ts`
- [ ] 🔴 Copy TC-e2e-smoke-clear-01 → `tests/e2e/smoke/clear-session.spec.ts`
- [ ] 🔴 Copy TC-e2e-smoke-error-01 → `tests/e2e/critical/error-recovery.spec.ts`
- [ ] 🔴 Copy TC-e2e-stop-01 → `tests/e2e/critical/stop-preserves-partial.spec.ts`
- [ ] 🔴 Copy TC-e2e-refresh-01 → `tests/e2e/critical/refresh-invariant.spec.ts`
- [ ] 🔴 跑 6 個 E2E → 預期最初幾個 RED（DevTools 看 ChatPanel 渲染狀態，補任何缺的 fixture / handler 行為）
- [ ] 🟢 修補 ChatPanel / MSW fixture 直到 6 個全綠
- [ ] 🔵 Refactor：每個 test file 是否有重複 setup → 抽 helper（小心不要過度抽 — 6 個 test scope 不同）
- [ ] 🔵 Re-run all 6 → 全綠
- [ ] Commit：`git commit -m "test(s3): 6 E2E Tier 0 tests (security + smoke + critical)"`

---

### Flow Verification: M6 E2E Tier 0 ready

> M6 完成後 CI gate 條件成立。所有 5 個 automated layer 都通過。

| #   | Method     | Step                                                                                                          | Expected Result                                  |
| --- | ---------- | ------------------------------------------------------------------------------------------------------------- | ------------------------------------------------ |
| 1   | Vitest     | `cd frontend && pnpm test`                                                                                    | 全部 unit / component / hook / integration tests 通過 |
| 2   | Playwright | `cd frontend && pnpm playwright test --grep "@smoke\|@critical\|@security"`                                    | 6 個 E2E tests passed                             |
| 3   | Coverage   | `pnpm test -- --coverage`                                                                                     | unit ≥ 90% / component ≥ 80% / integration branch ≥ 70% |
| 4   | Build      | `pnpm build`                                                                                                  | Production bundle 通過                            |

- [ ] All M6 flow verifications pass

---

## Milestone 7 — Post-implementation Verification（一次性，不在 CI 跑）

> 這個 milestone 跟前 6 個 milestone 不同：**不寫 code、不寫 test**。它 reference `verification_plan_streaming_chat_ui.md` §2 / §3 / §4 / §5 / §6 的步驟，由 implementer + Browser-Use CLI agent + human reviewer 跑完一輪 post-impl verification，並把結果寫進 `verification_results_streaming_chat_ui.md`。
>
> **無 TDD 紅綠重構** — 這是「驗收」階段，不是 implementation。

### Task 7.1: BDD Real Backend Verification（verification_plan §2 — V2-01..V2-09）

**Files:**

- Update: `artifacts/current/verification_results_streaming_chat_ui.md`

**What & Why:** 用 Browser-Use CLI agent + real S1 backend + real LLM 跑 9 個 scenario 涵蓋 ~9 個 BDD scenarios。抓 mocked 環境抓不到的 wire format drift / real network / LLM 行為。

**Steps:** 完整 V2-01..V2-09 步驟見 `verification_plan_streaming_chat_ui.md` §2。每個 scenario 跑完 → screenshot 收集 + 寫結果到 verification_results 文件對應 section。

**Verification:**

| Scope | Command | Expected Result | Why |
|---|---|---|---|
| All V2-* | 依 verification_plan §2 順序跑 | 每個 V2 都有 PASS / FAIL + screenshot path 紀錄 | 一次性 post-impl gate |

**Execution Checklist:**

- [ ] Backend running + frontend running
- [ ] 跑 V2-01 ~ V2-09 各一次，把結果（PASS/FAIL + 觀察）寫入 verification_results
- [ ] FAIL 的 scenario：開 issue + reference 對應 implementation file + 排進後續修復 task
- [ ] Commit：`git commit -m "test(s3): record post-impl bdd-real verification results"`

---

### Task 7.2: BDD Visual Mockup Comparison（verification_plan §3 — V3-01..V3-08）

**Files:**

- Update: `artifacts/current/verification_results_streaming_chat_ui.md`

**What & Why:** Browser-Use agent 對 implementation 真實 render 跟 `S3_state_storyboard.html` / `S3_layout_wireframe.html` 做視覺比對。8 個 visual checkpoint。

**Steps:** 完整 V3-01..V3-08 見 `verification_plan_streaming_chat_ui.md` §3。

**Execution Checklist:**

- [ ] 跑 V3-01 ~ V3-08，agent 比對 actual vs storyboard，把描述寫入 verification_results
- [ ] 視覺差異不可接受的 → 開 fix task
- [ ] Commit：`git commit -m "test(s3): record bdd-visual mockup comparison results"`

---

### Task 7.3: Real Interaction Feel Reports（verification_plan §4 — V4-01..V4-05）

**Files:**

- Update: `artifacts/current/verification_results_streaming_chat_ui.md`

**What & Why:** Browser-Use agent 寫 5 份 free-form report 描述「互動體感」— 非 boolean assertion，是 qualitative judgment。

**Execution Checklist:**

- [ ] 跑 V4-01 ~ V4-05，把 agent 寫的 report 黏貼進 verification_results
- [ ] Commit：`git commit -m "test(s3): record bdd interaction feel reports"`

---

### Task 7.4: Manual Behavior Tests（verification_plan §5 — MBT-01..MBT-09）

**Files:**

- Update: `artifacts/current/verification_results_streaming_chat_ui.md`

**What & Why:** 9 個 human manual test cover automated test 不容易到的 edge cases（CSS overflow、CJK 混排、window resize、paste bomb、browser back/forward 等）。

**Execution Checklist:**

- [ ] 人工跑 MBT-01 ~ MBT-09，把 PASS/FAIL + 觀察寫入 verification_results
- [ ] FAIL 的 → 補 fix task
- [ ] Commit：`git commit -m "test(s3): record manual behavior test results"`

---

### Task 7.5: User Acceptance Tests（verification_plan §6 — UAT-01..UAT-05）

**Files:**

- Update: `artifacts/current/verification_results_streaming_chat_ui.md`

**What & Why:** Product Owner / 真實 user 從 end-user 視角驗收 5 個面向：streaming 體驗、empty state onboarding、tool card 展開體驗、error messaging 友善度、暗色主題視覺一致性。

**Execution Checklist:**

- [ ] PO / user 跑 UAT-01 ~ UAT-05，記錄反饋
- [ ] 不通過 → 排 fix
- [ ] Commit：`git commit -m "test(s3): record user acceptance test results"`

---

### Flow Verification: M7 post-impl verification complete

| #   | Method                | Step                                                                                  | Expected Result                                                  |
| --- | --------------------- | ------------------------------------------------------------------------------------- | ---------------------------------------------------------------- |
| 1   | Document inspection   | 開 `verification_results_streaming_chat_ui.md`                                        | 含 V-1/V-2/V-3 + V2-01..09 + V3-01..08 + V4-01..05 + MBT-01..09 + UAT-01..05 全部紀錄 |
| 2   | Outstanding issues    | 數一下 verification_results 中的 FAIL 數                                                 | 0（或全部已開 issue 並排進修復 task）                             |
| 3   | Briefing handoff      | 跑 `generate-briefing` skill                                                         | `briefing_streaming_chat_ui.md` 產出，內容包含 implementation + BDD artifacts 摘要 |

- [ ] All M7 flow verifications pass

---

## Pre-delivery Checklist

### Code Level (TDD)

- [ ] Targeted verification for each task passes（每個 M0-M6 task 的 verification table 全綠）
- [ ] All Vitest unit / component / hook / integration tests pass
- [ ] All Playwright Tier 0 tests pass（`pnpm playwright test --grep "@smoke|@critical|@security"`）
- [ ] Lint passes（`cd frontend && pnpm lint`）
- [ ] Type check passes（`cd frontend && pnpm tsc -b --noEmit`）
- [ ] Build / bundle step succeeds（`cd frontend && pnpm build`）
- [ ] Coverage gates met（unit ≥ 90% / component ≥ 80% / integration branch ≥ 70%）

### Flow Level (Behavioral)

- [ ] M0 contract gates — PASS / FAIL
- [ ] M1 dev environment ready — PASS / FAIL
- [ ] M2 foundation libraries ready — PASS / FAIL
- [ ] M3 atoms + molecules dev preview — PASS / FAIL
- [ ] M4 component layer ready — PASS / FAIL
- [ ] M5 ChatPanel + integration tests ready — PASS / FAIL
- [ ] M6 E2E Tier 0 ready — PASS / FAIL
- [ ] M7 post-impl verification complete — PASS / FAIL

### Architecture Invariants（人工 review，不在 test 中）

- [ ] `frontend/src/components/primitives/*.tsx` 未被手動編輯（pristine）
- [ ] `data-testid` permanently shipped — 無 babel plugin / build-step removal
- [ ] `lib/error-messages.ts` 是唯一 user-facing error string 來源 — 沒有 component 自行寫 hardcoded English error
- [ ] Backend 只有 system prompt 補強這一改動（其他 backend code 完全沒動）
- [ ] No `useEffect([status], () => setText(''))` 反 pattern in Composer
- [ ] Sources molecule 在 anchor href 渲染前有 scheme guard（雙層防禦）
- [ ] `.dark` scope 包含 `--status-aborted` 變數 + StatusDot atom 的 aborted className 不含 `animate-pulse`

### Summary

- [ ] 所有 levels 通過 → ready for delivery
- [ ] 任何 failure 已紀錄 cause + next action 在 `verification_results_streaming_chat_ui.md`
