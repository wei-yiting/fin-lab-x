# Code Review Round 2

> Reviewer: gpt-5.6-sol | Date: 2026-08-18

## Summary

| Metric | Count |
|--------|-------|
| Total issues | 2 |
| Blocking | 0 |
| Major | 1 |
| Minor | 1 |
| Suggestion | 0 |
| Library checks | 5 |

## Previous Round Status

| # | Issue ID | Status | Notes |
|---|----------|--------|-------|
| 1 | M-1.3 / SP-1.1 | ✅ Fixed | Override wins both directions; lifecycle/visibility decoupling per user ruling |
| 2 | M-1.1 | ⚠️ Partially Fixed | Write path fixed; read path still violates — see M-2.1 |
| 3 | M-1.2 | ✅ Fixed | Moved to `organisms/`, architecture doc updated |
| 4 | M-1.4 (partial) | ✅ Fixed | `consumer #2` and `(C4)` removed |
| 5 | M-1.4 (`v1 chips`) | 🚫 Dismissed (user decision) | Not re-raised |
| 6 | m-1.1 | ✅ Fixed | `aria-label` added; ARIA combination verified clean this round |
| 7 | m-1.2 | ✅ Fixed | Budget Two → Three |
| 8 | m-1.3 | ✅ Fixed | `(DEV-105)` stripped |
| 9 | S-1.1 | 🚫 Dismissed (user decision) | Not re-raised |
| 10 | SP-1.2 | 🚫 Dismissed (user decision) | Not re-raised |
| 11 | SP-1.3 | ✅ Fixed | Pinning tests added and mutation-checked |
| 12 | SP-1.4 | ✅ Fixed | Contract attributes pinned |

## Issues

### [Major] M-2.1: The rewritten timer contract still requires a render-time ref read
- **File:** `frontend/src/hooks/useReasoningTimers.ts` L23-L32, L60-L64; `frontend/src/hooks/__tests__/useReasoningTimers.test.ts` L19-L43
- **Problem:** Moving `observe` into a `useLayoutEffect` fixes its render-time writes, but the new contract explicitly says that "on the freezing render itself `getSeconds` falls back to the live `Date.now() - startedAt`." That requires the consumer to call `getSeconds` while rendering, where the implementation executes the load-bearing code `const timing = timingsRef.current.get(key);`. React 19 forbids reading as well as writing `ref.current` during render except for initialization. The current tests call `getSeconds` imperatively after `act`, so they do not exercise or validate the documented integration path. The rewritten contract is therefore still incompatible with React's purity model; this is Major under the Library/Framework Verification rule, not additional robustness beyond design-envelope §1–§3.
- **Fix:** Preserve the chosen ref-backed hook by calling both `observe` and `getSeconds` from the consumer's `useLayoutEffect`, copying changed frozen values into caller-owned React state, and rendering that state instead of calling `getSeconds` during render. Add a `StrictMode` integration harness that follows this lifecycle. If caller-owned render state is also rejected, return this API to the discussion gate because its current render contract cannot satisfy React's rule.
- **Context7:** React 19.2.4 states not to read or write `ref.current` during rendering except for one-time initialization; `getSeconds` performs a general lookup, not initialization.
- **Vercel rule:** `rerender-use-ref-transient-values`

### [Minor] m-2.1: The exported `ChipState` type has the wrong documentation
- **File:** `frontend/src/lib/reasoning-chips.ts` L24-L30
- **Problem:** The comment `/** Minimal structural view of a chat message shared by the chip hooks. */` is immediately attached to `export type ChipState = "streaming" | "done" | "aborted";`, even though it describes the following `ChatMessageLike` interface. Generated editor documentation consequently misidentifies `ChipState`, while `ChatMessageLike` has no attached explanation. This is misleading API documentation and optional-polish territory under design-envelope §7 rubric item 4.
- **Fix:** Move the existing comment directly above `ChatMessageLike`; give `ChipState` a state-specific comment or leave it uncommented.

## Documentation Gaps

| Folder | Missing |
|--------|---------|
| — | None. The misplaced type comment is a content defect rather than a missing README. |

## Official Standards Check

