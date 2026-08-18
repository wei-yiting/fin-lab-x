# Code Review Round 1

> Reviewer: gpt-5.6-sol | Date: 2026-08-17

## Summary

| Metric | Count |
|--------|-------|
| Total issues | 7 |
| Blocking | 0 |
| Major | 4 |
| Minor | 3 |
| Suggestion | 0 |
| Library checks | 7 |

## Issues

### [Major] M-1.1: Grace-delayed placeholder can mount outside the viewport

- **File:** `frontend/src/components/templates/MessageList.tsx` L48
- **Problem:** `useFollowBottom` only receives `messages` as its scroll trigger, while the placeholder is appended separately at L124 after the 300ms grace period. In a long transcript, the terminal tool update first scrolls to the old bottom while the placeholder is hidden. When the placeholder later mounts, `messages` has not changed, so no additional scroll occurs and the placeholder sits below the viewport until the next part removes it. Window C—and eventually B—therefore fails to provide visible feedback in the exact dead-air period it is meant to cover. This can break a live walkthrough under design-envelope §7(3).
- **Fix:** Include placeholder visibility as a memo-stable auto-scroll trigger while preserving the existing `shouldFollowBottom` gate. Add an overflow regression covering terminal tool result → grace elapsed → placeholder visible at the viewport bottom.

### [Major] M-1.2: AI SDK’s official tool-part type guard is reimplemented

- **File:** `frontend/src/lib/reasoning-chips.ts` L34
- **Problem:** `isToolPart` manually duplicates AI SDK’s public `isToolUIPart` logic and returns only `boolean`, discarding the official type narrowing. This is explicitly prohibited by the supplied library-review standard. It also leaves another same-shaped predicate in `AssistantMessage.tsx`, so classification can drift between consumers.
- **Fix:** Import `isToolUIPart` from `ai` and type messages/parts using `UIMessage` or `UIMessagePart`. Use the official guard throughout the placeholder and tool-rendering paths.
- **Context7:** `isToolUIPart` is the current, non-deprecated AI SDK 6 export covering both static `tool-*` and `dynamic-tool` parts.

### [Major] M-1.3: Single-use visual element violates the repository’s extraction rule

- **File:** `frontend/src/components/atoms/ActivityPlaceholder.tsx` L12
- **Problem:** The new component has exactly one consumer at `ChatPanel.tsx` L241. `docs/frontend_chat_architecture.md` L88 explicitly requires visual elements to remain inline until a second occurrence. This is an unearned module under design-envelope §0/§7 and a possible Speculative Generality smell. Its documentation is also already inaccurate: L7 describes two windows although the hook implements three, and L9 says it never appears with a tool card although window C intentionally appears beneath completed tool cards.
- **Fix:** Inline the markup at its sole use and delete the atom. If it is retained despite the repository rule, document all three windows accurately and distinguish running from completed tool cards.

### [Major] M-1.4: Production hooks expose unreachable and test-only timing knobs

- **File:** `frontend/src/hooks/useStallTimer.ts` L15; `frontend/src/hooks/useDeadAirPlaceholder.ts` L48
- **Problem:** The spec fixes the timings at 10s and 300ms, but both hooks expose configurable parameters. `threshold` has no production caller and is selected only by a unit test; `graceMs` is never overridden anywhere, while its `<= 0` branches are unreachable. These are speculative API surface under design-envelope §0/§7, and `threshold` is a production test seam prohibited by §5 rule 4.
- **Fix:** Read `STALL_THRESHOLD_MS` and `PLACEHOLDER_GRACE_MS` directly inside the hooks. Remove both parameters, the unreachable grace-bypass branches, and the custom-threshold-only test. Existing fake timers and the integration module mock already provide deterministic testing.

### [Minor] m-1.1: Valid indented CommonMark definitions are misclassified as visible text

- **File:** `frontend/src/lib/markdown-sources.ts` L81
- **Problem:** `REF_DEF_LINE_RE` only matches definitions beginning at column zero, but CommonMark accepts up to three leading spaces. For `"   [1]: https://example.com"`, `hasVisibleReplyText` returns `true`, closing window A, while `ReactMarkdown` parses the content solely as a definition and renders no visible body. The same regex remains duplicated in `AssistantMessage.tsx` L112, a possible Fowler Duplicated Code smell that undermines the claimed shared rendering predicate.
- **Fix:** Support CommonMark’s permitted indentation and make `AssistantMessage` and `hasVisibleReplyText` call one shared stripping helper. Add a regression covering an indented definition-only delta.

### [Minor] m-1.2: New folder READMEs are redundant and already contain false claims

