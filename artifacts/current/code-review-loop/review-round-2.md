# Code Review Round 2

> Reviewer: gpt-5.6-sol | Date: 2026-08-17

## Summary

| Metric | Count |
|--------|-------|
| Total issues | 2 |
| Blocking | 0 |
| Major | 0 |
| Minor | 2 |
| Suggestion | 0 |
| Library checks | 7 |

All approved Round 1 fixes are present. The user-dismissed portions of M-1.3, m-1.2, and SP-1.1 were not re-raised. The fixer reported no “Not Fixed” items.

Read-only checks: targeted ESLint, Prettier, and `git diff --check` passed. Vitest could not run because the sandbox prevented Vite from creating `node_modules/.vite-temp`; the fixer's recorded test run was therefore verified by inspection rather than rerun.

## Previous Round Status

| # | Issue ID | Status | Notes |
|---|----------|--------|-------|
| 1 | M-1.1 | ✅ Fixed | Memo-stable `{ messages, hasPlaceholder }` scrollTrigger; mutation-checked. |
| 2 | M-1.2 | ✅ Fixed | Delegation to `ai`'s official guards; false SSOT comment corrected. |
| 3 | M-1.3 | ⚠️ Partially Fixed | Doc half fixed. "Inline the atom" half 🚫 Dismissed (user decision). |
| 4 | M-1.4 | ✅ Fixed | Both params and unreachable branches removed. |
| 5 | m-1.1 | ✅ Fixed | Shared `REF_DEF_LINE_RE`; regex widened to `^ {0,3}`. |
| 6 | m-1.2 | ⚠️ Partially Fixed | Stale content fixed. "Delete the READMEs" 🚫 Dismissed (contradicts DEV-106 AC). |
| 7 | m-1.3 | ✅ Fixed | Throttle comment restored to ~20Hz / ~3 frames. |
| 8 | SP-1.1 | 🚫 Dismissed (user decision) | Current rendering stays. |
| 9 | SP-1.2 | ✅ Fixed | `atoms/__tests__/ActivityPlaceholder.test.tsx` added. |
| 10 | SP-1.3 | ✅ Fixed | Stall case now drives non-renderable whitespace deltas; mutation-checked. |

## Issues

### [Minor] m-2.1: The new AssistantMessage rendering behavior lacks direct regression coverage
- **File:** `frontend/src/components/organisms/AssistantMessage.tsx` L112
- **Problem:** Widening `REF_DEF_LINE_RE` correctly makes `AssistantMessage.displayText` strip reference definitions indented by up to three spaces. However, the new tests exercise only `hasVisibleReplyText`; the existing `AssistantMessage` no-flicker test still covers only a column-zero definition. The user-visible cross-file behavior is therefore not directly proven under design-envelope §5. Reverting this consumer to its old literal would leave all newly added tests green while allowing an indented definition to appear during streaming.
- **Fix:** Parameterize the existing `AssistantMessage — citation rendering` streaming test with zero and three leading spaces, asserting that the raw definition URL never renders. Reuse the existing test rather than adding another test module.

### [Minor] m-2.2: The concrete composition graph retains the old component ownership
- **File:** `docs/frontend_chat_architecture.md` L104
- **Problem:** The change moved placeholder derivation and `ActivityPlaceholder` construction into `ChatPanel` (`ChatPanel.tsx` L240), while `MessageList` now receives and renders an opaque `ReactNode`. The graph still says `MessageList --> ActivityPlaceholder` and omits `ChatPanel --> ActivityPlaceholder`, even though sibling slot content such as `EmptyState` and `ErrorBlock` is attributed to `ChatPanel`. This makes the graph’s claimed “actual compositions” inaccurate.
- **Fix:** Replace `MessageList --> ActivityPlaceholder` with `ChatPanel --> ActivityPlaceholder`, consistent with the actual import and construction site.

## Documentation Gaps

None. The required `atoms`, `pages`, and `hooks` READMEs exist and their Round 1 stale-content issues are fixed.

## Official Standards Check