| Library | Version | API Used | Status | Notes |
|---------|---------|----------|--------|-------|
| React | 19.2.4 | `useRef`, `useLayoutEffect`, `useCallback` | ❌ Wrong | `ReasoningChip` correctly uses `useLayoutEffect` for pre-paint scrolling, and `observe` now writes refs from an effect. The documented render-time call to `getSeconds` still reads `timingsRef.current`, violating React's ref-purity rule. |
| `@testing-library/react` | 16.3.2 | `render`, `renderHook`, `getByRole`, `fireEvent.click` | ✅ Current | `getByRole` correctly verifies accessible names. The configurable `HTMLElement.prototype` metric shadows are deleted after every test and reveal the original inherited `Element` descriptors, so they do not leak. |
| WAI-ARIA | 1.2 | `aria-label`, `aria-live`, `aria-expanded` | ✅ Current | The button retains a descriptive accessible name, `aria-expanded` tracks body visibility, and only status/action text — not streamed body deltas — is inside the polite live region. |
| `lucide-react` | 1.7.0 | `ChevronRight` | ✅ Current | Unchanged from Round 1. |
| Tailwind CSS | 4.2.2 | `[overflow-wrap:anywhere]`, conditional utility classes | ✅ Current | Valid Tailwind v4 arbitrary-property syntax. |

## Vercel Standards Check

| Rule id | Applies? | Verdict | Notes |
|---------|----------|---------|-------|
| `rerender-use-ref-transient-values` | yes — timing data is transient | ⚠️ Violated | Ref-backed storage is appropriate, but the documented rendering path still reads the ref through `getSeconds`. |
| `rerender-derived-state-no-effect` | yes | ✅ Followed | `chipStateOf` and `isChipExpanded` avoid synchronized derived state. |
| `rerender-dependencies` | yes — pinned-scroll layout effect | ✅ Followed | Depends on the primitive values it reads: `text`, `streaming`, `showBody`; re-expanding a live chip re-pins it. |
| `rendering-conditional-render` | yes | ✅ Followed | `showBody` is boolean, avoiding accidental falsy-value rendering. |
| `js-batch-dom-css` | yes | ✅ Followed | One `scrollHeight` read then one `scrollTop` write, no interleaving. |
| `architecture-avoid-boolean-props` | yes | ✅ Followed | `stalled` and `expanded` are independent UI facts. |
| `state-decouple-implementation` | yes | ✅ Followed | `ReasoningChip` receives derived values, does not import the timing hook. |
| `react19-no-forwardref` | no | n/a | No `forwardRef` or public ref prop. |
| `async-*` / `server-*` | no — client-only Vite code | n/a | Next.js/RSC rules do not apply. |

---

# Spec Conformance Round 2

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

✅ SP-1.1 Fixed: explicit collapse now overrides a streaming chip, while explicit expansion overrides completed chips — `frontend/src/components/organisms/ReasoningChip.tsx`
✅ Tail-only expansion with user override in both directions remains pinned by pure-helper tests — `frontend/src/lib/__tests__/reasoning-chips.test.ts`
✅ Lifecycle and visibility are deliberately decoupled as ruled: collapsed streaming chips retain `data-state="streaming"`, set `aria-expanded="false"`, and omit the body — `frontend/src/components/organisms/__tests__/ReasoningChip.test.tsx`
✅ SP-1.3 Fixed: streaming text growth and collapsed-to-expanded transitions both assert bottom pinning against non-zero, changing scroll metrics — `frontend/src/components/organisms/__tests__/ReasoningChip.test.tsx`
✅ SP-1.4 Fixed: `data-state`, `data-round`, `aria-expanded`, companion testids, `aria-live`, and the header accessible name are pinned by tests — `frontend/src/components/organisms/__tests__/ReasoningChip.test.tsx`
✅ The documented DOM contract matches the settled lifecycle/visibility behavior — `docs/frontend_dom_contract.md`
✅ The component's move to the hook-using `organisms` layer is reflected in the architecture map — `docs/frontend_chat_architecture.md`
✅ The component, derivation helper, and timing hook remain dark with no page-level consumer in this segment — `frontend/src/components/organisms/ReasoningChip.tsx`

## Previous Spec Findings — Status

| # | Issue ID | Status | Notes |
|---|----------|--------|-------|
| 1 | SP-1.1 | ✅ Fixed | Override wins in both directions; lifecycle/visibility decoupling is the user's settled ruling |
| 2 | SP-1.2 | 🚫 Dismissed (user decision) | Disproven by orchestrator mutation test; not re-raised |
| 3 | SP-1.3 | ✅ Fixed | Pinning tests assert against non-zero, changing scroll metrics |
| 4 | SP-1.4 | ✅ Fixed | All declared contract attributes pinned |