- **File:** `frontend/src/components/atoms/README.md` L16
- **Problem:** The `atoms` and `pages` inventories duplicate the existing component and frontend architecture documentation, contrary to design-envelope §6. The atoms README is already stale: `StatusDot` is consumed by `ToolRow`, not `ChatHeader`, and L21 claims per-component tests under an `atoms/__tests__` folder that does not exist.
- **Fix:** Delete the redundant `atoms` and `pages` READMEs. Keep non-obvious lifecycle documentation in the existing architecture document or the hooks README only where it materially adds information.

### [Minor] m-1.3: Throttle documentation states the wrong frame duration

- **File:** `frontend/src/lib/timing.ts` L28
- **Problem:** The comment calls a 50ms throttle “one frame’s worth.” At 60Hz, 50ms is approximately three frames. The prior comment was accurate; the changed wording now misleads performance tuning.
- **Fix:** Describe it as approximately three frames at 60Hz, or replace the claim with the measured update frequency of roughly 20Hz.

## Documentation Gaps

No folder requires an additional README. The documentation problem is excessive and stale folder-level documentation, covered by m-1.2.

## Official Standards Check

| Library | Version | API Used | Status | Notes |
|---------|---------|----------|--------|-------|
| `ai` | 6.0.142 | `DefaultChatTransport`, tool-part classification | ❌ Wrong | `DefaultChatTransport` is current, but the change reimplements the current `isToolUIPart` export. Approval/`output-denied` and preliminary outputs are not emitted by the current backend, so design-envelope §0 does not justify adding unreachable handling. |
| `@ai-sdk/react` | 3.0.144 | `useChat`, `onData`, `status`, `stop` | ✅ Current | `onData` is correctly used for transient `data-*` parts; native message parts are observed through `messages`. No throwing path was found in the callback. |
| `react` | 19.2.4 | `useEffect`, `useLayoutEffect`, `useCallback`, refs/state | ✅ Current | No deprecated React API found. |
| `@testing-library/react` | 16.3.2 | `render`, `renderHook`, `act`, `waitFor` | ✅ Current | Usage matches the current testing APIs. |
| `vitest` | 4.1.2 | `vi.mock`, fake timers, assertions | ✅ Current | No deprecated API found. |
| `msw` | 2.13.4 | `setupServer`, `http.post`, `HttpResponse` | ✅ Current | Current MSW 2 APIs are used. |
| `@playwright/test` | 1.59.0 | `test`, locator assertions | ✅ Current | No deprecated or incorrect API found. |

---

# Spec Conformance Round 1

> Reviewer: gpt-5.6-sol | Date: 2026-08-17

## Summary

| Metric | Count |
|--------|-------|
| Total findings | 3 |
| Missing | 2 |
| Scope creep | 0 |
| Misimplemented | 1 |

## Findings

### [Blocking] SP-1.1: Placeholder 未呈現規定的精確文案
- **Type:** Misimplemented
- **Spec:** "文案（英文）：`Thinking…` / `Still working…`。" (Source 3, Context)
- **File:** `frontend/src/components/atoms/ActivityPlaceholder.tsx` L19
- **Problem:** DOM 實際文字是 `Thinking` / `Still working`。省略號由 `aria-hidden` 的 CSS pseudo-element 動畫產生，且會在無點至三個句點間循環；因此 `aria-live` 宣告的文案缺少省略號，視覺文案也不是固定的 spec 字串。E2E 同樣把錯誤的 `Thinking` 鎖成預期值。
- **Fix:** 直接在 live region 內 render 精確字串 `Thinking…` / `Still working…`，移除或調整 decorative dots cycler，並將相關測試改為精確比對含 Unicode ellipsis 的文案。

### [Blocking] SP-1.2: 第三狀態的 component unit coverage 缺失
- **Type:** Missing
- **Spec:** "其餘 3-state 與 chip 邏輯以 hook/component 單元測試覆蓋" (Source 2, DEV-106 acceptance criteria)
- **File:** `frontend/src/components/atoms/__tests__/ActivityPlaceholder.test.tsx` L1
- **Problem:** Changeset 沒有 `ActivityPlaceholder` component unit test。現有 `MessageList` unit test 傳入自行建立的 `<div>`，未 render 真正 component；因此 Waiting 與 Waiting+degraded 對應的文案及 `aria-live="polite"` 沒有 component-level unit coverage。
- **Fix:** 新增 `ActivityPlaceholder` unit test，分別驗證 `stalled=false`、`stalled=true` 的精確文案，以及 `aria-live="polite"`；保留 hook tests 負責 Hidden/Waiting visibility derivation。