| Library | Version | API Used | Status | Notes |
|---------|---------|----------|--------|-------|
| `ai` | 6.0.142 | `DefaultChatTransport`, `isToolUIPart`, `isReasoningUIPart` | ✅ Current | Round 2 delegation is correct. The string guard makes `isToolUIPart` total for optional structural `type`; `isReasoningUIPart` safely compares `type` directly. Unemitted approval, `output-denied`, and preliminary-result paths do not justify speculative handling under design-envelope §0. |
| `@ai-sdk/react` | 3.0.144 | `useChat`, `onData`, `status`, `stop` | ✅ Current | Unchanged since Round 1. |
| `react` | 19.2.4 | Hooks, including `useMemo` and `useLayoutEffect` | ✅ Current | Current APIs; placeholder visibility is included in a memo-stable scroll trigger. |
| `@testing-library/react` | 16.3.2 | `render`, `renderHook`, `act`, `waitFor`, `fireEvent` | ✅ Current | Unchanged, current APIs. |
| `vitest` | 4.1.2 | Mocks, fake timers, assertions | ✅ Current | Unchanged, current APIs. |
| `msw` | 2.13.4 | `setupServer`, `http.post`, `HttpResponse` | ✅ Current | Unchanged, current MSW 2 APIs. |
| `@playwright/test` | 1.59.0 | `test`, locator assertions | ✅ Current | Unchanged, current APIs. |

---

# Spec Conformance Round 2

> Reviewer: gpt-5.6-sol | Date: 2026-08-17

## Summary

| Metric | Count |
|--------|-------|
| Total findings | 3 |
| Missing | 0 |
| Scope creep | 0 |
| Misimplemented | 3 |

## Findings

### [Blocking] SP-2.1: Stall stopwatch 並非由任何 stream part 歸零
- **Type:** Misimplemented
- **Spec:** "全域單一 10s stall 碼表(任何 stream part 歸零)" (Source 2, DEV-106 Frontend requirements)
- **File:** `frontend/src/components/pages/ChatPanel.tsx` L88
- **Problem:** Native chunk 的 reset 僅依賴 throttled `messages` identity 更新；`onData` 則只涵蓋 `data-*`。AI SDK 6 的 `processUIMessageStream` 對 `start-step` 與 `finish-step` 不呼叫 `write()`，因此不觸發 `messages` render，也不觸發 `onData`。這些 stream parts 抵達時 stopwatch 不會歸零；例如 stall 後收到 `finish-step`、下一輪內容仍未抵達，placeholder 不會恢復 `Thinking`。Round 1 新增的 whitespace `text-delta` assertion 已修復 SP-1.3 所指出的 mutation gap，但只證明會寫入 `messages` 的 part，未證明「任何 stream part」。
- **Fix:** 在 AI SDK 過濾或 throttle 前的 UIMessageStream chunk 邊界接入 `notifyActivity`，確保每個 chunk 都歸零；並在現有唯一一個 ChatPanel stall integration case 中，以不觸發 `messages` write 的 `finish-step` 或 `start-step` 驗證恢復，不要新增第二個 stall case。

### [Blocking] SP-2.2: Round-1 fixes 破壞 final-tree byte identity 硬檢核
- **Type:** Misimplemented
- **Spec:** "Train 疊完 tree 與 refactor 終態 byte-identical(diff 為空)" (Source 1, DEV-110 acceptance criteria)
- **File:** `frontend/src/hooks/useDeadAirPlaceholder.ts` L48
- **Problem:** Orchestrator 的 identity check 是針對 `8280c61`；目前 working tree 又修改了先前確認與 final tree identical 的 `useDeadAirPlaceholder.ts`、`useStallTimer.ts`、`ActivityPlaceholder.tsx`、`timing.ts`、`markdown-sources.ts` 與 stall tests，並新增 final tree 不存在的 `ActivityPlaceholder.test.tsx`。`MessageList` follow-bottom 與 official guard fixes 也不同於目前 final tree。若 downstream segments 仍按既有 segment 5/6 diff 疊加，最終 tree 不會再與 `feat/multi-provider-streaming-reasoning` byte-identical。
- **Fix:** 將核准的 fixes 先套用至 canonical final tree，重新驗證該終態並由它重建/rebase downstream segments；若終態不可變，則須還原 current-only deviations。完成後重新執行整棵 train 對 final tree 的 byte diff，確認為空。

