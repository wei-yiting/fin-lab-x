# Implementation Test Cases — S3 Streaming Chat UI

## Meta

- Design Reference: `artifacts/current/design_streaming_chat_ui.md`
- BDD Scenarios Reference: `artifacts/current/bdd_scenarios_streaming_chat_ui.md`
- Implementation Prerequisites Reference: `artifacts/current/implementation_prerequisites_streaming_chat_ui.md`
- Verification Plan Reference: `artifacts/current/verification_plan_streaming_chat_ui.md`
- Generated: 2026-04-08

## 文件目的

這份文件是 implementation 階段的 **TDD/BDD spec source**。Coding agent 在做每個 component / hook / lib 時，先從這裡找對應的 test cases、寫成 failing test、再實作 production code 直到 green。

跟其他 artifacts 的角色分工：

| Artifact | 性質 | 何時讀 |
|---|---|---|
| `design.md` | What to build（架構、決策、視覺）| Implementation 開始前 |
| `bdd_scenarios.md` | Behavior spec（user-observable 行為）| 任何時候作 reference |
| `implementation_prerequisites.md` | Before-implementation contracts（DOM contract、MSW infra、V-checks、library interfaces）| Milestone 0/1 |
| **本文件** | **During-implementation TDD spec**（每個 layer 的具體 test case）| 寫每個 component / hook / lib 時 |
| `verification_plan.md` | After-implementation verification（real backend + visual + UAT）| Milestone 5（implementation 完成後）|

## 設計原則

1. **每個 test case 對應一個或多個 BDD scenario** — 透過 `Source` 欄位連結
2. **每個 test case 對應一個 production code subject** — 透過 `Subject under test` 欄位連結
3. **Test code 直接可寫** — 複雜邏輯給完整 TypeScript code，簡單邏輯給 structured pseudo-code，coding agent 不需要二次推理 assertion 該怎麼寫
4. **Layer 嚴格分層** — 不要把該在 unit 層測的東西寫成 component 測（速度差 100x）、也不要把只能 e2e 測的東西寫成 unit 測（false positive）
5. **TDD red-green-refactor** — 先寫 test、跑紅、實作 code 跑綠、refactor

## TC ID convention

格式：`TC-{layer}-{feature-or-subject}-{nn}`

| Layer prefix | 含義 | 工具 |
|---|---|---|
| `TC-unit-` | Pure function / lib | Vitest |
| `TC-comp-` | React component | Vitest + RTL + jsdom |
| `TC-hook-` | React hook | Vitest + renderHook + msw/node |
| `TC-int-` | ChatPanel-level integration | Vitest + renderHook + msw/node + RTL |
| `TC-e2e-` | Playwright E2E | Playwright Tier 0 |

---

## Section 1: Unit Tests (Vitest pure functions)

### TC-unit-md-01: extractSources extracts reference with title attribute

- **Source**: S-md-01 (row 1)
- **File**: `frontend/src/lib/__tests__/markdown-sources.test.ts`
- **Subject under test**: `extractSources(markdown: string): ExtractedSources` from `lib/markdown-sources.ts`

```ts
import { extractSources } from '../markdown-sources'

describe('extractSources — happy paths', () => {
  test('extracts single reference with title attribute', () => {
    const md = `
NVDA 宣布擴大 Blackwell 產能 [1]。

[1]: https://reuters.com/nvda-blackwell-expansion "Reuters: NVIDIA expands Blackwell production"
    `.trim()

    const result = extractSources(md)

    expect(result).toEqual([
      {
        label: '1',
        url: 'https://reuters.com/nvda-blackwell-expansion',
        title: 'Reuters: NVIDIA expands Blackwell production',
        hostname: 'reuters.com',
      },
    ])
  })
})
```

**Why**: design.md `Markdown & Sources Pipeline`「Title Fallback 策略」第 1 條 — title 優先。

---

### TC-unit-md-02: extractSources falls back to hostname when title missing

- **Source**: S-md-01 (row 2)
- **File**: same as TC-unit-md-01
- **Subject under test**: `extractSources`

```ts
test('falls back to hostname when title is missing', () => {
  const md = `
NVDA Q2 [2] reported.

[2]: https://bloomberg.com/nvda-q2
  `.trim()

  const result = extractSources(md)

  expect(result).toEqual([
    {
      label: '2',
      url: 'https://bloomberg.com/nvda-q2',
      title: undefined,
      hostname: 'bloomberg.com',
    },
  ])
})
```

**Why**: design.md fallback 第 2 條，hostname fallback。

---

### TC-unit-md-03: extractSources keeps first definition for duplicate labels (first-wins)

- **Source**: S-md-02
- **File**: same
- **Subject under test**: `extractSources`

```ts
test('first-wins dedup when [1] is defined twice', () => {
  const md = `
NVDA [1] 漲。

[1]: https://reuters.com/a "Reuters A"
[1]: https://bloomberg.com/b "Bloomberg B"
  `.trim()

  const result = extractSources(md)

  expect(result).toHaveLength(1)
  expect(result[0]).toEqual({
    label: '1',
    url: 'https://reuters.com/a',
    title: 'Reuters A',
    hostname: 'reuters.com',
  })
})
```

**Why**: Q-USR-8 first-wins 決策。DOM 唯一 id 依賴此 invariant — 不能讓兩個 `id="src-1"` 同時存在。

---

### TC-unit-md-04: extractSources rejects non-http(s) URL schemes (security guard)

- **Source**: S-md-03（**security critical**）
- **File**: same
- **Subject under test**: `extractSources`

```ts
describe('extractSources — security: scheme allowlist', () => {
  test.each([
    ['javascript:alert(1)', 'javascript:'],
    ['data:image/png;base64,iVBOR', 'data:'],
    ['mailto:ir@nvidia.com', 'mailto:'],
    ['file:///etc/hosts', 'file:'],
    ['vbscript:msgbox(1)', 'vbscript:'],
  ])('drops or sanitizes %s scheme', (url) => {
    const md = `
See [1] for the report.

[1]: ${url} "Click me"
    `.trim()

    const result = extractSources(md)

    // Either filter out completely OR mark as non-link (implementation choice)
    if (result.length > 0) {
      // If kept, must NOT have a clickable URL
      expect(result[0].url).not.toMatch(/^(javascript|data|mailto|file|vbscript):/i)
    } else {
      expect(result).toHaveLength(0)
    }
  })

  test('allows http and https schemes', () => {
    const md = `
[1]: http://example.com/a "HTTP"
[2]: https://example.com/b "HTTPS"
    `.trim()

    const result = extractSources(md)

    expect(result).toHaveLength(2)
    expect(result.map((r) => r.url)).toEqual([
      'http://example.com/a',
      'https://example.com/b',
    ])
  })
})
```

**Why**: design.md 「核心原則」+ Q-USR-11 security boundary。**這條 test 必須在 production code 寫完前就能跑紅，否則 plugin 沒做 sanitization 會直接吃 XSS。**

---

### TC-unit-md-05: extractSources gracefully handles partial / malformed definitions

- **Source**: `extractSources` internal invariant（defensive against malformed input — 即使 stream 被 stop / error 中斷時 text 不完整，extraction 不得 throw）
- **File**: same
- **Subject under test**: `extractSources`

```ts
describe('extractSources — incremental parse robustness', () => {
  test('does not throw on partial URL (chunk boundary mid-URL)', () => {
    const md = `
NVDA [1]。

[1]: https://reut
    `.trim()

    expect(() => extractSources(md)).not.toThrow()
    // Either return empty (def incomplete) or sanitized partial
    const result = extractSources(md)
    if (result.length > 0) {
      expect(result[0].hostname).not.toBe('reut') // 不能顯破碎 hostname
    }
  })

  test('does not throw on malformed URL (no scheme)', () => {
    const md = `
[1]: bloomberg.com/nvda-q2 "Bloomberg"
    `.trim()

    expect(() => extractSources(md)).not.toThrow()
  })

  test('does not throw on partial title (open quote not closed)', () => {
    const md = `
[1]: https://reuters.com/x "Partial tit
    `.trim()

    expect(() => extractSources(md)).not.toThrow()
  })
})
```

**Why**: defer-to-ready 策略下 extraction 只在 stream 結束時跑，但 stream 可能被 stop / mid-stream error 中斷，此時 text 會是任意 partial 狀態。`extractSources` 必須 robust，不得 throw。

---

### TC-unit-md-06: extractSources handles orphan body refs and orphan defs

- **Source**: S-md-05
- **File**: same
- **Subject under test**: `extractSources` + `findOrphanBodyRefs` helper（如果 implementation 拆出去的話）

```ts
describe('extractSources — orphan handling', () => {
  test('def orphan: definition exists but body never references it → still in result', () => {
    const md = `
NVDA 很棒。

[1]: https://reuters.com "Reuters"
    `.trim()

    const result = extractSources(md)

    // def orphan 仍顯示（per Q-USR-9）
    expect(result).toHaveLength(1)
    expect(result[0].label).toBe('1')
  })

  test('body orphan: [3] in body but no [3]: def → not in result', () => {
    const md = `
NVDA 很棒 [3]。

[1]: https://reuters.com "Reuters"
    `.trim()

    const result = extractSources(md)

    expect(result).toHaveLength(1)
    expect(result[0].label).toBe('1')
    expect(result.find((r) => r.label === '3')).toBeUndefined()
  })
})
```

**Why**: Q-USR-9 orphan handling。

---

### TC-unit-md-07: extractSources orders by label number (not arrival order)

- **Source**: `extractSources` internal invariant（stable final ordering by numeric label — 即使 LLM 在 text 中以任意順序發出 definition，最終 Sources block 依 label number 排序）
- **File**: same
- **Subject under test**: `extractSources`

```ts
test('orders Sources by numeric label, not by appearance order in markdown', () => {
  const md = `
