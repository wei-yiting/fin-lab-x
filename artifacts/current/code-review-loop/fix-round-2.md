# Fix Round 2

> Fixer: claude (general-purpose subagent) | Date: 2026-07-28

## Fixed

| Issue ID | How Fixed | Files Changed |
|----------|-----------|---------------|
| M-2.1 (Quality, Major) | Changed `.toHaveText("Thinking…")` → `.toHaveText("Thinking")` (textContent has no ellipsis; it's CSS `::after`) | `frontend/tests/e2e/smoke/slow-start-stream.spec.ts` |
| SP-2.1 (Quality, Major) | Reworded "exactly three" → "four" non-derived stores, adding `useDeadAirPlaceholder`'s grace timer as the fourth, in all three places the claim appeared. `docs/frontend_chat_architecture.md` and ADR-0006 had no matching "closed at three" claim (ADR-0006 L20 is scoped to its own consequence, not a system-wide count, left untouched). `frontend/src/lib/reasoning-chips.ts` carries the same stale claim but was explicitly carved out of scope — left untouched. | `frontend/src/hooks/README.md`, `frontend/src/components/pages/ChatPanel.tsx`, `frontend/src/components/pages/README.md` |
| m-2.1 (Quality, Minor) | Removed `tool_call_chunk` from the reasoning-part close-boundary list; added a note that same-round tool-call chunks leave reasoning open (S-chip-06), closing only via text-block arrival / chunk-id transition / second reasoning block / `finalize()` — verified against current `event_mapper.py` handlers | `backend/agent_engine/streaming/README.md` |
| SP-2.1 (Spec, Blocking) + m-2.2 (Quality, Minor) | Part A: deleted `backend/tests/scripts/README.md` (design-envelope §6 precedent; no other file referenced its path). Part B: removed "segmenter" from the deploy-guidance sentence in `backend/scripts/validation/README.md` (`reasoning_segmenter.py` no longer exists) | `backend/tests/scripts/README.md` (deleted), `backend/scripts/validation/README.md` |

## Not Fixed

None — all four issues in scope were fixable as scoped.

## Tests Run

| Test Command | Result | Notes |
|--------------|--------|-------|
| `npx playwright test tests/e2e/smoke/slow-start-stream.spec.ts --project=chromium` | ✅ Pass (1/1) | Confirms Issue 1 fix — real browser run |
| `uv run ruff check backend/` | ✅ Pass | |
| `uv run pytest backend/tests/scripts/ backend/tests/streaming/` | ✅ Pass (136 passed) | `test_verify_langfuse_trace.py` remains; only the README was deleted |
| `npm run test -- --run` (frontend vitest) | ✅ Pass (196 passed, 24 files) | |
| `npx tsc -b` | ✅ Pass, no output | |
| `npx eslint .` | ✅ Pass, 0 errors (1 pre-existing unrelated warning in `public/mockServiceWorker.js`) | |

## Tests Added or Modified

None — all fixes were a stale assertion correction and documentation-only changes.

## Commits

- `3fc764f` — `fix(frontend): stale E2E assertion + non-derived store count doc drift (round-2 review)`
- `dd7eee8` — `docs(backend): fix streaming README boundary drift + drop stale per-test-folder README`

Branch is 5 commits ahead of `origin/feat/multi-provider-streaming-reasoning`; not pushed.