### [Blocking] SP-1.3: 唯一的 ChatPanel stall integration case 未驗證 reset wiring
- **Type:** Missing
- **Spec:** "有且僅有 1 個 ChatPanel 整合測試 case(mock 小 threshold + MSW 真實時間)驗 wiring(F6 裁決)" (Source 2, DEV-106 acceptance criteria)
- **File:** `frontend/src/components/pages/__tests__/ChatPanel.integration.test.tsx` L515
- **Problem:** Case 只驗證 silence 觸發 `Still working`，接著立即送出可渲染 reply text 並確認 placeholder 被 answer 取代。即使 `notifyActivity` 完全沒有接上 stream parts，這個測試仍會通過；它沒有驗證任何 part 抵達後，仍存在的 live placeholder 是否由 degraded copy 恢復正常文案。
- **Fix:** 擴充同一個 integration case：stall 後先送出不會取代 placeholder 的 stream part（例如 `text-start` 或 transient `data-*`），確認 placeholder 保持顯示且恢復為 `Thinking…`，再送出 reply text 完成 stream。不要新增第二個 ChatPanel stall case。

## Covered Requirements

✅ Segment 4 的 `useDeadAirPlaceholder`、`useStallTimer` 與 `ActivityPlaceholder` 已立即接入 `ChatPanel`，不依賴 reasoning profile — `frontend/src/components/pages/ChatPanel.tsx`
✅ Window A 涵蓋 `submitted` 及 streaming-but-no-renderable-content，首個 renderable content 後隱藏 — `frontend/src/hooks/useDeadAirPlaceholder.ts`
✅ Window B 由 completed reasoning part 推導，並套用 300ms grace 以避免 chip→tool micro-gap 閃現 — `frontend/src/hooks/useDeadAirPlaceholder.ts`
✅ Window C 在所有 tool parts terminal 後啟動，且 invisible trailing parts 不會提前關閉或重置 grace — `frontend/src/hooks/useDeadAirPlaceholder.ts`
✅ Streaming chip 或執行中的 tool card 存在時 placeholder 隱藏 — `frontend/src/hooks/useDeadAirPlaceholder.ts`
✅ 全域單一 10s stall stopwatch 已實作，native message parts 與 transient `data-*` 都接上 activity reset — `frontend/src/components/pages/ChatPanel.tsx`
✅ Hidden / Waiting / Waiting+degraded 三種 runtime display 組合已由 visibility state 與 stall flag 組合產生 — `frontend/src/components/pages/ChatPanel.tsx`
✅ Placeholder 具 `aria-live="polite"` 且不包含 reasoning 內容 — `frontend/src/components/atoms/ActivityPlaceholder.tsx`
✅ Stop 仍可於 placeholder silence 期間 abort 並回到穩定狀態 — `frontend/src/components/pages/ChatPanel.tsx`
✅ 舊 `ReasoningIndicator`、其 derivation logic 與舊 tests 已刪除 — `frontend/src/components/atoms/ReasoningIndicator.tsx`
✅ Placeholder visibility 由 `(status, messages)` 推導，沒有恢復舊的 reasoning `onData` latch 或 auto-hide guard — `frontend/src/hooks/useDeadAirPlaceholder.ts`
✅ 10s production default 已由 fake-timer hook unit test 鎖定 — `frontend/src/hooks/__tests__/useStallTimer.test.ts`
✅ 三個 dead-air windows、300ms grace、parallel tools 與 zero-renderable trailing parts 均有 hook unit coverage — `frontend/src/hooks/__tests__/useDeadAirPlaceholder.test.ts`
✅ Segment 5/6 的 `ReasoningChip`、chip timers 與 page-level chip wiring 未提前點亮；`reasoning-chips.ts` 僅包含 placeholder 所需 derivations — `frontend/src/lib/reasoning-chips.ts`

---

# Orchestrator Fact-Check (Round 1)

Every finding was verified against the working tree and against the BDD-verified final
tree `feat/multi-provider-streaming-reasoning`, before the discussion gate.

## Verified as factually correct