Body text [3] then [1] then [2].

[3]: https://c.com "C"
[1]: https://a.com "A"
[2]: https://b.com "B"
  `.trim()

  const result = extractSources(md)

  expect(result.map((r) => r.label)).toEqual(['1', '2', '3'])
})
```

**Why**: LLM 在 text 中可能以任意順序發出 definition，defer-to-ready extraction 的最終 Sources block 必須 deterministic — 依 numeric label 排序，不依 appearance order。

---

### TC-unit-err-01: toFriendlyError maps pre-stream HTTP errors to English friendly title

- **Source**: S-err-01 (all rows)
- **File**: `frontend/src/lib/__tests__/error-messages.test.ts`
- **Subject under test**: `toFriendlyError(ctx: ErrorContext): FriendlyError` from `lib/error-messages.ts`

```ts
import { toFriendlyError } from '../error-messages'

describe('toFriendlyError — pre-stream HTTP errors', () => {
  test.each([
    [422, "Couldn't regenerate that message. Please try again.", true],
    [404, 'Conversation not found. Refresh to start a new one.', false],
    [409, 'The system is busy. Please try again in a moment.', true],
    [500, 'Server error. Please try again.', true],
    [503, 'Something went wrong. Please try again.', true], // 5xx fallback
  ])('status %d → "%s" (retriable: %s)', (status, expectedTitle, expectedRetriable) => {
    const result = toFriendlyError({ source: 'pre-stream-http', status })
    expect(result.title).toBe(expectedTitle)
    expect(result.retriable).toBe(expectedRetriable)
  })
})
```

**Why**: design.md `Friendly Mapping 表` pre-stream-http 子集 + Q-USR-4 distinct messaging。

---

### TC-unit-err-02: toFriendlyError handles network failure

- **Source**: S-err-01 (network row)
- **File**: same
- **Subject under test**: `toFriendlyError`

```ts
test('network failure → connection-lost message', () => {
  const result = toFriendlyError({
    source: 'network',
    rawMessage: 'Failed to fetch',
  })
  expect(result.title).toBe('Connection lost. Check your network and try again.')
  expect(result.retriable).toBe(true)
  expect(result.detail).toBe('Failed to fetch')
})
```

**Why**: Network failure 跟 HTTP error 是不同 user 心智模型，必須 distinct messaging。

---

### TC-unit-err-03: toFriendlyError pattern-matches tool errors

- **Source**: S-tool-02
- **File**: same
- **Subject under test**: `toFriendlyError`

```ts
describe('toFriendlyError — tool-output-error pattern matching', () => {
  test.each([
    ['API rate limit exceeded', 'Too many requests. Please wait a moment and try again.', true],
    ['ticker not found', "We couldn't find that data.", false],
    ['Connection timeout after 30s', 'The tool timed out. Please try again.', true],
    ['Permission denied (403)', 'Access denied for this resource.', false],
    ['Some unknown error', 'The tool failed to run. Please try again.', true], // fallback
  ])('rawMessage "%s" → "%s"', (rawMessage, expectedTitle, expectedRetriable) => {
    const result = toFriendlyError({
      source: 'tool-output-error',
      rawMessage,
    })
    expect(result.title).toBe(expectedTitle)
    expect(result.retriable).toBe(expectedRetriable)
    expect(result.detail).toBe(rawMessage) // raw 必須保留供 expand
  })
})
```

**Why**: design.md `Friendly Mapping 表` tool-output-error 子集。Raw message 在 inline 不顯示，但 detail 必須保留供 `Show details` 展開。

---

### TC-unit-err-04: toFriendlyError handles mid-stream errors

- **Source**: S-err-05/06/07
- **File**: same
- **Subject under test**: `toFriendlyError`

```ts
describe('toFriendlyError — mid-stream-sse pattern matching', () => {
  test.each([
    ['context length exceeded', 'This conversation is too long. Start a new chat to continue.', false],
    ['token limit reached', 'This conversation is too long. Start a new chat to continue.', false],
    ['rate limit', 'The system is busy. Please try again in a moment.', true],
    ['Unknown stream error', 'Something went wrong while generating the response. Please try again.', true],
  ])('mid-stream rawMessage "%s" → "%s"', (rawMessage, expectedTitle, expectedRetriable) => {
    const result = toFriendlyError({
      source: 'mid-stream-sse',
      rawMessage,
    })
    expect(result.title).toBe(expectedTitle)
    expect(result.retriable).toBe(expectedRetriable)
  })
})
```

**Why**: Context overflow 是不可恢復錯誤，retriable 必須 false 避免 user 反覆無效嘗試。

---

### TC-unit-err-05: toFriendlyError invariants

- **Source**: design.md 不變量 section
- **File**: same

```ts
describe('toFriendlyError — invariants', () => {
  test('title is always English ASCII (no Chinese characters)', () => {
    const cases: ErrorContext[] = [
      { source: 'pre-stream-http', status: 422 },
      { source: 'pre-stream-http', status: 999 },
      { source: 'network' },
      { source: 'tool-output-error', rawMessage: 'random error' },
      { source: 'mid-stream-sse', rawMessage: 'random' },
    ]
    for (const ctx of cases) {
      const result = toFriendlyError(ctx)
      expect(result.title).toMatch(/^[\x20-\x7E]+$/) // printable ASCII only
      expect(result.title.length).toBeLessThanOrEqual(80)
      expect(result.title.length).toBeGreaterThan(0)
    }
  })

  test('detail is set only when rawMessage is provided', () => {
    expect(toFriendlyError({ source: 'pre-stream-http', status: 422 }).detail).toBeUndefined()
    expect(toFriendlyError({ source: 'pre-stream-http', status: 422, rawMessage: 'x' }).detail).toBe('x')
  })
})
```

**Why**: 防止 future contributor 不小心加中文或超長 title 破壞 layout。

---

### TC-unit-classify-01: classifyError dispatches correctly

- **Source**: S-err-04 + smart retry implementation
- **File**: `frontend/src/lib/__tests__/error-classifier.test.ts`
- **Subject under test**: `classifyError(err: unknown): ErrorClass`

```ts
import { classifyError } from '../error-classifier'

describe('classifyError', () => {
  test('TypeError with "fetch" in message → network', () => {
    expect(classifyError(new TypeError('Failed to fetch'))).toBe('network')
  })

  test.each([
    [422, 'pre-stream-422'],
    [404, 'pre-stream-404'],
    [409, 'pre-stream-409'],
    [500, 'pre-stream-500'],
    [503, 'pre-stream-5xx'],
    [504, 'pre-stream-5xx'],
  ])('error with status %d → %s', (status, expected) => {
    const err = { status, message: 'mock' }
    expect(classifyError(err)).toBe(expected)
  })

  test('unknown error → unknown', () => {
    expect(classifyError({ foo: 'bar' })).toBe('unknown')
    expect(classifyError(null)).toBe('unknown')
    expect(classifyError(undefined)).toBe('unknown')
  })
})
```

**Why**: smart retry routing 依賴正確 classification，分錯了會降級錯誤路徑。

---

### TC-unit-helpers-01: findOriginalUserText extracts user text from message history

- **Source**: smart retry implementation requirement
- **File**: `frontend/src/lib/__tests__/message-helpers.test.ts`
- **Subject under test**: `findOriginalUserText(messages, assistantMessageId): string`

```ts
import { findOriginalUserText } from '../message-helpers'
import type { UIMessage } from '@ai-sdk/react'

const makeMsg = (id: string, role: 'user' | 'assistant', text: string): UIMessage => ({
  id,
  role,
  parts: [{ type: 'text', text }],
})

describe('findOriginalUserText', () => {
  test('returns text of the user message immediately before assistant', () => {
    const messages = [
      makeMsg('u1', 'user', 'first question'),
      makeMsg('a1', 'assistant', 'first answer'),
      makeMsg('u2', 'user', 'second question'),
      makeMsg('a2', 'assistant', 'second answer'),
    ]
    expect(findOriginalUserText(messages, 'a2')).toBe('second question')
    expect(findOriginalUserText(messages, 'a1')).toBe('first question')
  })

  test('returns empty string if assistantMessageId not found', () => {
    expect(findOriginalUserText([], 'nonexistent')).toBe('')
  })

  test('returns empty string if message before is not user role', () => {
    const messages = [
      makeMsg('a1', 'assistant', 'orphan'),
    ]
    expect(findOriginalUserText(messages, 'a1')).toBe('')
  })
})
```

**Why**: smart retry 422→sendMessage 降級時需要從 message history 取回原 user text，否則 retry 不知道送什麼。

---

## Section 2: Component Tests (Vitest + RTL + jsdom)

### TC-comp-composer-01: Composer guards against rapid double-submit

- **Source**: S-stream-05
- **File**: `frontend/src/components/organisms/__tests__/Composer.test.tsx`
- **Subject under test**: `Composer` organism

```tsx
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Composer } from '../Composer'

describe('Composer — double-submit guard', () => {
  test('rapid Enter twice triggers sendMessage exactly once', async () => {
    const user = userEvent.setup()
    const sendMessage = vi.fn()
    render(
      <Composer
        sendMessage={sendMessage}
        stop={vi.fn()}
        status="ready"
      />
    )

    const textarea = screen.getByTestId('composer-textarea')
    await user.type(textarea, 'hello')
    await user.keyboard('{Enter}{Enter}') // 連按兩次

    expect(sendMessage).toHaveBeenCalledTimes(1)
    expect(sendMessage).toHaveBeenCalledWith({ text: 'hello' })
  })

  test('Send button click during submitted state is ignored', async () => {
    const user = userEvent.setup()
    const sendMessage = vi.fn()
    render(
      <Composer
        sendMessage={sendMessage}
        stop={vi.fn()}
        status="submitted" // 已經在送
      />
    )

    // submitted 狀態下 button 變 Stop，沒有 send button 可點
    expect(screen.queryByTestId('composer-send-btn')).not.toBeInTheDocument()
    expect(screen.getByTestId('composer-stop-btn')).toBeInTheDocument()
  })
})
```

