# Fix Round 1

> Fixer: Claude (general-purpose subagent) | Date: 2026-08-17
> Dispatched with 9 approved items. 2 review findings were dismissed by the user before
> dispatch and excluded from the fixer's list (SP-1.1 literal copy; M-1.3's "inline the
> atom" half). m-1.2's "delete the READMEs" recommendation was excluded as contradicting
> a DEV-106 acceptance criterion; only its stale-content half was dispatched.

## Fixed

| Issue ID | How Fixed | Files Changed |
|----------|-----------|---------------|
| M-1.1 | `MessageList` derives `hasPlaceholder = placeholder != null` (a boolean, not the fresh-per-render node) and passes a `useMemo`-stable `{ messages, hasPlaceholder }` object as `useFollowBottom`'s `scrollTrigger`. Trigger identity changes when messages change **or** placeholder visibility flips, so the grace-delayed mount gets its scroll. `shouldFollowBottom` untouched — the effect still early-returns when the user has scrolled up. | `frontend/src/components/templates/MessageList.tsx`, `frontend/src/components/templates/__tests__/MessageList.test.tsx` |
| M-1.2 | `isReasoningPart` delegates to `ai`'s `isReasoningUIPart`; `isToolPart` delegates to `isToolUIPart`, keeping a `typeof part.type !== "string"` early return (the SDK guard calls `.startsWith` unguarded, and the hooks pass structurally-typed parts whose `type` may be absent). Local structural signatures preserved; one shared `AnyUIPart` cast alias carries a comment explaining the boundary. The false "single source of truth" claim replaced with an accurate note that `AssistantMessage` holds its own predicate, unifying them being out of slice. `AssistantMessage.tsx`'s predicate itself untouched. | `frontend/src/lib/reasoning-chips.ts` |
| M-1.3 (doc half) | Doc comment rewritten to name all three windows (A submit → first renderable content, B chip collapse → next content, C tool round complete → next content) and to distinguish a *running* tool card (suppressed) from *completed* tool cards (window C renders below them). Markup, copy, behaviour untouched. | `frontend/src/components/atoms/ActivityPlaceholder.tsx` |
| M-1.4 | Removed `useStallTimer`'s `threshold` param and `useDeadAirPlaceholder`'s `graceMs` param; both hooks read `STALL_THRESHOLD_MS` / `PLACEHOLDER_GRACE_MS` directly from `@/lib/timing`. Removed both unreachable `graceMs <= 0` branches. `scheduleCheck`'s dep array is now `[]`. Deleted the `"custom threshold is honored"` test. | `frontend/src/hooks/useStallTimer.ts`, `frontend/src/hooks/useDeadAirPlaceholder.ts`, `frontend/src/hooks/__tests__/useStallTimer.test.ts` |
| m-1.1 | (a) `AssistantMessage.tsx` imports `REF_DEF_LINE_RE` instead of inlining the literal — one definition. (b) Widened to `/^ {0,3}\[(\d+)\]:?\s+\S+.*$/gm` for CommonMark's up-to-three leading spaces. Both call sites use `String.replace`, which resets `lastIndex`; no `.test()` anywhere, so the shared `/g` regex is safe. | `frontend/src/lib/markdown-sources.ts`, `frontend/src/components/organisms/AssistantMessage.tsx`, `frontend/src/lib/__tests__/markdown-sources.test.ts` |
| m-1.2 (content half) | (a) `StatusDot.tsx` row names its real consumer, `molecules/ToolRow`. (b) Testing section rewritten to state the actual end state — one test file in the folder, the rest of the atoms covered through consumers — and to note that visibility derivation belongs to `useDeadAirPlaceholder`, not the component. Both READMEs kept. | `frontend/src/components/atoms/README.md` |
| m-1.3 | Restored an accurate description: "Coalescing into a ~20Hz update rate (about 3 frames at a 60Hz display)". Rest of the reasoning intact. | `frontend/src/lib/timing.ts` |
| SP-1.2 | New unit test rendering the real component: non-degraded copy at `stalled={false}`, degraded copy at `stalled={true}` (each also asserting the other copy is absent), `aria-live="polite"` on the element, `aria-hidden="true"` on the `.thinking-dots` span. No ellipsis assertions (dismissal respected). | `frontend/src/components/atoms/__tests__/ActivityPlaceholder.test.tsx` (new) |
| SP-1.3 | Extended the **same** case (no second case added). The MSW handler now runs three phases: silence past the mocked threshold → degraded copy; then a burst of 12 whitespace (`"\n"`) `text-delta`s spaced at `threshold/4`, which change `messages` (driving `notifyActivity` via the layout effect) but are non-renderable per `hasVisibleReplyText`, so the placeholder stays mounted and its copy must revert to `"Thinking"`; then the real answer. Test renamed to match. | `frontend/src/components/pages/__tests__/ChatPanel.integration.test.tsx` |