| Finding | Verification |
|---|---|
| M-1.1 | `MessageList.tsx:48` passes `messages` as the sole `scrollTrigger`; `useFollowBottom`'s effect deps are `[ref, shouldFollowBottom, scrollTrigger]`. The grace timer firing changes only `placeholder`, not `messages` → no re-scroll on placeholder mount. **Final tree has the identical call.** |
| M-1.2 | `reasoning-chips.ts:34` hand-rolls the guard; `ai` exports `isToolUIPart`. `AssistantMessage.tsx:14` holds a *third*, differently-shaped predicate (`t === "tool" \|\| t.startsWith("tool-") \|\| t === "dynamic-tool"`), so `reasoning-chips.ts`'s "Single source of truth" comment is false today. **Final tree has the identical hand-rolled guard.** |
| M-1.3 (doc half) | `ActivityPlaceholder.tsx` L7–9 states two windows (hook implements three) and "never rendered while a tool card … is on screen" (window C renders under *completed* tool cards). Both statements are wrong. `docs/frontend_chat_architecture.md` L88 does contain the extension rule quoted. |
| M-1.4 | `useStallTimer(chatActive)` and `useDeadAirPlaceholder(messages, status)` are the only production call sites — both use defaults. `graceMs` is never overridden by any caller or test; the `graceMs <= 0` branches are unreachable. **Final tree carries the same params.** |
| m-1.1 (dup half) | `AssistantMessage.tsx:112` still inlines `/^\[(\d+)\]:?\s+\S+.*$/gm` verbatim while this PR exports the same literal as `REF_DEF_LINE_RE`. The new comment's "the exact stripping pipeline AssistantMessage applies" is therefore not literally true. |
| m-1.2 (stale half) | `StatusDot` is consumed by `molecules/ToolRow.tsx:48`, not `ChatHeader`. `frontend/src/components/atoms/__tests__/` does not exist, so "Atoms have unit coverage in `__tests__/<Component>.test.tsx`" is false. |
| m-1.3 | The pre-change comment said "about 3 frames at a 60Hz display"; this PR replaced it with "One frame's worth". 50ms ≈ 3 frames at 60Hz — the change made an accurate comment inaccurate. |
| SP-1.1 (fact) | DOM text is `Thinking` / `Still working`; the ellipsis is CSS `::after` content on an `aria-hidden` span. |
| SP-1.2 (fact) | No `ActivityPlaceholder` unit test exists. |
| SP-1.3 (fact) | The stall case asserts only (a) degraded copy appears, (b) `done` renders. It would pass with `notifyActivity` fully disconnected. |

## Context the reviewers lacked

| Finding | Context |
|---|---|
| SP-1.1 | The literal string `Still working…` lives in the **reasoning chip header** (segment 5/6). The final tree's ONE stall integration case asserts `reasoning-chip-header` → `"Still working…"`. The placeholder has always rendered text + an animated CSS dot cycler, and `ActivityPlaceholder.tsx` is **byte-identical** to the tree that passed the full BDD suite and the manual browser phase. |
| SP-1.2 | The final tree has no `ActivityPlaceholder` unit test either — `atoms/__tests__/` contains only `LiveStatusAnnouncer.test.tsx` (a segment-6 component). Pre-existing gap, not dropped by this slice. |
| SP-1.3 | The final tree's version of the same case has the same weakness: its comment claims "The late delta resets the stopwatch → normal copy returns", but the only assertion is `getByText("done")`. Inherited, not introduced. However, the gap **is** constructible in this segment: a whitespace-only `text-delta` is non-renderable per `hasVisibleReplyText`, so it resets the stopwatch while the placeholder stays mounted. |
| M-1.3 (headline) | `ActivityPlaceholder` replaces `ReasoningIndicator`, which occupied the same single-use atom slot. The extension rule governs a *new* visual element at *first* use; this is a like-for-like replacement of an established atom, and DEV-106 names the component explicitly. |
| m-1.2 (headline) | DEV-106 acceptance criterion requires the touched-module READMEs: "動到的模組 README(streaming、hooks、agents、atoms/pages)與新 code 同步,無 drift". "Delete them" contradicts the spec; "fix the drift" is exactly what the criterion asks for. |
| All | DEV-110 carries a hard acceptance criterion: "Train 疊完 tree 與 refactor 終態 byte-identical(diff 為空)". Every fix listed above changes files that are currently byte-identical to the final tree, so each one trades against that criterion. |

## Byte-identity baseline (this PR vs. final tree)

```
IDENTICAL  frontend/src/hooks/useDeadAirPlaceholder.ts
IDENTICAL  frontend/src/hooks/useStallTimer.ts
IDENTICAL  frontend/src/components/atoms/ActivityPlaceholder.tsx
IDENTICAL  frontend/src/lib/timing.ts
IDENTICAL  frontend/src/lib/markdown-sources.ts
IDENTICAL  frontend/src/hooks/__tests__/useDeadAirPlaceholder.test.ts
IDENTICAL  frontend/src/hooks/__tests__/useStallTimer.test.ts
DIFFERS    frontend/src/lib/reasoning-chips.ts               (final +54 −7)
DIFFERS    frontend/src/components/templates/MessageList.tsx (final +21 −13)
DIFFERS    frontend/src/components/pages/ChatPanel.tsx       (final +77 −9)
```

## CI baseline (orchestrator-run, before any fix)

| Check | Result |
|---|---|
| `pnpm format:check` | ✅ |
| `pnpm lint` | ✅ 0 errors (1 pre-existing warning in `frontend/public/mockServiceWorker.js`, untouched by this PR) |
| `pnpm exec tsc -b` | ✅ |
| `pnpm test` | ✅ 21 files / 169 tests |
| `pnpm build` | ✅ |