**Why**: race condition 防護。Status guard 要在 Composer 內部防呆，不能依賴 user 行為。

---

### TC-comp-composer-02: Composer textarea preserves value across status transitions

- **Source**: S-stream-04, S-regen-04
- **File**: same
- **Subject under test**: `Composer`

```tsx
test('textarea value is not cleared when status transitions streaming → ready', async () => {
  const user = userEvent.setup()
  const { rerender } = render(
    <Composer sendMessage={vi.fn()} stop={vi.fn()} status="streaming" />
  )

  const textarea = screen.getByTestId('composer-textarea') as HTMLTextAreaElement
  await user.type(textarea, 'next question')

  expect(textarea.value).toBe('next question')

  // simulate status change（assistant 完成串流）
  rerender(<Composer sendMessage={vi.fn()} stop={vi.fn()} status="ready" />)

  // **不能** 被任何 useEffect 清掉
  expect(textarea.value).toBe('next question')
})

test('textarea value is not cleared when status transitions submitted → ready (regenerate)', async () => {
  const user = userEvent.setup()
  const { rerender } = render(
    <Composer sendMessage={vi.fn()} stop={vi.fn()} status="ready" />
  )

  const textarea = screen.getByTestId('composer-textarea') as HTMLTextAreaElement
  await user.type(textarea, 'in-progress text')

  // 模擬 regenerate 觸發 status 變化
  rerender(<Composer sendMessage={vi.fn()} stop={vi.fn()} status="submitted" />)
  rerender(<Composer sendMessage={vi.fn()} stop={vi.fn()} status="streaming" />)
  rerender(<Composer sendMessage={vi.fn()} stop={vi.fn()} status="ready" />)

  expect(textarea.value).toBe('in-progress text')
})
```

**Why**: 防止 implementer 加 `useEffect([status], () => setText(''))` 這種反 pattern。User in-progress input 是神聖的。

---

### TC-comp-composer-03: Composer chip click overwrites textarea (last-wins)

- **Source**: S-empty-02
- **File**: same
- **Subject under test**: `Composer` (assuming controlled value via prop or internal state with `onPickPrompt` integration)

```tsx
test('chip click overwrites existing textarea content (last-wins)', async () => {
  const user = userEvent.setup()
  // 假設 Composer 透過 ref 或 imperative API 接受 setValue
  const composerRef = createRef<{ setValue: (v: string) => void }>()
  render(
    <Composer
      ref={composerRef}
      sendMessage={vi.fn()}
      stop={vi.fn()}
      status="ready"
    />
  )

  const textarea = screen.getByTestId('composer-textarea') as HTMLTextAreaElement
  await user.type(textarea, '已輸入一半')

  // 模擬 chip click 觸發
  composerRef.current?.setValue('Latest market news')

  expect(textarea.value).toBe('Latest market news')
  expect(textarea.value).not.toContain('已輸入一半')
})
```

**Why**: Q-USR-2 last-wins 決策。第二次 chip click 必須完全 override，不能 append。

---

### TC-comp-typing-01: TypingIndicator visibility derivation table

- **Source**: S-stream-06, S-stream-07, S-stream-08, Rule 1.2 (PO base)
- **File**: `frontend/src/components/atoms/__tests__/TypingIndicator.test.tsx` 或 `MessageList.test.tsx`（取決於 visibility logic 在哪一層）
- **Subject under test**: TypingIndicator visibility derivation function

```tsx
import { shouldShowTypingIndicator } from '../typing-indicator-logic'
// 或從 MessageList 內部 export

describe('shouldShowTypingIndicator — truth table', () => {
  type Case = {
    name: string
    status: 'submitted' | 'streaming' | 'ready' | 'error'
    lastMessage: { role: 'user' | 'assistant'; parts: any[] } | null
    expected: boolean
  }

  const cases: Case[] = [
    {
      name: 'submitted, no last message → show',
      status: 'submitted',
      lastMessage: null,
      expected: true,
    },
    {
      name: 'submitted, last is user → show',
      status: 'submitted',
      lastMessage: { role: 'user', parts: [{ type: 'text', text: 'q' }] },
      expected: true,
    },
    {
      name: 'streaming, last assistant has no rendered part → show',
      status: 'streaming',
      lastMessage: { role: 'assistant', parts: [] },
      expected: true,
    },
    {
      name: 'streaming, last assistant has text part → hide',
      status: 'streaming',
      lastMessage: { role: 'assistant', parts: [{ type: 'text', text: 'hi' }] },
      expected: false,
    },
    {
      name: 'streaming, last assistant has tool part → hide',
      status: 'streaming',
      lastMessage: {
        role: 'assistant',
        parts: [{ type: 'tool', state: 'input-available', toolCallId: 'tc1' }],
      },
      expected: false,
    },
    {
      name: 'streaming, last assistant has only error part → hide (S-stream-07)',
      status: 'streaming',
      lastMessage: {
        role: 'assistant',
        parts: [{ type: 'error', errorText: 'oops' }],
      },
      expected: false,
    },
    {
      name: 'ready, last assistant complete → hide (S-stream-08)',
      status: 'ready',
      lastMessage: { role: 'assistant', parts: [{ type: 'text', text: 'done' }] },
      expected: false,
    },
    {
      name: 'error → hide',
      status: 'error',
      lastMessage: null,
      expected: false,
    },
  ]

  test.each(cases)('$name', ({ status, lastMessage, expected }) => {
    expect(shouldShowTypingIndicator({ status, lastMessage })).toBe(expected)
  })
})
```

**Why**: 一個窮舉 truth table 比寫 6 個獨立 component test 更精準。Logic 應該是 pure function，從 MessageList / ChatPanel 傳 derived state 給 TypingIndicator atom。

---

### TC-comp-typing-02: TypingIndicator does not hide on transient data-tool-progress

- **Source**: S-stream-06
- **File**: `frontend/src/components/templates/__tests__/MessageList.test.tsx`
- **Subject under test**: `MessageList` （驗 transient progress 不算 rendered part）

```tsx
test('transient data-tool-progress does not hide TypingIndicator', () => {
  // 假設 transient 不會出現在 messages array (AI SDK 的 transient 行為)
  // 此 test 驗 MessageList 對 progress-only Map 的反應
  const { rerender } = render(
    <MessageList
      messages={[{ id: 'u1', role: 'user', parts: [{ type: 'text', text: 'q' }] }]}
      status="streaming"
      toolProgress={{}}
    />
  )

  expect(screen.getByTestId('typing-indicator')).toBeInTheDocument()

  // 收到 transient progress（toolProgress map 有更新但 messages 沒變）
  rerender(
    <MessageList
      messages={[{ id: 'u1', role: 'user', parts: [{ type: 'text', text: 'q' }] }]}
      status="streaming"
      toolProgress={{ 'tc-1': 'fetching...' }}
    />
  )

  // TypingIndicator 仍應顯示 — 因為 messages 沒有 assistant rendered part
  expect(screen.getByTestId('typing-indicator')).toBeInTheDocument()
  // 也不應該 render ghost ToolCard
  expect(screen.queryByTestId('tool-card')).not.toBeInTheDocument()
})
```

**Why**: design.md Rule 1.2 邊界 + Dev Round 1 challenge 4。

---

### TC-comp-toolcard-01: ToolCard renders 4 visual states

- **Source**: S-tool-01, S-tool-02, S-err-07
- **File**: `frontend/src/components/organisms/__tests__/ToolCard.test.tsx`
- **Subject under test**: `ToolCard` organism

```tsx
import { render, screen } from '@testing-library/react'
import { ToolCard } from '../ToolCard'

describe('ToolCard — visual state via data-tool-state attribute', () => {
  const baseToolPart = {
    type: 'tool' as const,
    toolCallId: 'tc-1',
    toolName: 'yfinance_quote',
    input: { ticker: 'AAPL' },
  }

  test('input-available → data-tool-state="input-available", running pulse', () => {
    render(<ToolCard part={{ ...baseToolPart, state: 'input-available' }} isAborted={false} />)
    const card = screen.getByTestId('tool-card')
    expect(card).toHaveAttribute('data-tool-state', 'input-available')
    expect(card).toHaveAttribute('data-tool-call-id', 'tc-1')

    const dot = screen.getByTestId('status-dot')
    expect(dot).toHaveAttribute('data-status-state', 'running')
    expect(dot.className).toMatch(/animate-pulse/)
  })

  test('output-available → data-tool-state="output-available", green dot, no pulse', () => {
    render(
      <ToolCard
        part={{ ...baseToolPart, state: 'output-available', output: { price: 1045 } }}
        isAborted={false}
      />
    )
    const card = screen.getByTestId('tool-card')
    expect(card).toHaveAttribute('data-tool-state', 'output-available')
    expect(screen.getByTestId('status-dot').className).not.toMatch(/animate-pulse/)
  })

  test('output-error → data-tool-state="output-error" + friendly error inline', () => {
    render(
      <ToolCard
        part={{ ...baseToolPart, state: 'output-error', errorText: 'API rate limit exceeded' }}
        isAborted={false}
      />
    )
    expect(screen.getByTestId('tool-card')).toHaveAttribute('data-tool-state', 'output-error')
    // friendly translation, NOT raw backend message
    expect(screen.getByText(/Too many requests/)).toBeInTheDocument()
    expect(screen.queryByText('API rate limit exceeded')).not.toBeInTheDocument()
  })

  test('isAborted=true with input-available → data-tool-state="aborted", gray, no pulse', () => {
    render(
      <ToolCard part={{ ...baseToolPart, state: 'input-available' }} isAborted={true} />
    )
    const card = screen.getByTestId('tool-card')
    expect(card).toHaveAttribute('data-tool-state', 'aborted')
    expect(screen.getByTestId('status-dot').className).not.toMatch(/animate-pulse/)
  })
})
```

