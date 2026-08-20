All 9 issues fixed and verified. Working tree left uncommitted per instructions.

### Fixed

| Issue ID | How Fixed | Files Changed |
|----------|-----------|---------------|
| M-1.1 / SP-1.2 | Reverted `aria-hidden="true"` off the `Collapsible` wrapper (and removed the false "D22" comment claiming `LiveStatusAnnouncer` covers tool transitions) — restores pre-diff accessible behavior. Removed the test asserting `aria-hidden="true"` exists. Corrected `README.md`'s ARIA-surfaces bullet from "`ToolCard` stays `aria-hidden`" to "`ToolCard` remains fully accessible (no `aria-hidden`)". | `frontend/src/components/organisms/ToolCard.tsx`, `frontend/src/components/organisms/__tests__/ToolCard.test.tsx`, `frontend/src/components/atoms/README.md` |
| M-1.2 / SP-1.1 | Added `setLastSSEEvent(null)` to `handleRegenerate`, in the same position (before triggering the request) as `handleSend`/`handleRetry`/`handleClearSession`. Added a new integration test covering natural completion → Regenerate → live region clears → second completion → live region announces "Response complete" again. | `frontend/src/components/pages/ChatPanel.tsx`, `frontend/src/components/pages/__tests__/ChatPanel.integration.test.tsx` |
| M-1.5 / SP-1.3 | Removed the "Reasoning transcript" glossary entry (and its `_Avoid_` line) and the "Chat turn" entry's "...and the Reasoning transcript" reference. Left "Chat turn", "Activity indicator", "Stream stall" and the rest of "root trace" untouched since those describe what this diff actually implements. | `CONTEXT.md` |
| M-1.3 + M-1.4 | Made `ErrorBlock`'s `role="alert"` the sole error announcer. In `live-status-text.ts`: removed `errorText` from `AnnouncedEvent` (now just `{ type: "finish" }`) and the `status === "error"` branch; since `status` became fully unused inside `formatStatusText`, dropped it from the signature (kept the interface as a single-field type rather than renaming/restructuring further, per "don't over-refactor"). Cascaded the now-unnecessary `status` prop removal through `LiveStatusAnnouncer` (prop + `ChatStatus` import dropped) and `ChatPanel.tsx`'s render call. Updated both components' doc comments to "finish-only". Rewrote `LiveStatusAnnouncer.test.tsx`: dropped the "error status precedence" describe block and the two error-branch `formatStatusText` unit tests (replaced with one "null event" test), updated all render calls to drop the removed `status` prop. Kept/renamed the `ErrorBlock.test.tsx` `role="alert"` test. Confirmed `ChatPanel.tsx` had no other `errorText`-to-`lastSSEEvent` plumbing to remove. | `frontend/src/components/organisms/ErrorBlock.tsx` (verified, no change needed — already sole `role="alert"` owner), `frontend/src/components/atoms/live-status-text.ts`, `frontend/src/components/atoms/LiveStatusAnnouncer.tsx`, `frontend/src/components/pages/ChatPanel.tsx`, `frontend/src/components/atoms/__tests__/LiveStatusAnnouncer.test.tsx`, `frontend/src/components/organisms/__tests__/ErrorBlock.test.tsx`, `frontend/src/components/atoms/README.md` |
| M-1.6 | Replaced every leaked session-local codename with descriptive text or deletion, restricted to lines this diff actually added (verified against `git diff main...HEAD`, not pre-existing occurrences of the same tokens elsewhere in the codebase — e.g. other pre-existing `DEV-109 ruling 11` mentions in `InterruptedMarker.tsx`, `MessageList.tsx`, `AssistantMessage.tsx`, `useDeadAirPlaceholder.ts` predate this PR and were left alone). Fixture's `scenarios: [...]` → `[]` (its `description` field already stands alone). CSS/test/comment "D22"/"S-rsn-14"/"S-chip-05"/"DEV-109 ruling 11" occurrences reworded or removed (several overlapped with M-1.1/M-1.3/M-1.4's edits above). | `frontend/src/__tests__/msw/fixtures/long-reasoning-then-text.ts`, `frontend/src/index.css`, `frontend/src/components/pages/ChatPanel.tsx`, `frontend/src/components/pages/__tests__/ChatPanel.integration.test.tsx`, plus `ToolCard.tsx`/`ToolCard.test.tsx`/`LiveStatusAnnouncer.test.tsx`/`ErrorBlock.test.tsx` (covered above) |
| m-1.1 | Corrected both `README.md` references from `molecules/ReasoningChip.tsx` / `molecules/__tests__/ReasoningChip.test.tsx` to `organisms/...`. Also fixed "lives one layer up" → "lives two layers up" since atoms→organisms is two layers in this repo's atoms/molecules/organisms/templates/pages hierarchy. | `frontend/src/components/atoms/README.md` |
| m-1.2 | Restored a compact test inside the existing `describe("AssistantMessage — RegenerateButton visibility", ...)` block: `interrupted={true}` + `onRegenerate` provided + all parts "done" → `regenerate-btn` absent. Comment rewritten without the "DEV-109 ruling 11" codename. | `frontend/src/components/organisms/__tests__/AssistantMessage.test.tsx` |
| m-1.3 | Removed "(DEV-106 review fix)"; comment now states directly what's guarded: a new send clearing an already-frozen chip duration. | `frontend/src/components/pages/__tests__/ChatPanel.integration.test.tsx` |

