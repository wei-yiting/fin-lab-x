---
# Code Review Round 2

> Reviewer: gpt-5.5 | Date: 2026-07-28

## Summary

| Metric | Count |
|--------|-------|
| Total issues | 4 |
| Blocking | 0 |
| Major | 2 |
| Minor | 2 |
| Suggestion | 0 |
| Library checks | 2 |

## Previous Round Status

| # | Issue ID | Status | Notes |
|---|----------|--------|-------|
| 1 | M-1.1 | Fixed | `resetForNewTurn()` no longer clears `resetTimers()`. `handleClearSession()` still performs the full timer wipe. The new hook/integration tests are meaningful and assert the old regression directly. |
| 2 | m-1.1 | Fixed | `verify_langfuse_trace.py` docstring now matches `_check_reasoning_on()`'s per-trace non-empty contract. |
| 3 | m-1.2 | Fixed | `backend/scripts/validation/README.md` fixed the `--expect-aborted` row/assertions to root-status-only. Related stale wording remains elsewhere; see `m-2.2`. |
| 4 | m-1.3 | Fixed | `backend/agent_engine/agents/README.md` no longer says abort cleanup drains the deleted segmenter. |
| 5 | m-1.4 | Fixed | `_latest_generation()` is gone; no references found. |
| 6 | SP-1.2 | Fixed | Current `event_mapper.py` no longer force-closes reasoning on same-call `tool_call_chunk`; tests were updated. Related README boundary drift remains; see `m-2.1`. |
| 7 | SP-1.3 / SP-1.4 (Claude-run, "Exactly three" README wording) | Still Open | Not in Round 1's approved fix scope; see `SP-2.1`. |

## Issues

### [Major] M-2.1: Placeholder copy is rendered through CSS pseudo-content but the E2E asserts DOM text
- **File:** `frontend/src/components/atoms/ActivityPlaceholder.tsx` L19-L21; `frontend/tests/e2e/smoke/slow-start-stream.spec.ts` L16
- **Problem:** `ActivityPlaceholder` renders DOM text as `Thinking` / `Still working` and puts the animated dots in `.thinking-dots::after`. The E2E asserts `toHaveText("Thinking…")`, but Playwright's `toHaveText` checks DOM text content by default; CSS generated `::after` content is not part of it.
- **Fix:** Update the E2E to assert `Thinking` / `Still working` (matching the component, unit tests, and docs already updated this session) instead of the ellipsis form.
- **Context7:** Playwright `/microsoft/playwright`; `toHaveText` matches element text content, with optional `useInnerText`.
- **Orchestrator verification:** CONFIRMED by actually running the test (`npx playwright install chromium` + `npx playwright test tests/e2e/smoke/slow-start-stream.spec.ts --project=chromium`). Real failure: `Expected: "Thinking…" ... unexpected value "Thinking"`. This is a genuine, previously-uncaught regression — dates back to the manual-test dots-animation fix (`5ddb0f6`) earlier this session, never caught because Playwright e2e wasn't part of the verification loop run at that time (only vitest unit/integration + tsc/eslint/prettier).

### [Major] SP-2.1: Non-derived state budget still claims "exactly three" while the implementation has a fourth store
- **File:** `frontend/src/hooks/README.md` L15-L21; `frontend/src/components/pages/ChatPanel.tsx` L88-L91; `frontend/src/hooks/useDeadAirPlaceholder.ts` L37
- **Problem:** Round 1 already flagged this (Claude-run SP-1.3/SP-1.4): `useDeadAirPlaceholder()` owns `elapsedGapKey` state plus a timeout-backed grace mechanism, but the README and `ChatPanel` comment still say exactly three non-derived stores are allowed. Not in Round 1's approved fix scope, so it's still open.
- **Fix:** Either remove the fourth store by deriving the grace behavior differently, or ratify it and update the README/`ChatPanel` comment to enumerate the placeholder grace state explicitly.