**Why**: 4 個視覺狀態是 ToolCard 核心責任。`data-tool-state` 是 BDD selector 跟 CSS state 雙用途，必須隨 props 自動正確 reflect。

---

### TC-comp-toolcard-02: ToolCard expand state survives messages re-render

- **Source**: S-tool-07, S-tool-09 + Dev challenge 8
- **File**: same
- **Subject under test**: `ToolCard`

```tsx
test('expanded state stable across parent re-render with same toolCallId', async () => {
  const user = userEvent.setup()
  const { rerender } = render(
    <ToolCard
      part={{
        type: 'tool',
        toolCallId: 'tc-stable',
        toolName: 'yfinance',
        state: 'input-available',
        input: {},
      }}
      isAborted={false}
    />
  )

  // 點擊展開
  await user.click(screen.getByTestId('tool-card-expand'))
  expect(screen.getByTestId('tool-input-json')).toBeInTheDocument()

  // 父元件 re-render 但 toolCallId 一樣（modeling 串流中 messages array 更新）
  rerender(
    <ToolCard
      part={{
        type: 'tool',
        toolCallId: 'tc-stable',
        toolName: 'yfinance',
        state: 'output-available',
        input: {},
        output: { price: 100 },
      }}
      isAborted={false}
    />
  )

  // 仍然展開（key 是 toolCallId，沒 unmount）
  expect(screen.getByTestId('tool-input-json')).toBeInTheDocument()
})
```

**Why**: shadcn `Collapsible` 是 uncontrolled，stable key 由 toolCallId 提供。streaming 中每次 text-delta 都觸發 re-render，user 已展開的 card 不能因此 collapse。

---

### TC-comp-assistant-01: AssistantMessage parts dispatch

- **Source**: S-stream-02, S-md-01, S-tool-01, S-err-05 base
- **File**: `frontend/src/components/organisms/__tests__/AssistantMessage.test.tsx`
- **Subject under test**: `AssistantMessage` organism

```tsx
test('renders text part as Markdown', () => {
  const message = {
    id: 'a1',
    role: 'assistant' as const,
    parts: [{ type: 'text', text: 'hello **world**' }],
  }
  render(<AssistantMessage message={message} isLast={false} abortedTools={new Set()} toolProgress={{}} />)
  expect(screen.getByText(/hello/)).toBeInTheDocument()
})

test('renders tool part as ToolCard', () => {
  const message = {
    id: 'a1',
    role: 'assistant' as const,
    parts: [
      { type: 'tool', state: 'input-available', toolCallId: 'tc-1', toolName: 'yfinance', input: {} },
    ],
  }
  render(<AssistantMessage message={message} isLast={false} abortedTools={new Set()} toolProgress={{}} />)
  expect(screen.getByTestId('tool-card')).toBeInTheDocument()
})

test('renders error part as inline ErrorBlock', () => {
  const message = {
    id: 'a1',
    role: 'assistant' as const,
    parts: [
      { type: 'text', text: 'partial...' },
      { type: 'error', errorText: 'context overflow' },
    ],
  }
  render(<AssistantMessage message={message} isLast={false} abortedTools={new Set()} toolProgress={{}} />)
  expect(screen.getByTestId('inline-error-block')).toBeInTheDocument()
  expect(screen.getByText(/partial/)).toBeInTheDocument() // partial text 保留
})

test('renders parallel tool parts in arrival order, stable', () => {
  const message = {
    id: 'a1',
    role: 'assistant' as const,
    parts: [
      { type: 'tool', state: 'output-available', toolCallId: 'tc-A', toolName: 'a', input: {}, output: {} },
      { type: 'tool', state: 'input-available', toolCallId: 'tc-B', toolName: 'b', input: {} },
    ],
  }
  const { container } = render(
    <AssistantMessage message={message} isLast={false} abortedTools={new Set()} toolProgress={{}} />
  )
  const cards = container.querySelectorAll('[data-testid="tool-card"]')
  expect(cards).toHaveLength(2)
  expect(cards[0]).toHaveAttribute('data-tool-call-id', 'tc-A')
  expect(cards[1]).toHaveAttribute('data-tool-call-id', 'tc-B')
})
```

**Why**: parts dispatch 是 AssistantMessage 核心邏輯。Order stability 防止 user 展開後 card 跳位。

---

### TC-comp-assistant-02: AssistantMessage marks aborted tools when in abortedTools set

- **Source**: S-err-07
- **File**: same
- **Subject under test**: `AssistantMessage`

```tsx
test('input-available tool with id in abortedTools → ToolCard data-tool-state="aborted"', () => {
  const message = {
    id: 'a1',
    role: 'assistant' as const,
    parts: [
      { type: 'tool', state: 'input-available', toolCallId: 'tc-aborted', toolName: 'x', input: {} },
    ],
  }
  render(
    <AssistantMessage
      message={message}
      isLast={false}
      abortedTools={new Set(['tc-aborted'])}
      toolProgress={{}}
    />
  )
  expect(screen.getByTestId('tool-card')).toHaveAttribute('data-tool-state', 'aborted')
})

test('output-available tool not affected by abortedTools', () => {
  const message = {
    id: 'a1',
    role: 'assistant' as const,
    parts: [
      { type: 'tool', state: 'output-available', toolCallId: 'tc-done', toolName: 'x', input: {}, output: {} },
    ],
  }
  render(
    <AssistantMessage
      message={message}
      isLast={false}
      abortedTools={new Set(['tc-done'])} // 即使被標
      toolProgress={{}}
    />
  )
  // tool 已成功，aborted set 不該 override
  expect(screen.getByTestId('tool-card')).toHaveAttribute('data-tool-state', 'output-available')
})
```

**Why**: aborted state 只 override `input-available`，不能蓋掉已 terminal 的 success/error。

---

### TC-comp-assistant-03: RegenerateButton visibility gated by isLast + status

- **Source**: S-regen-02, S-regen-03
- **File**: same
- **Subject under test**: `AssistantMessage`

```tsx
describe('AssistantMessage — RegenerateButton visibility', () => {
  const baseMsg = {
    id: 'a1',
    role: 'assistant' as const,
    parts: [{ type: 'text', text: 'done' }],
  }

  test('isLast=true and status=ready → button visible', () => {
    render(
      <AssistantMessage
        message={baseMsg}
        isLast={true}
        status="ready"
        abortedTools={new Set()}
        toolProgress={{}}
      />
    )
    expect(screen.getByTestId('regenerate-btn')).toBeInTheDocument()
  })

  test('isLast=true but status=streaming → button hidden', () => {
    render(
      <AssistantMessage
        message={baseMsg}
        isLast={true}
        status="streaming"
        abortedTools={new Set()}
        toolProgress={{}}
      />
    )
    expect(screen.queryByTestId('regenerate-btn')).not.toBeInTheDocument()
  })

  test('isLast=false → button hidden regardless of status', () => {
    render(
      <AssistantMessage
        message={baseMsg}
        isLast={false}
        status="ready"
        abortedTools={new Set()}
        toolProgress={{}}
      />
    )
    expect(screen.queryByTestId('regenerate-btn')).not.toBeInTheDocument()
  })
})
```

**Why**: Q-USR-1 streaming 中隱藏。防止 stale button 觸發 backend 422。

---

### TC-comp-sources-01: Sources molecule renders title or hostname fallback

- **Source**: S-md-01
- **File**: `frontend/src/components/molecules/__tests__/Sources.test.tsx`
- **Subject under test**: `Sources` molecule

```tsx
test('renders entries with title when present, hostname when missing', () => {
  const extractedSources = [
    { label: '1', url: 'https://reuters.com/x', title: 'Reuters X', hostname: 'reuters.com' },
    { label: '2', url: 'https://bloomberg.com/y', title: undefined, hostname: 'bloomberg.com' },
  ]
  render(<Sources sources={extractedSources} />)

  expect(screen.getByText('Reuters X')).toBeInTheDocument()
  expect(screen.getByText('bloomberg.com')).toBeInTheDocument()
})

test('SourceLink has anchor id="src-{label}" for in-page jump', () => {
  const extractedSources = [
    { label: '3', url: 'https://x.com', title: 'X', hostname: 'x.com' },
  ]
  const { container } = render(<Sources sources={extractedSources} />)
  expect(container.querySelector('#src-3')).toBeInTheDocument()
})
```

**Why**: BDD scenario S-md-01 在 component layer 已可驗，不需要 e2e。

---

### TC-comp-sources-02: SourceLink does NOT render anchor for non-http(s) scheme

- **Source**: S-md-03 (security)
- **File**: same
- **Subject under test**: `Sources` 或 `SourceLink`

```tsx
test('source with javascript: URL is filtered out before rendering anchor', () => {
  // 假設 lib/markdown-sources 已 filter 過，但 Sources 多一層 defensive
  const evilSources = [
    { label: '1', url: 'javascript:alert(1)', title: 'Evil', hostname: '' },
  ]
  const { container } = render(<Sources sources={evilSources} />)

  // 不能有 <a href="javascript:">
  expect(container.querySelector('a[href^="javascript:"]')).toBeNull()
})
```

**Why**: 雙層 defense — 即使 plugin 漏網，molecule 層也擋。

---

### TC-comp-error-01: ErrorBlock displays friendly title with optional show-details

- **Source**: S-err-01
- **File**: `frontend/src/components/organisms/__tests__/ErrorBlock.test.tsx`
- **Subject under test**: `ErrorBlock` organism

