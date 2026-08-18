# Code Review Round 3

> Reviewer: gpt-5.6-sol | Date: 2026-08-18

## Summary

| Metric | Count |
|--------|-------|
| Total issues | 1 |
| Blocking | 0 |
| Major | 0 |
| Minor | 1 |
| Suggestion | 0 |
| Library checks | 5 |

> **Reviewer environment note (recorded for honesty of the trail):** targeted Vitest
> execution could not start in the reviewer's sandbox because its Node runtime does not
> export `node:util.styleText`; startup failed before loading project code. This round's
> quality verdict is therefore based on code reading alone. **The orchestrator covered the
> gap**: full suite run independently after the Round 2 fix → 25 files / 245 tests pass,
> plus a mutation test on the loop guard (removing the `return next ?? prev` bail-out makes
> the effect-loop guard test fail). Not counted as a code issue.

## Previous Round Status

| # | Issue ID | Status | Notes |
|---|----------|--------|-------|
| 1 | M-2.1 | ✅ Fixed | `useReasoningTimers.ts` L39-L81 — timing map is React state, `Date.now()` sampled outside the updater, both map and frozen `ChipTiming` cloned, callback deps correct |
| 2 | m-2.1 | ✅ Fixed | `reasoning-chips.ts` L24-L28 — the two JSDoc comments now describe their respective exported types |
| 3 | All Round 1 issues | ✅ Fixed / 🚫 Dismissed | Dismissed items were not re-raised |

## Issues

### [Minor] m-3.1: `chipKey` documentation still describes the removed ref-backed timer
- **File:** `frontend/src/lib/reasoning-chips.ts` L129-L132; `frontend/src/hooks/useReasoningTimers.ts` L39
- **Problem:** The exported helper is documented as a "Stable key for timer refs / override map," but Round 2 replaced the timer ref with `useState<Map<string, ChipTiming>>`. This now contradicts both the implementation (`const [timings, setTimings] = useState...`) and `frontend/src/hooks/README.md`, which correctly calls it a state map. The stale wording makes the public helper documentation misleading.
- **Fix:** Replace "timer refs / override map" with implementation-neutral wording such as "timer and override maps," or explicitly say "timer state / override map."

## Documentation Gaps

| Folder | Missing |
|--------|---------|
| — | None. m-3.1 is a stale-content defect rather than a missing README. |

## Official Standards Check

| Library | Version | API Used | Status | Notes |
|---------|---------|----------|--------|-------|
| React | 19.2.4 | `useState`, `useCallback`, `useRef`, `useLayoutEffect`, `StrictMode` | ✅ Current | `getSeconds` reads React state rather than a ref. The state updater is deterministic from captured `now`, does not mutate `prev` or an existing `ChipTiming`, and returns `prev` when unchanged. The only ref access is inside `useLayoutEffect`, after commit. |
| `@testing-library/react` / `user-event` | 16.3.2 / 14.6.1 | `render`, `renderHook`, `getByRole`, `fireEvent.click` | ✅ Current | `fireEvent.click` is sufficient for the single uncomplicated button activation. The render-count test ties callback identity to the hook's state-map bailout, and the `StrictMode` wrapper exercises updater replay without relying on render-time ref access. |
| WAI-ARIA | 1.2 | `aria-label`, `aria-live`, `aria-expanded` | ✅ Current | The button has a stateful accessible name, `aria-expanded` follows body visibility, and streamed body text remains outside the polite live region. |
| `lucide-react` | 1.7.0 | `ChevronRight` | ✅ Current | Icon API current; `aria-hidden="true"` prevents duplicate accessible content. |
| Tailwind CSS | 4.2.2 | `[overflow-wrap:anywhere]`, conditional utility classes | ✅ Current | Valid Tailwind v4 arbitrary-property syntax. |

## Vercel Standards Check

| Rule id | Applies? | Verdict | Notes |
|---------|----------|---------|-------|
| `rerender-use-ref-transient-values` | yes | ✅ Followed | Rendered timing data lives in React state; the remaining ref is DOM-adjacent and only accessed from `useLayoutEffect`. (Was ⚠️ Violated in Rounds 1–2.) |
| `rerender-functional-setstate` | yes | ✅ Followed | `setTimings(prev => …)` avoids stale state and returns the identical `prev` map on a no-op pass. |
| `rerender-lazy-state-init` | yes | ✅ Followed | `useState(() => new Map())` uses lazy initialization. |
| `rerender-derived-state-no-effect` | yes | ✅ Followed | `chipStateOf` / `isChipExpanded` calculate from current inputs rather than synchronizing state through an effect. |
| `rerender-dependencies` | yes | ✅ Followed | The pinned-scroll effect depends on the primitives it reads: `text`, `streaming`, `showBody`. |
| `rendering-conditional-render` | yes | ✅ Followed | `showBody` and `streaming` are booleans, so `&&` cannot leak `0` or `NaN` into the DOM. |
| `js-batch-dom-css` | yes | ✅ Followed | One `scrollHeight` read then one `scrollTop` write, no interleaved layout reads. |
| `architecture-avoid-boolean-props` | yes | ✅ Followed | `stalled` / `expanded` are independent UI facts; lifecycle stays the explicit `ChipState` union. |
| `state-decouple-implementation` | yes | ✅ Followed | `ReasoningChip` receives derived props, not coupled to `useReasoningTimers`. |
| `react19-no-forwardref` | no | n/a | Internal DOM ref only; no `forwardRef`. |
| `async-*` / `server-*` | no — client-only Vite SPA | n/a | Next.js/RSC/SSR rules do not apply. |

---

# Spec Conformance Round 3

> Reviewer: gpt-5.6-sol | Date: 2026-08-18

## Summary

| Metric | Count |
|--------|-------|
| Total findings | 0 |
| Missing | 0 |
| Scope creep | 0 |
| Misimplemented | 0 |

## Findings

None.

## Covered Requirements

✅ Per-chip wall-clock starts when the part appears and freezes when `msg.parts.length > i + 1 || !chatActive` — `frontend/src/hooks/useReasoningTimers.ts`
✅ Abort duration samples when the chat leaves the active pair — `frontend/src/hooks/useReasoningTimers.ts`
✅ Timing map uses `chipKey(messageId, partIndex)` and preserves frozen durations across turns — `frontend/src/hooks/useReasoningTimers.ts`
✅ A done-but-not-yet-frozen chip reports live-growing elapsed seconds — `frontend/src/hooks/useReasoningTimers.ts`
✅ Hook public surface remains exactly `{ observe, getSeconds, reset }` — `frontend/src/hooks/useReasoningTimers.ts`
✅ Unit tests pin next-part freezing, Stop sampling, live elapsed time, reset, cross-turn isolation, idempotence, and StrictMode behavior — `frontend/src/hooks/__tests__/useReasoningTimers.test.ts`
