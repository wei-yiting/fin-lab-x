---
# Code Review Round 3

> Reviewer: gpt-5.5 | Date: 2026-07-28

## Convergence Verdict

**NOT CONVERGED** — no remaining Blocking issues, but one Major documentation/comment drift remains in the current code. The Round 2 fixes corrected the README / `ChatPanel.tsx` wording, but left a conflicting architectural invariant comment in `reasoning-chips.ts` (explicitly out of scope for the Round 2 fixer dispatch, so this is expected, not a surprise).

## Summary

| Metric | Count |
|--------|-------|
| Total issues | 2 |
| Blocking | 0 |
| Major | 1 |
| Minor | 1 |
| Suggestion | 0 |

## Previous Round Status

| # | Issue ID | Status | Notes |
|---|----------|--------|-------|
| 1 | M-2.1 | Fixed | `slow-start-stream.spec.ts` now asserts `toHaveText("Thinking")`, matching `ActivityPlaceholder` textContent; test still meaningfully verifies placeholder visibility before streamed answer. |
| 2 | SP-2.1 (quality) | Partially fixed | `hooks/README.md`, `ChatPanel.tsx`, and `pages/README.md` now say four stores, but `frontend/src/lib/reasoning-chips.ts` still claims only three — was explicitly carved out of Round 2's fix scope, so this is the expected remainder. |
| 3 | m-2.1 | Fixed | `streaming/README.md` no longer lists `tool_call_chunk` as a reasoning close boundary; matches `event_mapper.py`. |
| 4 | SP-2.1 (spec, Blocking) / m-2.2 | Fixed | `backend/tests/scripts/README.md` deleted, no dangling reference; `validation/README.md` no longer mentions "segmenter". |

## Issues

### M-3.1 [Major] Stale architectural invariant still says there are only three non-derived chip stores
- **File:** `frontend/src/lib/reasoning-chips.ts` L3
- **Problem:** File-level comment says the only allowed non-derived stores live in `ChatPanel` and lists three (chip timing map, global stall stopwatch, expand/collapse override map) — omits `useDeadAirPlaceholder.ts`'s `elapsedGapKey` grace-timer store, now explicitly acknowledged as the fourth in `hooks/README.md`/`ChatPanel.tsx`/`pages/README.md`. Conflicts with those now-correct docs.
- **Fix:** Update the comment to match (four stores, or "at least three").

### m-3.1 [Minor] Test class docstring still describes tool-call-chunk as a reasoning close boundary
- **File:** `backend/tests/streaming/test_event_mapper.py` L363
- **Problem:** `TestReasoningPartBoundaries` class docstring says "Part closes when the provider moves on: text, tool, new LLM call" — no longer true after the SP-1.2 fix (tool-call-chunk arrival no longer closes reasoning). The actual test names/assertions underneath are already correct; only the docstring is stale.
- **Fix:** Update the docstring to: "Part closes when the provider moves on: text, new LLM call, or finalize — NOT a same-round tool-call chunk (S-chip-06 overlap)."

---

# Spec Conformance Round 3

> Reviewer: gpt-5.5 | Date: 2026-07-28

## Convergence Verdict

**CONVERGED** — zero remaining Blocking/Major spec deviations found across `86d3ae6..dd7eee8`. SP-2.1 (test-folder README deletion) confirmed fixed with no dangling references.

## Summary

| Metric | Count |
|--------|-------|
| Total findings | 0 |
| Missing | 0 |
| Scope creep | 0 |
| Misimplemented | 0 |

## Previous Findings Status

| # | Finding | Verdict | Notes |
|---|---------|---------|-------|
| 1 | SP-2.1 (test-folder README deletion) | ✅ Confirmed fixed | `backend/tests/scripts/README.md` absent; `git grep` found no references anywhere; `validation/README.md` now documents root `metadata.status == "aborted"` as the only abort marker. |

## Findings

None. Non-counted note: `reasoning-chips.ts:3`'s stale "three stores" comment observed but not counted as a spec-blocking deviation for this axis (it's the same item as Quality M-3.1 above).

## Covered Requirements

✅ Chip/tool-card overlap keeps tool card below still-open chip, no forced collapse — `event_mapper.py`, `test_event_mapper.py`, `AssistantMessage.tsx`
✅ Reload/in-flight turn behavior matches accepted no-history-hydration disposition — `ChatPanel.tsx`
✅ `useChat.status` 4-value contract + accepted placeholder window rule — `models.ts`, `useDeadAirPlaceholder.ts`, `bdd-scenarios.md`
✅ Backend test-folder READMEs deleted per design-envelope §6 — `backend/tests/agents/`, `backend/tests/scripts/`, `backend/tests/streaming/`
✅ Touched module READMEs in sync — `streaming/README.md`, `validation/README.md`, `pages/README.md`, `hooks/README.md`

---

## Orchestrator note

Both axes agree: only one substantive item remains (M-3.1 / the reasoning-chips.ts comment), a one-line doc correction, plus one trivial test-docstring line (m-3.1). Both are exactly the kind of item explicitly carved out of Round 2's fixer dispatch scope — expected, not a new surprise. Given Spec is fully converged and Quality's remainder is two one-line comment corrections with zero logic risk, proposing to fix these directly (no need for a full fixer+reviewer round 4) and then proceed to Final Verification.