### [Minor] m-2.1: Streaming README still documents the pre-fix tool-call boundary
- **File:** `backend/agent_engine/streaming/README.md` L38-L41
- **Problem:** The README says an open reasoning part closes when a `tool_call_chunk` block arrives. Current code intentionally does the opposite (this round's SP-1.2 fix) to satisfy S-chip-06 overlap behavior.
- **Fix:** Remove `tool_call_chunk` from the close-boundary list; note same-call tool-call chunks leave the reasoning part open, closure happens on text/next-LLM-call-id/second-same-chunk-reasoning-block/`finalize()`.

### [Minor] m-2.2: Backend script docs still reference deleted abort/segmenter contracts
- **File:** `backend/tests/scripts/README.md` L9; `backend/scripts/validation/README.md` L80
- **Problem:** `backend/tests/scripts/README.md` still says `reasoning_tail_aborted` is always required. `backend/scripts/validation/README.md` still tells operators to run after touching the `segmenter`, which was deleted.
- **Fix:** See spec-axis SP-2.1 below — `backend/tests/scripts/README.md` should be deleted outright (design-envelope §6 precedent), not just edited. Remove the stale `segmenter` wording from `validation/README.md`.

## Documentation Gaps

No missing README found in the changed module set. The active gaps are stale docs, covered by `m-2.1`, `m-2.2`, and `SP-2.1`.

## Official Standards Check

| Library | Version / Source | API Used | Status | Notes |
|---------|------------------|----------|--------|-------|
| Playwright | Context7 `/microsoft/playwright` | `expect(locator).toHaveText()` | ⚠️ Issue found (confirmed by live run) | Matcher checks DOM text content by default; CSS `::after` ellipsis will not satisfy `Thinking…`. |
| Vercel AI SDK `ai` | local `frontend/node_modules/ai` `^6.0.142` | tool part shape | ✅ No issue | Static tool chunks become `tool-${toolName}`; dynamic tools use `dynamic-tool`. |

---

# Spec Conformance Round 2

> Reviewer: gpt-5.5 | Date: 2026-07-28

## Summary

| Metric | Count |
|--------|-------|
| Total findings | 1 |
| Missing | 1 |
| Scope creep | 0 |
| Misimplemented | 0 |

## Previous Spec Findings Status

| # | Finding | Round-2 verdict | Notes |
|---|---------|------------------|-------|
| 1 | SP-1.1 (zero-delta wire emission) | Agree it's a false positive | `S-parts-05` covers reasoning-off / no reasoning block emitted at all; distinct from `S-chip-08`'s native zero-delta part + frontend-only suppression. Current mapper matches `S-chip-08`. |
| 2 | SP-1.2 (tool-call-chunk force-close) | ✅ Fixed | `_handle_tool_call_chunk_block` no longer force-closes; part closes on new LLM call id, following text, or `finalize()`. No-subsequent-LLM edge covered by `finalize()`. |
| 3 | SP-1.4 (window-a doc drift) | ✅ Doc now accurate | `bdd-scenarios.md:453` marks the old framing superseded and documents the shipped rule; Linear-record reconciliation explicitly deferred to DEV-108, not treated as an unresolved DEV-106 defect. |

## Findings

### [Blocking] SP-2.1: Test-folder README remains and still documents the removed abort-tail contract
- **Type:** Missing
- **Spec:** "touched-module README...backend 測試資料夾 README 依 design-envelope §6 刪除(named precedent)" (DEV-106 description, acceptance criterion 5); also "abort-cleanup 的 tail 撈取刪除" (What to build, Backend section)
- **File:** `backend/tests/scripts/README.md` L9
- **Problem:** This changeset touches `backend/tests/scripts/test_verify_langfuse_trace.py` and `backend/scripts/validation/verify_langfuse_trace.py` for the DEV-106 abort-tail removal, making `backend/tests/scripts/` a touched test folder — same category as `backend/tests/agents/README.md` and `backend/tests/streaming/README.md`, both already deleted this refactor per the named envelope §6 precedent. This one was missed. It also still says `reasoning_tail_aborted` is "always required" — directly contradicting the implemented root-status-only abort contract.
- **Fix:** Delete `backend/tests/scripts/README.md` per the same acceptance criterion and precedent already applied to the other two test-folder READMEs.

## Covered Requirements

(25 requirements independently re-confirmed against current code — full list in agent output; includes the new Round 2 chip-timing fix: "✅ Round 2 chip timing fix preserves prior completed chip durations across new turns — `frontend/src/components/pages/ChatPanel.tsx:124-132`")

---

## Orchestrator note on `backend/tests/scripts/README.md`

Verified: `docs/design-envelope.md` L94 states the rule generally ("no per-test-folder READMEs; precedent: two shipped already describing flags and events that don't exist") — that precedent is exactly `backend/tests/agents/README.md` and `backend/tests/streaming/README.md`, both deleted in Round 1 (m-1.3 area). `backend/tests/scripts/README.md` is the same pattern, touched by this same diff, and was missed. Both the Quality (m-2.2) and Spec (SP-2.1, Blocking) axes independently flagged it — agreement across axes on the underlying fact, differing only on severity/fix framing (edit vs. delete). Deleting it (matching precedent) resolves both.