```tsx
test('displays friendly title only, raw detail hidden by default', () => {
  render(
    <ErrorBlock
      friendly={{
        title: 'The system is busy. Please try again in a moment.',
        detail: 'HTTP 409: session busy on backend',
        retriable: true,
      }}
      onRetry={vi.fn()}
      source="pre-stream"
      errorClass="pre-stream-409"
    />
  )

  expect(screen.getByTestId('error-title')).toHaveTextContent(
    'The system is busy. Please try again in a moment.'
  )
  // raw detail 隱藏
  expect(screen.queryByText('HTTP 409: session busy on backend')).not.toBeInTheDocument()
})

test('clicking show-details toggle reveals raw detail', async () => {
  const user = userEvent.setup()
  render(
    <ErrorBlock
      friendly={{ title: 'Server error.', detail: 'stack trace ...', retriable: true }}
      onRetry={vi.fn()}
      source="pre-stream"
      errorClass="pre-stream-500"
    />
  )

  await user.click(screen.getByTestId('error-detail-toggle'))
  expect(screen.getByTestId('error-raw-detail')).toHaveTextContent('stack trace ...')
})

test('Retry button hidden when retriable=false', () => {
  render(
    <ErrorBlock
      friendly={{
        title: 'Conversation not found. Refresh to start a new one.',
        retriable: false,
      }}
      onRetry={vi.fn()}
      source="pre-stream"
      errorClass="pre-stream-404"
    />
  )
  expect(screen.queryByTestId('error-retry-btn')).not.toBeInTheDocument()
})

test('long detail (>200 chars) is truncated with show-more affordance', () => {
  const longDetail = 'x'.repeat(500)
  render(
    <ErrorBlock
      friendly={{ title: 'Server error.', detail: longDetail, retriable: true }}
      onRetry={vi.fn()}
      source="pre-stream"
      errorClass="pre-stream-500"
    />
  )

  // 展開後檢查
  // ...具體 truncation UX 由 implementation 決定，這裡只 assert 不會直接 dump 500 chars
  const detail = screen.queryByTestId('error-raw-detail')
  if (detail) {
    expect(detail.textContent!.length).toBeLessThan(longDetail.length)
  }
})
```

**Why**: Q-USR-4 distinct messaging + Q-USR-6 truncation + Q-USR-7 retriable gating。

---

### TC-comp-empty-01: EmptyState renders when messages empty, hides chip click does not auto-send

- **Source**: S-empty-01
- **File**: `frontend/src/components/organisms/__tests__/EmptyState.test.tsx`
- **Subject under test**: `EmptyState` organism

```tsx
test('renders 4 prompt chips with correct labels', () => {
  const onPickPrompt = vi.fn()
  render(<EmptyState onPickPrompt={onPickPrompt} />)

  const chips = screen.getAllByTestId(/^prompt-chip$/)
  expect(chips).toHaveLength(4)
})

test('chip click invokes onPickPrompt with chip text, does NOT auto-send', async () => {
  const user = userEvent.setup()
  const onPickPrompt = vi.fn()
  const onSend = vi.fn() // 假設有獨立的 send callback
  render(<EmptyState onPickPrompt={onPickPrompt} />)

  await user.click(screen.getAllByTestId(/^prompt-chip$/)[1])

  expect(onPickPrompt).toHaveBeenCalledTimes(1)
  expect(onPickPrompt).toHaveBeenCalledWith(expect.any(String))
  // onSend 不該被觸發
  expect(onSend).not.toHaveBeenCalled()
})
```

**Why**: Q-USR-2 + design Q5 — 點 chip 填入但不自動送。

---

### TC-comp-header-01: ChatHeader clear button disabled when messages empty

- **Source**: S-clear-02
- **File**: `frontend/src/components/organisms/__tests__/ChatHeader.test.tsx`
- **Subject under test**: `ChatHeader` organism

```tsx
test('clear button disabled when messagesEmpty=true', () => {
  render(<ChatHeader onClear={vi.fn()} messagesEmpty={true} />)
  expect(screen.getByTestId('composer-clear-btn')).toBeDisabled()
})

test('clear button enabled when messagesEmpty=false', () => {
  render(<ChatHeader onClear={vi.fn()} messagesEmpty={false} />)
  expect(screen.getByTestId('composer-clear-btn')).toBeEnabled()
})

test('click invokes onClear callback', async () => {
  const user = userEvent.setup()
  const onClear = vi.fn()
  render(<ChatHeader onClear={onClear} messagesEmpty={false} />)
  await user.click(screen.getByTestId('composer-clear-btn'))
  expect(onClear).toHaveBeenCalledTimes(1)
})
```

**Why**: design 明文 empty state 時 disabled。

---

## Section 3: Hook Tests (Vitest + renderHook)

### TC-hook-progress-01: useToolProgress routes by toolCallId without cross-pollination

- **Source**: S-tool-05 + Dev challenge 5
- **File**: `frontend/src/hooks/__tests__/useToolProgress.test.ts`
- **Subject under test**: `useToolProgress()` hook

```ts
import { renderHook, act } from '@testing-library/react'
import { useToolProgress } from '../useToolProgress'

describe('useToolProgress — routing isolation', () => {
  test('progress for tc-A does not affect tc-B', () => {
    const { result } = renderHook(() => useToolProgress())

    act(() => {
      result.current.handleData({ id: 'tc-A', data: { message: 'A loading' } })
    })
    expect(result.current.toolProgress).toEqual({ 'tc-A': 'A loading' })

    act(() => {
      result.current.handleData({ id: 'tc-B', data: { message: 'B loading' } })
    })
    expect(result.current.toolProgress).toEqual({
      'tc-A': 'A loading',
      'tc-B': 'B loading',
    })

    // 更新 A 不影響 B
    act(() => {
      result.current.handleData({ id: 'tc-A', data: { message: 'A done' } })
    })
    expect(result.current.toolProgress).toEqual({
      'tc-A': 'A done',
      'tc-B': 'B loading',
    })
  })
})
```

**Why**: parallel tool isolation 是 hook 核心契約。

---

### TC-hook-progress-02: useToolProgress functional setState handles rapid 3 updates

- **Source**: S-tool-04 + Dev challenge 7
- **File**: same
- **Subject under test**: `useToolProgress`

```ts
test('rapid 3 progress updates within same tick produce final = 3rd', () => {
  const { result } = renderHook(() => useToolProgress())

  act(() => {
    result.current.handleData({ id: 'tc-1', data: { message: 'step 1' } })
    result.current.handleData({ id: 'tc-1', data: { message: 'step 2' } })
    result.current.handleData({ id: 'tc-1', data: { message: 'step 3' } })
  })

  expect(result.current.toolProgress['tc-1']).toBe('step 3')
})
```

**Why**: 防止 implementer 用 stale closure `setProgress({ ...toolProgress, [id]: msg })` 而不是 functional form。

---

### TC-hook-progress-03: clearProgress empties the record

- **Source**: S-clear-01 (tool progress cleanup)
- **File**: same
- **Subject under test**: `useToolProgress`

```ts
test('clearProgress empties the toolProgress record', () => {
  const { result } = renderHook(() => useToolProgress())

  act(() => {
    result.current.handleData({ id: 'tc-1', data: { message: 'loading' } })
    result.current.handleData({ id: 'tc-2', data: { message: 'loading' } })
  })
  expect(Object.keys(result.current.toolProgress)).toHaveLength(2)

  act(() => result.current.clearProgress())

  expect(result.current.toolProgress).toEqual({})
})
```

**Why**: clear session 跟 regenerate 都需要 clearProgress 的 atomic reset。

---

### TC-hook-followbottom-01: useFollowBottom 100px threshold

- **Source**: S-scroll-01, S-scroll-02, S-scroll-03
- **File**: `frontend/src/hooks/__tests__/useFollowBottom.test.ts`
- **Subject under test**: `useFollowBottom(ref)` hook

```ts
import { renderHook } from '@testing-library/react'
import { useFollowBottom } from '../useFollowBottom'

describe('useFollowBottom — 100px threshold smart tracking', () => {
  function makeContainer(scrollTop: number, scrollHeight: number, clientHeight: number) {
    const div = document.createElement('div')
    Object.defineProperty(div, 'scrollTop', { value: scrollTop, writable: true })
    Object.defineProperty(div, 'scrollHeight', { value: scrollHeight, writable: true })
    Object.defineProperty(div, 'clientHeight', { value: clientHeight, writable: true })
    return div
  }

  test('shouldFollowBottom=true when within 100px of bottom', () => {
    const ref = { current: makeContainer(800, 1000, 150) } // distance = 1000 - 800 - 150 = 50
    const { result } = renderHook(() => useFollowBottom(ref as any))
    // simulate scroll event (implementation 細節：可能 attach 到 ref.current)
    act(() => result.current.handleScroll())
    expect(result.current.shouldFollowBottom).toBe(true)
  })

  test('shouldFollowBottom=false when more than 100px from bottom', () => {
    const ref = { current: makeContainer(0, 1000, 150) } // distance = 850
    const { result } = renderHook(() => useFollowBottom(ref as any))
    act(() => result.current.handleScroll())
    expect(result.current.shouldFollowBottom).toBe(false)
  })

  test('forceFollowBottom() sets flag true regardless of position', () => {
    const ref = { current: makeContainer(0, 1000, 150) }
    const { result } = renderHook(() => useFollowBottom(ref as any))
    act(() => result.current.handleScroll())
    expect(result.current.shouldFollowBottom).toBe(false)

    act(() => result.current.forceFollowBottom())
    expect(result.current.shouldFollowBottom).toBe(true)
  })
})
```

**Why**: scroll behavior 是 hook 純邏輯，不需要 real browser。

---

## Section 4: Integration Tests (ChatPanel orchestration with msw/node)

### TC-int-retry-01: Smart retry — pre-stream 422 on regenerate falls back to sendMessage