### [Major] SP-2.3: Segment 4 超出 300–800 行 gate，且沒有獲准例外
- **Type:** Misimplemented
- **Spec:** "300–800 行 gate 以總 diff(含測試)為準,盡量遵守;兩段裁決超線(理由見各段備註)。" (Source 1, eight-segment ruling)
- **File:** `frontend/src/hooks/__tests__/useDeadAirPlaceholder.test.ts` L1
- **Problem:** Committed PR 已有 1,210 行總 diff；目前 working tree 為 1,349 行 tracked diff，再加 38 行 untracked component test，共 1,387 行。裁決只明確允許 segments 6、7 超線，segment 4 仍標示約 800 行，因此目前拆法不符合 slice contract。
- **Fix:** 重新拆分 segment 4，使其在保留獨立部署能力與必要驗證的前提下回到 800 行內；若無法形成 coherent slice，必須先取得 human adjudication，將 segment 4 明列為第三個超線例外並更新 ruling。

## Covered Requirements

✅ Round-1 SP-1.2 已修復：真實 `ActivityPlaceholder` component test 覆蓋 Waiting、Waiting+degraded 與 `aria-live="polite"` — `frontend/src/components/atoms/__tests__/ActivityPlaceholder.test.tsx`
✅ Round-1 SP-1.3 的原始缺口已修復 — `frontend/src/components/pages/__tests__/ChatPanel.integration.test.tsx`
✅ Segment 4 已立即接入 placeholder，且不依賴 reasoning profile — `frontend/src/components/pages/ChatPanel.tsx`
✅ Window A / B / C 推導正確，completed tool cards 可進入 window C — `frontend/src/hooks/useDeadAirPlaceholder.ts`
✅ Placeholder 三狀態、polite live region、無 reasoning 文字 — `frontend/src/components/atoms/ActivityPlaceholder.tsx`
✅ Production stall threshold 固定 10 秒並由 fake-timer unit test 鎖定 — `frontend/src/hooks/__tests__/useStallTimer.test.ts`
✅ Visibility derivation 僅使用 `(status, messages)`；未恢復 latch / dual guard / auto-hide — `frontend/src/hooks/useDeadAirPlaceholder.ts`
✅ 舊 `ReasoningIndicator` 檔案群已移除，且不存在 `abortedMessages` — `frontend/src/components/atoms/ReasoningIndicator.tsx`
✅ `ai@6.0.142` delegation 正確 — `frontend/src/lib/reasoning-chips.ts`
✅ 三格內縮 reference definition 不會錯誤終止 placeholder；0/3/4-space 邊界已有測試 — `frontend/src/lib/markdown-sources.ts`
✅ Segment 5/6 的 chip 元件與 wiring 未提前點亮 — `frontend/src/lib/reasoning-chips.ts`
✅ Touched-module READMEs 已同步 — `frontend/src/hooks/README.md`

---

# Orchestrator Fact-Check (Round 2)

## m-2.1 — CONFIRMED
`frontend/src/components/organisms/__tests__/AssistantMessage.test.tsx` citation cases use
only column-zero definitions (L301, L371, L413) plus one bullet-prefixed case (L392). No
indented case exists, so reverting `AssistantMessage`'s import back to the old inline
literal would leave every new test green. The mutation argument holds.

## m-2.2 — CONFIRMED
`ActivityPlaceholder` is imported in exactly two places: `ChatPanel.tsx:14` (production)
and its own test. `MessageList` receives an opaque `ReactNode`. The graph in
`docs/frontend_chat_architecture.md` attributes the sibling slot contents `EmptyState` and
`ErrorBlock` to `ChatPanel`, so `MessageList --> ActivityPlaceholder` is inconsistent with
the document's own convention. Note this edge was *renamed* by this PR (it previously read
`MessageList --> ReasoningIndicator`, which was accurate then — `MessageList` did import it).

## SP-2.1 — technical premise CONFIRMED, remedy DISPUTED
Verified in `frontend/node_modules/ai/dist/index.js`: `write()` is called per-case inside
the chunk switch, and neither step case calls it.