## Not Fixed

None.

## Reverted

None.

## Mutation checks (fixer-run: temporary local breakage, then restored)

- **M-1.1** — reverting `scrollTrigger` back to `messages` makes the new test fail
  (`expected 2000, got 0`); the other 10 `MessageList` tests still pass, so the assertion
  isolates exactly the regression.
- **SP-1.3** — disabling the reset wiring in `ChatPanel.tsx`
  (`if (false && chatActive) notifyActivity()`) makes the strengthened case fail; the
  other 6 tests in the file still pass. Before strengthening, that case would have passed
  with the wiring disconnected. `ChatPanel.tsx` restored (absent from `git status`).
- **M-1.4** — the integration file's `vi.mock("@/lib/timing", …)` still drives the hook
  after param removal: the stall case asserts the degraded copy within a 5s timeout,
  reachable only with the mocked 700ms threshold, not the real 10s.

## Tests Run

| Test Command | Result | Notes |
|--------------|--------|-------|
| `pnpm format:check` | ✅ Pass | Initially flagged `MessageList.tsx` and `atoms/README.md`; ran `pnpm format`, re-checked clean. |
| `pnpm lint` | ✅ Pass | 0 errors, 1 warning — the pre-existing unused eslint-disable in `public/mockServiceWorker.js`, untouched by this PR. |
| `pnpm exec tsc -b` | ✅ Pass | Exit 0, no output. |
| `pnpm test` | ✅ Pass | 22 files, 178 tests (was 21 / 169). |
| `pnpm build` | ✅ Pass | Built in 646ms; only the pre-existing >500kB chunk-size advisory. |

## Tests Added or Modified

| Test File | Added/Modified | What It Tests |
|-----------|----------------|---------------|
| `frontend/src/components/atoms/__tests__/ActivityPlaceholder.test.tsx` | Added | Both copy states, `aria-live="polite"`, and `aria-hidden` on the dots cycler, by rendering the real component (SP-1.2). |
| `frontend/src/components/templates/__tests__/MessageList.test.tsx` | Modified | New describe block: placeholder mounting with an unchanged `messages` reference scrolls the viewport to the bottom; companion gate case — a user scrolled 1700px up is not yanked down when the placeholder mounts (M-1.1). |
| `frontend/src/lib/__tests__/markdown-sources.test.ts` | Modified | New `hasVisibleReplyText` block: indented (3-space) definition-only → `false`; column-zero definition → `false`; 4-space indent (a code block, which does paint) → `true`; real prose → `true` (m-1.1). |
| `frontend/src/components/pages/__tests__/ChatPanel.integration.test.tsx` | Modified | The single stall case now also proves the reset half of the F6 wiring — non-renderable stream parts zero the stopwatch and restore the non-degraded copy without closing the dead-air window (SP-1.3). |
| `frontend/src/hooks/__tests__/useStallTimer.test.ts` | Modified | Deleted `"custom threshold is honored"` — the parameter it tested no longer exists (M-1.4). |

## Orchestrator Verification of the Fixer's Work

Read independently against the diff, not taken on report:

| Claim | Verified |
|---|---|
| `isReasoningPart` delegation is safe without a `typeof` guard | ✅ `ai@6.0.142` implements `isReasoningUIPart` as `part.type === "reasoning"` — total for absent `type`. The asymmetry with `isToolPart` (which does need the guard, since `isToolUIPart` calls `.startsWith` unguarded) is correct, not an oversight. |
| Shared `/g` regex is not `lastIndex`-unsafe across two call sites | ✅ Both sites use `String.prototype.replace`, which resets `lastIndex`; no `.test()` / `.exec()` call anywhere on `REF_DEF_LINE_RE`. |
| `shouldFollowBottom` gate preserved | ✅ `useFollowBottom`'s effect still early-returns on `!shouldFollowBottom`; only `scrollTrigger` changed. Companion test covers the scrolled-up case. |
| `AssistantMessage.tsx` predicate untouched | ✅ Only its import line and the `.replace()` argument changed. |
| Behaviour change outside the original slice files | ⚠️ Noted for round 2: widening `REF_DEF_LINE_RE` also changes `AssistantMessage`'s `displayText` stripping — 3-space-indented reference definitions are now stripped there too. This is the intended consequence of making both sides share one definition, but it is a behaviour change in a file the original PR did not touch. |