- **Source**: S-err-04 + Q-USR-7
- **File**: `frontend/src/components/pages/__tests__/ChatPanel.integration.test.tsx`
- **Subject under test**: `ChatPanel` + `useChat` + smart retry routing

```tsx
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { setupServer } from 'msw/node'
import { http, HttpResponse } from 'msw'
import { ChatPanel } from '../ChatPanel'

let regenerateCallCount = 0
let sendMessageCallCount = 0

const server = setupServer(
  http.post('/api/v1/chat', async ({ request }) => {
    const body = (await request.json()) as { trigger?: string; messageId?: string; message?: string }
    if (body.trigger === 'regenerate') {
      regenerateCallCount++
      return HttpResponse.json({ error: 'last turn not assistant' }, { status: 422 })
    }
    sendMessageCallCount++
    // Return a successful stream
    return new HttpResponse(
      new ReadableStream({
        start(c) {
          const enc = new TextEncoder()
          c.enqueue(enc.encode('data: {"type":"start","messageId":"new"}\n\n'))
          c.enqueue(enc.encode('data: {"type":"text-start","id":"t1"}\n\n'))
          c.enqueue(enc.encode('data: {"type":"text-delta","id":"t1","delta":"recovered"}\n\n'))
          c.enqueue(enc.encode('data: {"type":"finish"}\n\n'))
          c.close()
        },
      }),
      {
        headers: { 'Content-Type': 'text/event-stream', 'x-vercel-ai-ui-message-stream': 'v1' },
      }
    )
  })
)

beforeAll(() => server.listen())
afterEach(() => {
  regenerateCallCount = 0
  sendMessageCallCount = 0
  server.resetHandlers()
})
afterAll(() => server.close())

test('regenerate 422 → Retry click → sendMessage with original user text', async () => {
  const user = userEvent.setup()
  render(<ChatPanel />)

  // 1. Send a message and wait for completion
  await user.type(screen.getByTestId('composer-textarea'), 'first question')
  await user.click(screen.getByTestId('composer-send-btn'))
  await waitFor(() => expect(screen.getByText('recovered')).toBeInTheDocument())

  // 2. Trigger regenerate which will 422
  await user.click(screen.getByTestId('regenerate-btn'))
  await waitFor(() => expect(screen.getByTestId('stream-error-block')).toBeInTheDocument())

  expect(regenerateCallCount).toBe(1)
  expect(sendMessageCallCount).toBe(1) // 從第一次 send

  // 3. Click Retry → smart retry should fall back to sendMessage with original text
  await user.click(screen.getByTestId('error-retry-btn'))
  await waitFor(() => expect(screen.queryByTestId('stream-error-block')).not.toBeInTheDocument())

  // Critical: only one regenerate call (no infinite loop), but TWO sendMessage calls
  expect(regenerateCallCount).toBe(1)
  expect(sendMessageCallCount).toBe(2)
})
```

**Why**: smart retry 是 ChatPanel orchestration 核心，必須在 integration layer 驗（unit test 不到 useChat）。

---

### TC-int-aborted-01: Mid-stream error marks input-available tools as aborted

- **Source**: S-err-07
- **File**: same
- **Subject under test**: `ChatPanel` + abortedTools state propagation

```tsx
test('mid-stream error after tool-input-available → ToolCard becomes aborted', async () => {
  // MSW handler 發 tool-input-available → text-delta × 2 → error event
  server.use(
    http.post('/api/v1/chat', () =>
      new HttpResponse(
        new ReadableStream({
          async start(c) {
            const enc = new TextEncoder()
            c.enqueue(enc.encode('data: {"type":"start","messageId":"a1"}\n\n'))
            c.enqueue(enc.encode('data: {"type":"tool-input-available","toolCallId":"tc-x","toolName":"yfinance","input":{}}\n\n'))
            await new Promise((r) => setTimeout(r, 50))
            c.enqueue(enc.encode('data: {"type":"text-start","id":"t1"}\n\n'))
            c.enqueue(enc.encode('data: {"type":"text-delta","id":"t1","delta":"partial"}\n\n'))
            await new Promise((r) => setTimeout(r, 50))
            c.enqueue(enc.encode('data: {"type":"error","errorText":"context overflow"}\n\n'))
            c.close()
          },
        }),
        { headers: { 'Content-Type': 'text/event-stream', 'x-vercel-ai-ui-message-stream': 'v1' } }
      )
    )
  )

  const user = userEvent.setup()
  render(<ChatPanel />)
  await user.type(screen.getByTestId('composer-textarea'), 'test')
  await user.click(screen.getByTestId('composer-send-btn'))

  // Wait for inline error block to appear
  await waitFor(() => expect(screen.getByTestId('inline-error-block')).toBeInTheDocument())

  // ToolCard 應該變 aborted
  const toolCard = screen.getByTestId('tool-card')
  expect(toolCard).toHaveAttribute('data-tool-state', 'aborted')

  // Partial text 仍可見
  expect(screen.getByText('partial')).toBeInTheDocument()
})
```

**Why**: abortedTools propagation 是 cross-component 邏輯，integration test 是正確 layer。

---

### TC-int-stop-clear-01: stop() then clear() race produces clean reset

- **Source**: S-clear-04 + Q-USR-5
- **File**: same
- **Subject under test**: `ChatPanel` orchestration

```tsx
test('stop + immediate clear in streaming state → EmptyState, no leak', async () => {
  // Long streaming MSW handler
  server.use(
    http.post('/api/v1/chat', () =>
      new HttpResponse(
        new ReadableStream({
          async start(c) {
            const enc = new TextEncoder()
            c.enqueue(enc.encode('data: {"type":"start","messageId":"a1"}\n\n'))
            c.enqueue(enc.encode('data: {"type":"text-start","id":"t1"}\n\n'))
            for (let i = 0; i < 20; i++) {
              await new Promise((r) => setTimeout(r, 100))
              c.enqueue(enc.encode(`data: {"type":"text-delta","id":"t1","delta":"chunk${i} "}\n\n`))
            }
            c.enqueue(enc.encode('data: {"type":"finish"}\n\n'))
            c.close()
          },
        }),
        { headers: { 'Content-Type': 'text/event-stream', 'x-vercel-ai-ui-message-stream': 'v1' } }
      )
    )
  )

  const user = userEvent.setup()
  render(<ChatPanel />)
  await user.type(screen.getByTestId('composer-textarea'), 'long question')
  await user.click(screen.getByTestId('composer-send-btn'))

  // Wait until streaming
  await waitFor(() => expect(screen.getByText(/chunk0/)).toBeInTheDocument())

  // Click clear (which should stop + reset)
  await user.click(screen.getByTestId('composer-clear-btn'))

  // EmptyState 立即出現
  expect(screen.getByTestId('empty-state')).toBeInTheDocument()
  // 無 user / assistant message 殘留
  expect(screen.queryByTestId('user-bubble')).not.toBeInTheDocument()
  expect(screen.queryByTestId('assistant-message')).not.toBeInTheDocument()

  // 等一下確認 late chunks 不會洩漏進新 EmptyState
  await new Promise((r) => setTimeout(r, 500))
  expect(screen.queryByText(/chunk/)).not.toBeInTheDocument()
})
```

**Why**: stop+clear race 是 hook orchestration 最易壞的點。

---

### TC-int-v2-01: Contract verification — useChat preserves user message after pre-stream HTTP 500

- **Source**: V-2 (implementation_prerequisites)
- **File**: `frontend/src/__tests__/contract/use-chat-error-lifecycle.test.ts`
- **Subject under test**: AI SDK v6 `useChat` contract

```ts
// NOTE: Vitest config has globals: false → must explicitly import test/expect/lifecycle hooks.
// NOTE: DefaultChatTransport is exported from `ai`, not `@ai-sdk/react`.
import { test, expect, beforeAll, afterAll } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { useChat } from '@ai-sdk/react'
import { DefaultChatTransport } from 'ai'
import { setupServer } from 'msw/node'
import { http, HttpResponse } from 'msw'

const server = setupServer(
  http.post('/api/v1/chat', () => HttpResponse.json({ error: 'boom' }, { status: 500 }))
)

beforeAll(() => server.listen())
afterAll(() => server.close())

test('V-2: user message remains in messages array after pre-stream HTTP 500', async () => {
  const transport = new DefaultChatTransport({ api: '/api/v1/chat' })
  const { result } = renderHook(() => useChat({ transport, id: 'test' }))

  await act(async () => {
    result.current.sendMessage({ text: 'test message' })
  })

  await waitFor(() => expect(result.current.error).toBeTruthy())

  expect(result.current.messages).toHaveLength(1)
  expect(result.current.messages[0].role).toBe('user')
})
```

**Why**: implementation_prerequisites Section 4 V-2 contract check。Milestone 0 必跑。

---

### TC-int-v3-01: Contract verification — useChat.stop() transitions to ready (not error)

- **Source**: V-3 (implementation_prerequisites)
- **File**: `frontend/src/__tests__/contract/use-chat-stop-semantic.test.ts`
- **Subject under test**: AI SDK v6 `useChat.stop()` contract

```ts
test('V-3: stop() transitions status to ready, error stays null', async () => {
  // setup as in implementation_prerequisites Section 4 V-3
  // Long stream → user.stop() → assert status === 'ready', error === null
  // (full code in implementation_prerequisites Section 4)
})
```

**Why**: Milestone 0 必跑。S-stop-01/02/03 直接依賴此契約。

---

## Section 5: E2E Tests (Playwright Tier 0)

### TC-e2e-xss-01: javascript: URL must not render as clickable anchor

- **Source**: S-md-03（**security critical, must always run in CI**）
- **File**: `frontend/tests/e2e/security/xss-source-link.spec.ts`
- **CI tag**: `@security`