```js
case "start-step": { state.message.parts.push({ type: "step-start" }); break; }   // no write()
case "finish-step": { state.activeTextParts = {}; state.activeReasoningParts = {}; break; } // no write()
```

So neither chunk re-renders `messages`, and `onData` fires only for `data-*`. The
stopwatch is genuinely not reset by these two frames.

Practical impact is much smaller than Blocking implies:
- `start-step` pushes a `step-start` part that is flushed by the *next* chunk that does
  call `write()` — and that chunk resets the stopwatch anyway. Harmless.
- `finish-step` produces no visible change at all. Reverting the copy from
  "Still working" to "Thinking" on an invisible protocol frame, while the screen still
  shows nothing new, is arguably worse UX than leaving it degraded.

The proposed remedy — tapping raw UIMessageStream chunks before AI SDK's filtering —
would require a transport wrapper or stream interception, and directly contradicts
DEV-106's foundational requirement: 「純 derivation:一切輸入 = `useChat` 的
`(status, messages)`;`onData` reasoning 分支、雙 guard ref、`useLayoutEffect` auto-hide、
onFinish/onError latch 全刪」. That side-channel is precisely what the refactor deleted.
The implementation's actual rule — "any chunk that materializes into `messages` resets" —
is consistent with the rest of the design (`isRenderablePart`, window A).

## SP-2.2 — factually correct, but already ruled on by the user
Line counts and file list verified. However, the user ruled during the Round 1 gate that
the final tree is a *base*, not an authority: each PR is what actually merges, and findings
in a slice's scope are fixed in that slice. This is therefore not a defect in this PR.
It does carry a real downstream consequence — segments 5–8 were carved from the final
tree and now need rebasing onto the corrected segment 4 — which is operational work, not
a fixer task.

## SP-2.3 — CONFIRMED
```
committed PR (c57b4f3..8280c61):  22 files, 1052 insertions, 158 deletions  → 1,210
+ round-1 fixes (tracked):        24 files, 1185 insertions, 164 deletions  → 1,349
+ untracked ActivityPlaceholder.test.tsx: 38                                → 1,387
```
The ruling estimated segment 4 at ~800 and named only segments 6 and 7 as adjudicated
over-line. Note the overage predates this review: the PR was already 1,210 lines (51%
over) when opened. The review's fixes added 177 (~15%). The remedy is a human
adjudication, not a code change.

## CI (orchestrator-run on the working tree)

| Check | Result |
|---|---|
| `pnpm test` | ✅ 22 files / 178 tests |

---

# Orchestrator-Originated Findings (Round 2)

Raised while investigating the user's question "why does this PR exceed the line gate —
is there over-engineering?". **Both Codex reviewers missed both of these.**

Line-count composition of the committed PR (`c57b4f3..8280c61`, insertions + deletions):

```
TEST     676  (56%)
SOURCE   424  (35%)
DOC       79
CSS       31
         ----
        1,210
```

Production source is 424 lines — comfortably inside the slice budget. The overage is
test mass, and its shape is the finding.

### [Major] O-2.1: `reasoning-chips.ts` ships exports with no consumer, contradicting the PR description

- **File:** `frontend/src/lib/reasoning-chips.ts` L76 (`isSuppressedChip`), L8 (`ReasoningPartLike`)
- **Problem:** The module exports six symbols; only four have any external consumer.
  `isSuppressedChip` is referenced solely by `isRenderablePart` at L65 in the same file,
  and `ReasoningPartLike` has zero external references. The PR description asserts:
  "`lib/reasoning-chips.ts` ships only the dead-air-relevant exports (`isReasoningPart`,
  `isToolPart`, `isRenderablePart`, `turnHasRenderableContent`) — the reasoning-chip-specific
  derivations land with the chip component itself later in the stack, so this PR doesn't
  ship unused exports." That claim is false as written, and `isSuppressedChip` is
  chip-named — precisely the category the description says was deferred to segment 5.