### Not Fixed

None — all 9 issues fixed.

### Reverted

None — no fix broke a test.

### Tests Run

| Test Command | Result | Notes |
|--------------|--------|-------|
| `pnpm -C frontend format` | ✅ Pass | Reformatted `README.md`'s table alignment only; no content change. |
| `pnpm -C frontend lint` | ✅ Pass | 0 errors. 1 pre-existing warning in generated `public/mockServiceWorker.js`, unrelated to this change. |
| `cd frontend && npx tsc -b` | ✅ Pass | No output — confirms the `status`-param removal cascade (live-status-text.ts → LiveStatusAnnouncer.tsx → ChatPanel.tsx) left no dangling unused imports/params under `noUnusedParameters`/`noUnusedLocals`. |
| `pnpm -C frontend test -- --run` (full suite) | ✅ Pass | 269 tests passed across 26 files. |
| `pnpm -C frontend format:check` | ✅ Pass | Re-verified after final edits. |

Note: initial run of the new regenerate test failed once — `happyStream`'s zero-delay SSE response made the "live region cleared" window too transient for `waitFor`'s polling to observe. Fixed by giving the second turn's mock stream a real 300ms hold (matching the pattern other tests in this file already use, e.g. `announcerServer`), then re-verified green.

### Tests Added or Modified

| Test File | Added/Modified | What It Tests |
|-----------|----------------|---------------|
| `frontend/src/components/pages/__tests__/ChatPanel.integration.test.tsx` | Added | "Regenerate clears the live region so a second natural completion announces again" — natural completion → Regenerate → live region clears → second completion → announces "Response complete" again (M-1.2/SP-1.1) |
| `frontend/src/components/organisms/__tests__/AssistantMessage.test.tsx` | Added (restored) | "interrupted turn hides Regenerate even when every part reads complete" (m-1.2) |
| `frontend/src/components/organisms/__tests__/ToolCard.test.tsx` | Removed | Deleted the `aria-hidden="true"` assertion (behavior reverted, so the assertion is now invalid) |
| `frontend/src/components/atoms/__tests__/LiveStatusAnnouncer.test.tsx` | Modified | Dropped error-branch tests/describe block (dead code removed); all remaining tests updated to the `status`-free `formatStatusText`/`LiveStatusAnnouncer` signatures |
| `frontend/src/components/organisms/__tests__/ErrorBlock.test.tsx` | Modified | Test name only (dropped "(D22)" suffix) — same coverage retained |