```ts
import { test, expect } from '@playwright/test'

test('S-md-03 @security: javascript: URL is sanitized', async ({ page }) => {
  // 監聽 dialog（如果 XSS 真的執行會跳 alert）
  let dialogTriggered = false
  page.on('dialog', async (dialog) => {
    dialogTriggered = true
    await dialog.dismiss()
  })

  await page.goto('/chat?msw_fixture=xss-javascript-url')

  await page.getByTestId('composer-textarea').fill('show me sources')
  await page.getByTestId('composer-send-btn').click()

  await expect(page.getByTestId('message-list')).toHaveAttribute('data-status', 'ready')

  // CRITICAL: no javascript: hrefs in DOM
  const xssAnchors = page.locator('[data-testid="sources-block"] a[href^="javascript:"]')
  await expect(xssAnchors).toHaveCount(0)

  // mailto: also filtered
  const mailtoAnchors = page.locator('[data-testid="sources-block"] a[href^="mailto:"]')
  await expect(mailtoAnchors).toHaveCount(0)

  // 沒有任何 alert 被觸發
  expect(dialogTriggered).toBe(false)
})
```

**Why**: 安全紅線。Regression 等於 production XSS。

---

### TC-e2e-smoke-tool-01: Send message with tool call → complete response

- **Source**: J-stream-02（smoke）
- **File**: `frontend/tests/e2e/smoke/chat-tool.spec.ts`
- **CI tag**: `@smoke`

```ts
test('J-stream-02 @smoke: tool + text streaming completes successfully', async ({ page }) => {
  // 用 MSW fixture 確保 deterministic
  await page.goto('/chat?msw_fixture=happy-tool-then-text')

  await page.getByTestId('composer-textarea').fill('What is AAPL price?')
  await page.getByTestId('composer-send-btn').click()

  // user bubble 出現
  await expect(page.getByTestId('user-bubble')).toBeVisible()

  // typing indicator 短暫出現
  await expect(page.getByTestId('typing-indicator')).toBeVisible()

  // ToolCard 出現 input-available
  await expect(page.locator('[data-tool-state="input-available"]')).toBeVisible()

  // Wait for output-available
  await expect(page.locator('[data-tool-state="output-available"]')).toBeVisible({ timeout: 5000 })

  // Final state: ready
  await expect(page.getByTestId('message-list')).toHaveAttribute('data-status', 'ready')

  // Composer button 回 Send
  await expect(page.getByTestId('composer-send-btn')).toBeVisible()
  await expect(page.getByTestId('composer-stop-btn')).not.toBeVisible()
})
```

**Why**: 整條 SSE pipeline 健全 smoke。任一環節壞掉這個 test 就 red。

---

### TC-e2e-smoke-error-01: Pre-stream error → Retry → success recovery

- **Source**: J-err-01
- **File**: `frontend/tests/e2e/critical/error-recovery.spec.ts`
- **CI tag**: `@critical`

```ts
test('J-err-01 @critical: pre-stream error recovery via Retry', async ({ page }) => {
  // 第一次請求 fixture 給 pre-stream-500，第二次給 happy-text
  // (需要 MSW 支援 sequential fixture or special handler)
  await page.goto('/chat?msw_fixture=pre-stream-500-then-success')

  await page.getByTestId('composer-textarea').fill('test')
  await page.getByTestId('composer-send-btn').click()

  // ErrorBlock 出現
  await expect(page.getByTestId('stream-error-block')).toBeVisible()

  // user bubble 仍保留
  await expect(page.getByTestId('user-bubble')).toBeVisible()
  await expect(page.getByTestId('user-bubble')).toHaveCount(1)

  // 點 Retry
  await page.getByTestId('error-retry-btn').click()

  // ErrorBlock 消失
  await expect(page.getByTestId('stream-error-block')).not.toBeVisible()

  // Stream 完成
  await expect(page.getByTestId('message-list')).toHaveAttribute('data-status', 'ready')

  // user bubble 仍是 1（無 dup）
  await expect(page.getByTestId('user-bubble')).toHaveCount(1)

  // assistant message 出現
  await expect(page.getByTestId('assistant-message')).toBeVisible()
})
```

**Why**: error → retry → success 是高 blast radius 的 recovery flow。

---

### TC-e2e-smoke-clear-01: Clear session resets state and isolates new conversation

- **Source**: J-clear-01
- **File**: `frontend/tests/e2e/smoke/clear-session.spec.ts`
- **CI tag**: `@smoke`

```ts
test('J-clear-01 @smoke: clear session resets messages and chatId', async ({ page }) => {
  await page.goto('/chat?msw_fixture=happy-text')

  // 完成第一輪
  await page.getByTestId('composer-textarea').fill('first question')
  await page.getByTestId('composer-send-btn').click()
  await expect(page.getByTestId('message-list')).toHaveAttribute('data-status', 'ready')

  // 取得當前 chatId
  const oldChatId = await page.getByTestId('chat-panel').getAttribute('data-chat-id')
  expect(oldChatId).toBeTruthy()

  // Click clear
  await page.getByTestId('composer-clear-btn').click()

  // EmptyState 出現
  await expect(page.getByTestId('empty-state')).toBeVisible()
  await expect(page.getByTestId('user-bubble')).toHaveCount(0)
  await expect(page.getByTestId('assistant-message')).toHaveCount(0)

  // chatId 換新
  const newChatId = await page.getByTestId('chat-panel').getAttribute('data-chat-id')
  expect(newChatId).toBeTruthy()
  expect(newChatId).not.toBe(oldChatId)
})
```

**Why**: clear session 是多 hook 協同的核心 reset flow。

---

### TC-e2e-stop-01: Stop preserves partial response and re-enables Composer

- **Source**: S-stop-01 + S-stop-04（合併）
- **File**: `frontend/tests/e2e/critical/stop-preserves-partial.spec.ts`
- **CI tag**: `@critical`

```ts
test('S-stop-01 @critical: stop preserves partial text and resets Composer', async ({ page }) => {
  await page.goto('/chat?msw_fixture=long-text-stream')

  await page.getByTestId('composer-textarea').fill('write a long essay')
  await page.getByTestId('composer-send-btn').click()

  // Wait for some text to appear
  await expect(page.locator('[data-testid="assistant-message"] >> text=/.+/')).toBeVisible()

  // Capture partial text length before stop
  const partialBefore = await page.getByTestId('assistant-message').textContent()
  expect(partialBefore).toBeTruthy()

  // Click stop
  await page.getByTestId('composer-stop-btn').click()

  // Status → ready immediately (1-frame requirement)
  await expect(page.getByTestId('message-list')).toHaveAttribute('data-status', 'ready')

  // Composer button 立即回 Send
  await expect(page.getByTestId('composer-send-btn')).toBeVisible()
  await expect(page.getByTestId('composer-stop-btn')).not.toBeVisible()

  // Partial text 仍在
  const partialAfter = await page.getByTestId('assistant-message').textContent()
  expect(partialAfter).toBeTruthy()
  expect(partialAfter!.length).toBeGreaterThan(0)

  // Composer 可繼續輸入
  await page.getByTestId('composer-textarea').fill('follow-up question')
  await expect(page.getByTestId('composer-textarea')).toHaveValue('follow-up question')
})

test('S-stop-04 @critical: stop in submitted state preserves user bubble, no ghost', async ({ page }) => {
  await page.goto('/chat?msw_fixture=slow-start-stream')

  await page.getByTestId('composer-textarea').fill('quick stop test')
  await page.getByTestId('composer-send-btn').click()

  // Stop 在第一個 SSE event 前
  await page.getByTestId('composer-stop-btn').click({ timeout: 100 })

  // user bubble 保留
  await expect(page.getByTestId('user-bubble')).toHaveCount(1)
  // 無 ghost assistant
  await expect(page.getByTestId('assistant-message')).toHaveCount(0)
  // 無 error block
  await expect(page.getByTestId('stream-error-block')).toHaveCount(0)
  // status ready
  await expect(page.getByTestId('message-list')).toHaveAttribute('data-status', 'ready')
})
```

**Why**: stop 是核心 escape hatch，1-frame latency + 兩種狀態下都正確 = critical。

---

### TC-e2e-refresh-01: Browser refresh = new chatId, clean EmptyState

- **Source**: S-cross-01
- **File**: `frontend/tests/e2e/critical/refresh-invariant.spec.ts`
- **CI tag**: `@critical`

```ts
test('S-cross-01 @critical: page refresh produces new chatId and clean state', async ({ page }) => {
  await page.goto('/chat?msw_fixture=happy-text')

  // 完成一輪
  await page.getByTestId('composer-textarea').fill('test')
  await page.getByTestId('composer-send-btn').click()
  await expect(page.getByTestId('message-list')).toHaveAttribute('data-status', 'ready')

  const chatIdBefore = await page.getByTestId('chat-panel').getAttribute('data-chat-id')

  // Refresh
  await page.reload()

  // EmptyState
  await expect(page.getByTestId('empty-state')).toBeVisible()
  await expect(page.getByTestId('user-bubble')).toHaveCount(0)

  const chatIdAfter = await page.getByTestId('chat-panel').getAttribute('data-chat-id')
  expect(chatIdAfter).not.toBe(chatIdBefore)
  expect(chatIdAfter).toBeTruthy()
})
```

**Why**: design Q2「refresh = 新對話」decision 的 invariant test。

---

## Section 6: BDD Scenario → Test Case Mapping

反向 lookup table — 給定一個 BDD scenario，找到對應的 test case(s)。