- **Fix:** Make `isSuppressedChip` module-private. Keep `ReasoningPartLike` exported only
  if TypeScript requires it to express `isReasoningPart`'s public narrowing; otherwise
  make it local too. Verify with `tsc -b`.

### [Major] O-2.2: Renderability is tested at the wrong layer, which is where the test bloat comes from

- **File:** `frontend/src/hooks/__tests__/useDeadAirPlaceholder.test.ts`;
  missing `frontend/src/lib/__tests__/reasoning-chips.test.ts`
- **Problem:** `reasoning-chips.ts` is 78 lines of pure, dependency-free derivation
  functions and has **no test file at all** — `frontend/src/lib/__tests__/` contains
  `error-classifier`, `error-messages`, `markdown-sources`, and `message-helpers`, but
  nothing for `reasoning-chips`. Its behaviour is instead asserted indirectly through
  `useDeadAirPlaceholder.test.ts`, where each renderability case has to build an
  `assistantMsg()` fixture, call `renderHook`, and drive fake timers inside `act()` —
  10–15 lines for an assertion that costs 2 lines against the pure function. Roughly 5 of
  the 15 hook cases plus an 8-shape loop are renderability assertions in hook-test
  costume ("window (a) stays visible after the `start` frame", "window (c) survives a
  zero-delta suppressed round", "window (c) survives a text delta that normalizes to
  nothing", "zero-delta suppressed chip", "window (c) stays covering when a
  not-yet-painting reasoning part appends"). This is not merely "too many tests" — the
  assertions' intent is obscured by machinery unrelated to what they check.
- **Fix:** Add `frontend/src/lib/__tests__/reasoning-chips.test.ts` covering
  `isReasoningPart` / `isToolPart` / `isRenderablePart` / `turnHasRenderableContent`
  directly, including the zero-delta, whitespace-only, reference-definition-only and
  source-header-only cases. Then reduce `useDeadAirPlaceholder.test.ts` to what only it
  can prove — window A/B/C transitions, grace-delay suppression, the invisible-trailing-part
  behaviour, and status gating — keeping one representative renderability case per window
  rather than enumerating shapes there. Net coverage must not decrease.

### Assessed and rejected as over-engineering (recorded so it is not re-litigated)

| Candidate | Verdict |
|---|---|
| `ChatPanel`'s `notifyActivityRef` + sync effect + `onData` wrapper (~20 lines) | **Load-bearing.** `data-tool-progress` (`backend/agent_engine/streaming/sse_serializer.py:102`) is the system's only transient event and fires throughout a long tool run. Without this reset the placeholder would appear *already degraded* the moment window C opens after a slow tool. The ref itself is forced by hook ordering: `onData` must exist before `useChat`, while `chatActive` derives from `useChat`'s `status`. |
| `useStallTimer`'s wall-clock re-arm branch | **Justified.** Guards against background-tab timer throttling under-counting; a late-firing timeout re-checks real elapsed time before flipping. |
| Three new READMEs (79 lines) | **Required** by a DEV-106 acceptance criterion. |
| Window B derived and tested though unreachable in this slice | **Ratified slice boundary** — the PR description states it, and the hook lights up in segment 6. Contributes to the count but is not a defect. |

### Round 2 disposition

| ID | Disposition |
|---|---|
| m-2.1 | Fix (undisputed) |
| m-2.2 | Fix (undisputed) |
| O-2.1 | Fix (user approved) |
| O-2.2 | Fix (user approved) |
| SP-2.1 | 🚫 **Dismissed (user decision)** — `start-step` / `finish-step` do not reset the stopwatch. Confirmed against `ai@6.0.142` source. Not fixed: both frames are invisible protocol boundaries, reverting the degraded copy on them would erase a correct "you have been waiting a while" signal, and the proposed remedy (tapping raw stream chunks before AI SDK filtering) would violate DEV-106's foundational pure-derivation rule. |
| SP-2.2 | Not a defect — superseded by the user's Round 1 ruling that the final tree is a base, not an authority. Downstream consequence recorded: segments 5–8 need rebasing onto the corrected segment 4. |
| SP-2.3 | Human adjudication pending — after O-2.1/O-2.2 land, take the residual overage to a ruling for a third over-line exception. |
