# Fix Round 2

> Fixer: Claude (code-fixer subagent) | Date: 2026-08-18
>
> Two issues from Round 2. M-2.1 was fixed in the direction the USER chose (option A —
> move the timing map into React state, owned by the hook), explicitly rejecting the
> reviewer's suggestion of consumer-owned state.

### Fixed

| Issue ID | How Fixed | Files Changed |
|----------|-----------|---------------|
| M-2.1 (Major) | Replaced `timingsRef` with `useState<Map<string, ChipTiming>>(() => new Map())`. `observe` samples `const now = Date.now()` in the function body (outside the updater) and calls `setTimings(prev => …)` with an updater that is pure given `now`. The updater builds `next` lazily — `next ??= new Map(prev)` fires only on the branch that creates a new chip or freezes one — and ends with `return next ?? prev`, so an unchanged pass returns the identical map and React bails out. Freezing writes a new object (`{ ...timing, frozenMs: now - timing.startedAt }`) into the cloned map; nothing is mutated in place. Lookups inside the loop read `(next ?? prev).get(key)` so a create-then-freeze in the same pass still works, preserving the original semantics exactly. `getSeconds` reads the `timings` **state** with unchanged semantics and its `useCallback` dep is `[timings]`. `reset()` is `setTimings(new Map())`. JSDoc contract rewritten, including an explicit statement of the one residual impurity (`Date.now()` during render for a done-but-not-yet-frozen chip) and why it is deliberate. | `frontend/src/hooks/useReasoningTimers.ts`, `frontend/src/hooks/README.md`, `frontend/src/hooks/__tests__/useReasoningTimers.test.ts` |
| m-2.1 (Minor) | Moved `/** Minimal structural view of a chat message shared by the chip hooks. */` back directly above `interface ChatMessageLike`; gave `ChipState` its own one-liner: `/** Lifecycle a reasoning chip's header renders from. */` | `frontend/src/lib/reasoning-chips.ts` |

### Not Fixed (with reason)

None.

### Reverted (fix broke tests)

None.

### Loop-guard reasoning (fixer)

The consumer's chain is `useLayoutEffect → observe → setTimings → (maybe) render → effect again`. It terminates because a pass over unchanged input never allocates: `next` starts `null`, and the only two writes to it are guarded by `if (!timing)` (chip not yet tracked) and `if (timing.frozenMs === null && (hasLaterPart || !chatActive))` (chip freezing now). On a repeat pass every chip is already tracked and every freezable chip is already frozen, so neither branch fires, `next` stays `null`, and the updater returns the identical `prev` reference. React discards the update.

Verified empirically rather than by the state-identity argument alone. Render counts across five successive identical `observe` calls are `[1, 2, 3, 3, 3, 3]`: the first repeat costs **one** extra render. This is React's documented eager-state caveat — the fast path (compute new state at dispatch time and skip scheduling) is only taken when the fiber has no pending lanes, which is not yet true immediately after the previous update committed, so React renders once, sees the same state, and bails out of rendering further. From the second repeat onward the eager path applies. The count plateaus, so the sequence converges after at most one extra render and cannot loop. Had the updater returned a fresh map each time, the count would grow by one every iteration instead of plateauing.

The bail-out and StrictMode interact correctly: React may invoke the updater twice, but with `now` captured outside it the function is deterministic, and both invocations return the same `prev` reference on an unchanged pass.

### Tests Run

| Test Command | Result | Notes |
|--------------|--------|-------|
| `pnpm test src/hooks/__tests__/useReasoningTimers.test.ts` | ✅ Pass — 8/8 | The six pre-existing cases pass **unmodified**; no assertion weakened, no extra `act` needed |
| `pnpm lint` | ✅ Pass — 0 errors | 1 pre-existing warning in generated `public/mockServiceWorker.js`, untouched |
| `pnpm format:check` | ✅ Pass | No reformat needed |
| `pnpm build` (`tsc -b` + vite) | ✅ Pass | Only the pre-existing >500 kB chunk advisory |
| `pnpm test` (full) | ✅ Pass — 25 files, 245 tests | No regressions |

**Orchestrator re-verification:** full suite re-run independently → 25 files / 245 tests pass. **Mutation test on the loop guard:** patching the updater's `return next ?? prev` to `return next ?? new Map(prev)` (i.e. removing the bail-out) makes `re-observing identical input changes nothing and stops re-rendering (effect-loop guard)` fail with `expected [Function] to be [Function] // Object.is equality`. Restored → 8/8 pass. The guard is genuinely pinned, not vacuous.

### Tests Added or Modified

| Test File | Added/Modified | What It Tests |
|-----------|----------------|---------------|
| `frontend/src/hooks/__tests__/useReasoningTimers.test.ts` | Added — `re-observing identical input changes nothing and stops re-rendering (effect-loop guard)` | Calls `observe` with identical input five times through a render-counting wrapper. Asserts `getSeconds` keeps the same identity across repeats — it is a `useCallback` over `[timings]`, so unchanged identity proves the updater returned `prev`. Then asserts the render count plateaus, with the one-extra-render caveat recorded in a comment |
| `frontend/src/hooks/__tests__/useReasoningTimers.test.ts` | Added — `StrictMode double-invocation leaves durations intact` | Renders the hook via `renderHook(…, { wrapper })` with a `<StrictMode>` wrapper (built with `createElement` so the file stays `.ts`) and replays the tool-round freeze scenario: still exactly 3s, tool execution still excluded |
| `frontend/src/hooks/__tests__/useReasoningTimers.test.ts` | Modified — imports only | Added `StrictMode`, `createElement`, `type ReactNode`. No existing test body touched |