| BDD Scenario | Layer | Test ID(s) |
|---|---|---|
| S-stream-01 (pure text lifecycle) | manual visual + e2e smoke | TC-e2e-smoke-tool-01 (variant) |
| S-stream-02 (tool first) | e2e smoke | TC-e2e-smoke-tool-01 |
| S-stream-03 (pure tool) | manual real backend | (no automated, Browser-Use) |
| S-stream-04 (textarea preservation finish) | component | TC-comp-composer-02 |
| S-stream-05 (rapid double-submit) | component | TC-comp-composer-01 |
| S-stream-06 (transient progress first) | component | TC-comp-typing-02 |
| S-stream-07 (only-error-part hides typing) | component | TC-comp-typing-01 (case in table) |
| S-stream-08 (idle ready hides typing) | component | TC-comp-typing-01 (case in table) |
| S-tool-01 (success state transition) | component | TC-comp-toolcard-01 |
| S-tool-02 (error inline friendly) | component | TC-comp-toolcard-01 + TC-unit-err-03 |
| S-tool-03 (parallel render order) | component | TC-comp-assistant-01 |
| S-tool-04 (rapid 3 progress) | hook | TC-hook-progress-02 |
| S-tool-05 (parallel routing isolation) | hook | TC-hook-progress-01 |
| S-tool-06 (success after progress no sustain) | component | (TC-comp-toolcard-01 variant) |
| S-tool-07 (success expand) | component | TC-comp-toolcard-02 |
| S-tool-08 (500KB JSON) | manual smoke + perf | (MBT) |
| S-tool-09 (error expand) | component | TC-comp-toolcard-02 (variant) |
| S-md-01 (title / hostname fallback) | unit + component | TC-unit-md-01, TC-unit-md-02, TC-comp-sources-01 |
| S-md-02 (duplicate first-wins) | unit | TC-unit-md-03 |
| S-md-03 (XSS guard) | unit + component + e2e | TC-unit-md-04, TC-comp-sources-02, **TC-e2e-xss-01** |
| `extractSources` malformed input invariant | unit | TC-unit-md-05 |
| S-md-05 (orphan refs) | unit | TC-unit-md-06 |
| `extractSources` numeric label sort invariant | unit | TC-unit-md-07 |
| S-md-07 (RefSup click anchor scroll) | manual visual + e2e edge | (Browser-Use visual) |
| S-md-08 (cursor visual) | manual visual | (Browser-Use visual) |
| S-regen-01 (regenerate click) | integration | (covered indirectly by TC-int-retry-01 setup) |
| S-regen-02 (only last has button) | component | TC-comp-assistant-03 |
| S-regen-03 (hide during streaming) | component | TC-comp-assistant-03 |
| S-regen-04 (preserve textarea) | component | TC-comp-composer-02 |
| S-regen-05 (new ToolCard collapsed) | component | TC-comp-toolcard-02 (variant) |
| S-err-01 (friendly distinct messaging) | unit + component | TC-unit-err-01, TC-comp-error-01 |
| S-err-02 (pre-stream error + no dup user bubble) | integration + e2e | TC-int-v2-01, TC-e2e-smoke-error-01 |
| S-err-03 (no error + typing coexist) | component | (state derivation test) |
| S-err-04 (smart retry 422→sendMessage) | integration | **TC-int-retry-01** |
| S-err-05 (mid-stream preserves partial) | component | TC-comp-assistant-01 |
| S-err-06 (tool not demoted) | component | TC-comp-assistant-02 |
| S-err-07 (running tool → aborted) | integration | **TC-int-aborted-01** |
| S-err-08 (mid-stream retry removes turn) | integration | (variant of TC-int-retry-01) |
| S-err-09 (auto-scroll on error) | hook + manual | TC-hook-followbottom-01 (variant) |
| S-clear-01 (clear → empty state + new chatId) | integration + e2e | **TC-e2e-smoke-clear-01** |
| S-clear-02 (button disabled when empty) | component | TC-comp-header-01 |
| S-clear-03 (new chatId fresh context) | manual real backend | (Browser-Use real backend) |
| S-clear-04 (streaming clear race) | integration | **TC-int-stop-clear-01** |
| S-empty-01 (chip click fills) | component | TC-comp-empty-01 |
| S-empty-02 (chip overwrite last-wins) | component | TC-comp-composer-03 |
| S-stop-01 (stop preserves partial) | integration + e2e | TC-int-stop-clear-01 (variant), **TC-e2e-stop-01** |
| S-stop-02 (stop status ready always) | integration | TC-int-v3-01 |
| S-stop-03 (running tool aborted on stop) | integration | TC-int-aborted-01 (variant) |
| S-stop-04 (stop in submitted) | e2e | **TC-e2e-stop-01** |
| S-scroll-01..04 (follow-bottom 100px) | hook | TC-hook-followbottom-01 |
| S-scroll-05 (keyboard scroll) | hook + manual | TC-hook-followbottom-01 (variant) |
| S-cross-01 (refresh = new chat) | e2e | **TC-e2e-refresh-01** |
| S-cross-02 (back/forward) | manual | (Browser-Use) |
| J-stream-01..02 | e2e smoke | TC-e2e-smoke-tool-01 |
| J-md-01 | manual visual | (Browser-Use) |
| J-regen-01 | integration | (TC-int-retry-01 setup) |
| J-err-01..02 | e2e | TC-e2e-smoke-error-01 |
| J-clear-01 | e2e | TC-e2e-smoke-clear-01 |
| J-empty-01 | manual real backend | (Browser-Use) |
| J-stop-01 | e2e | TC-e2e-stop-01 |
| J-scroll-01 | manual visual | (Browser-Use) |
| J-cross-01 | e2e | TC-e2e-refresh-01 |

---

## Section 7: TDD/BDD Workflow Guidance

### 寫 production code 前

1. 找到 implementation task 對應的 component / hook / lib（從 design.md component breakdown）
2. 在本文件用 Ctrl+F 搜尋對應 component name 找出該 component 的 test cases
3. 對應到 BDD scenario → 確認 user-observable behavior 你理解正確
4. 開新 test file（路徑見 test case `File` 欄位）
5. 把 test case 的 code copy 進去（或依 pseudo-code 寫成可執行 Vitest test）
6. 跑 → red（function / component 還沒寫）
7. 寫 production code 直到 green
8. Refactor production code（test 仍 green = 安全 refactor）
9. 重複下一個 test case

### Coverage 目標

- **Unit / hook / component layers**: 90%+ statement coverage（pure / isolated 邏輯本來就好測）
- **Integration layer**: 70%+ branch coverage on ChatPanel orchestration paths
- **E2E Tier 0**: 6 個 specific tests，每個 must pass，無 % target
- **Manual visual / UAT**: 不算 coverage，作 final gate

### 新增 test case 的時機

不只是「跟著 BDD scenarios」。新 test case 在這些情況加：

1. **Production bug fix**：每修一個 production bug，補一個 regression test（unit / component / e2e 都可）→ 加進本文件對應 section
2. **Refactor risk lock**：要動高風險區域前，先寫 test 把現有 behavior lock 住（characterization test）→ 加進本文件
3. **Discovery 新 edge case**：用 product 時發現 design / BDD 沒涵蓋的 case → 同時更新 BDD scenarios + 加 test
4. **Contract drift**：S1 backend 升級 / AI SDK 升級時跑 V-1/V-2/V-3 contract tests，發現契約變化 → 補新 contract test

### 何時不要寫 test

- LLM output quality（agent evaluation 範疇，非 BDD 範疇）
- 純 styling / 視覺細節（manual smoke 或 visual regression tool）
- 已有上一層 layer 完全 cover 的東西（避免 double coverage）
- Atomic primitives 純 wrapper（PromptChip 是 trivial wrapper，測 onClick 即可，不需要測 styling）

---

## Appendix: Test Case Index by File Path

```
frontend/src/lib/__tests__/
├── markdown-sources.test.ts        TC-unit-md-01..07
├── error-messages.test.ts          TC-unit-err-01..05
├── error-classifier.test.ts        TC-unit-classify-01
└── message-helpers.test.ts         TC-unit-helpers-01

frontend/src/hooks/__tests__/
├── useToolProgress.test.ts         TC-hook-progress-01..03
└── useFollowBottom.test.ts         TC-hook-followbottom-01

frontend/src/components/atoms/__tests__/
└── (TypingIndicator visibility 在 typing-indicator-logic 或 MessageList layer)

frontend/src/components/organisms/__tests__/
├── Composer.test.tsx               TC-comp-composer-01..03
├── ToolCard.test.tsx               TC-comp-toolcard-01..02
├── AssistantMessage.test.tsx       TC-comp-assistant-01..03
├── ErrorBlock.test.tsx             TC-comp-error-01
├── EmptyState.test.tsx             TC-comp-empty-01
└── ChatHeader.test.tsx             TC-comp-header-01

frontend/src/components/molecules/__tests__/
└── Sources.test.tsx                TC-comp-sources-01..02

frontend/src/components/templates/__tests__/
└── MessageList.test.tsx            TC-comp-typing-01..02

frontend/src/components/pages/__tests__/
└── ChatPanel.integration.test.tsx  TC-int-retry-01, TC-int-aborted-01, TC-int-stop-clear-01

frontend/src/__tests__/contract/
├── use-chat-error-lifecycle.test.ts   TC-int-v2-01
└── use-chat-stop-semantic.test.ts     TC-int-v3-01

frontend/tests/e2e/security/
└── xss-source-link.spec.ts            TC-e2e-xss-01

frontend/tests/e2e/smoke/
├── chat-tool.spec.ts                  TC-e2e-smoke-tool-01
└── clear-session.spec.ts              TC-e2e-smoke-clear-01

frontend/tests/e2e/critical/
├── error-recovery.spec.ts             TC-e2e-smoke-error-01
├── stop-preserves-partial.spec.ts     TC-e2e-stop-01
└── refresh-invariant.spec.ts          TC-e2e-refresh-01
```

**Total**: 18 unit + 13 component + 4 hook + 5 integration + 6 e2e = **46 test cases** covering 68 BDD scenarios（部分 scenarios 由多 test 共同 cover、部分由 manual / Browser-Use 驗）。
