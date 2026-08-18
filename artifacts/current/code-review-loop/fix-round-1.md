# Fix Round 1

> Fixer: Claude (code-fixer subagent) | Date: 2026-08-18
>
> Issue list agreed at the Round 1 discussion gate. Four findings were dismissed by the
> user and were NOT sent to the fixer (see "Dismissed at the gate" below).

### Fixed

| Issue ID | How Fixed | Files Changed |
|----------|-----------|---------------|
| M-1.3 / SP-1.1 | `showBody = expanded` (an explicit collapse now wins over a live part). `data-state` left tracking the part lifecycle — `streaming` even when collapsed — while `aria-expanded` follows `showBody`; the decoupling is documented in the component JSDoc and in the DOM contract's `data-state` section (all three enum values reworded in lifecycle terms). New test: streaming + `expanded={false}` → no body, `data-state="streaming"`, `aria-expanded="false"`. | `frontend/src/components/organisms/ReasoningChip.tsx`, `docs/frontend_dom_contract.md`, `frontend/src/components/organisms/__tests__/ReasoningChip.test.tsx` |
| M-1.1 | Rewrote the `observe` JSDoc contract: it must be called from a `useLayoutEffect`, never during render (React forbids writing/reading `ref.current` while rendering, lazy init excepted), plus the behavioural-equivalence argument (a streaming chip shows `Thinking…` with no seconds, and on the freezing render `getSeconds` falls back to the live `Date.now() - startedAt`, which rounds to the same integer second). Implementation unchanged. `hooks/README.md`'s `useReasoningTimers` row makes no render-time claim, so it needed no edit for this item. | `frontend/src/hooks/useReasoningTimers.ts` |
| M-1.2 | `git mv` of component + test into `organisms/`. The test's `../ReasoningChip` import still resolves (verified by running it). Grep confirmed zero other call sites. Architecture doc: moved out of the `molecules` subgraph into `organisms`, off `moleculeCls` onto `organismCls`, and from the molecules table row to the organisms row. | `frontend/src/components/organisms/ReasoningChip.tsx`, `frontend/src/components/organisms/__tests__/ReasoningChip.test.tsx`, `docs/frontend_chat_architecture.md` |
| M-1.4 (partial) | `stalled` prop JSDoc rewritten to describe the behaviour (streaming header swaps to the degraded "Still working…" copy while the global stall stopwatch has fired). Dropped `(C4)` from the test name. ADR-0015's `v1 chips` left untouched per the user's dismissal. | `ReasoningChip.tsx`, `ReasoningChip.test.tsx` |
| m-1.1 | Header button gets `aria-label={`${headerLabel} — ${showBody ? "collapse" : "expand"} reasoning`}` — built from the same `headerLabel` the visible span renders, so it tracks the live copy and the toggle direction. Test asserts the accessible name via `getByRole("button", { name })` across three states. | `ReasoningChip.tsx`, `ReasoningChip.test.tsx` |
| m-1.2 | Budget count Two → Three, with a third entry for `useReasoningTimers`'s `timingsRef`. ADR-0015's consequence narrowed to "the one piece of non-derived frontend state the reasoning chips introduce". | `frontend/src/hooks/README.md`, `docs/adr/0015-reasoning-as-collapsed-transcript-chips.md` |
| m-1.3 | Stripped `(DEV-105)`; swept the whole ADR for other ticket refs (`DEV-`/`HQ-`/`#N`) — none remain. | `docs/adr/0015-reasoning-as-collapsed-transcript-chips.md` |
| SP-1.3 | Effect guarded with `if (!streaming || !showBody) return;` and `showBody` added to the dep array, so it only runs when the body node exists and re-pins on re-expand. Two tests added, stubbing `scrollHeight`/`scrollTop` on `HTMLElement.prototype` and restoring them in `afterEach`: growth-repins, and collapsed→re-expanded repins. Mutation-checked — disabling the effect fails both. | `ReasoningChip.tsx`, `ReasoningChip.test.tsx` |
| SP-1.4 | New `DOM contract attributes` describe block pins `data-state` + `aria-expanded` for streaming-expanded, streaming-collapsed, done-collapsed (`data-state="collapsed"`, previously unasserted) and done-expanded, plus a `data-round` ordinal assertion (1 → 3). | `ReasoningChip.test.tsx` |

### Not Fixed (with reason)

None.

### Reverted (fix broke tests)

None.

### Dismissed at the gate (user decision — never sent to the fixer)

| Issue ID | User's reason |
|----------|---------------|
| M-1.4 (`v1 chips` sub-item) | "v1" is ordinary version prose, not a session-scoped process label; a future reader understands it. |
| S-1.1 (animate SVG wrapper) | A 14px chevron rotating once per click; a wrapper element buys no measurable gain. Envelope §7 rubric item 4 — mention once, never block. |
| SP-1.2 (timer freeze-boundary test gap) | Disproven by orchestrator mutation test: patching the impl to freeze on `part.state === "done"` failed 2 of 6 existing tests. The suite already pins the boundary. |
| — | (m-1.3 was initially recommended for dismissal by the orchestrator; the **user overrode** that and required the fix — ADR bodies carry no issue IDs at all.) |

### Tests Run

| Test Command | Result | Notes |
|--------------|--------|-------|
| `pnpm test src/components/organisms/__tests__/ReasoningChip.test.tsx` | ✅ Pass | 16 tests |
| Mutation check (pinning effect early-returned, then restored) | ✅ 2 failed as expected | Confirms the pinning tests are not vacuous |
| `pnpm lint` | ✅ Pass | 1 pre-existing warning on `public/mockServiceWorker.js`, untouched |
| `pnpm format:check` | ✅ Pass | No reformat needed |
| `pnpm build` (`tsc -b` + vite) | ✅ Pass | Only the pre-existing >500kB chunk advisory |
| `pnpm test` (full suite) | ✅ Pass | 25 files, 243 tests |

**Orchestrator re-verification:** `pnpm test` re-run independently → 25 files / 243 tests pass (was 235 before the round; +8 new). `git status` matches the reported file set: 5 modified + 2 renames, nothing committed, `artifacts/` untouched.

### Tests Added or Modified

| Test File | Added/Modified | What It Tests |
|-----------|----------------|---------------|
| `frontend/src/components/organisms/__tests__/ReasoningChip.test.tsx` | Moved from `molecules/__tests__/` + modified | Removed `(C4)` from a test name; added `header's accessible name carries the live copy plus the toggle action`; added the `DOM contract attributes` block (4 `data-state`/`aria-expanded` cases incl. streaming-but-collapsed, + `data-round` ordinals); added the `streaming window pinning` block (grow-repin and re-expand-repin, with jsdom scroll-metric stubs) |
