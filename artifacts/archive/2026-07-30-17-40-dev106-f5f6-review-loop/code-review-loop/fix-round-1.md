# Fix Round 1

> Fixer: claude (general-purpose subagent) | Date: 2026-07-28

## Fixed

| Issue ID | How Fixed | Files Changed |
|----------|-----------|---------------|
| M-1.1 (Quality, Major) | `resetForNewTurn` no longer calls `resetTimers()`; full timing-map wipe moved to `handleClearSession` only. Verified via AI SDK source (`node_modules/ai/dist/index.mjs`) that `regenerate()` never reuses the old assistant message id (new id always minted via `generateId()`), so no per-message pruning API was needed — kept `reset()` minimal (whole-map clear only). | `frontend/src/components/pages/ChatPanel.tsx`, `frontend/src/hooks/__tests__/useReasoningTimers.test.ts`, `frontend/src/components/pages/__tests__/ChatPanel.integration.test.tsx` |
| m-1.1 (Quality, Minor) | Rewrote docstring bullets in `verify_langfuse_trace.py` to describe the actual per-trace (not per-generation) non-empty-reasoning contract. | `backend/scripts/validation/verify_langfuse_trace.py` |
| m-1.2 (Quality, Minor) | Rewrote `--expect-aborted` row + assertion list to root-status-only, dropping the removed `metadata.reasoning_tail_aborted` marker. | `backend/scripts/validation/README.md` |
| m-1.3 (Quality, Minor) | Verified `_handle_abort_cleanup`'s actual docstring/behavior in `base.py` (root-chain `status="aborted"` stamp only); updated the module-map entry accordingly. | `backend/agent_engine/agents/README.md` |
| m-1.4 (Quality, Minor) | Confirmed via repo-wide grep that `_latest_generation()` has zero references (including the test file); deleted it. | `backend/scripts/validation/verify_langfuse_trace.py` |
| SP-1.2 (Spec/Codex rerun, Blocking) | Removed the unconditional `self._close_reasoning_part(events)` from `_handle_tool_call_chunk_block`; reasoning parts now stay open across same-round tool-call-chunks, closing only via the existing (already-tested) boundaries. | `backend/agent_engine/streaming/event_mapper.py`, `backend/tests/streaming/test_event_mapper.py` |
| SP-1.4 (Spec, doc-only) | Rewrote `bdd-scenarios.md` design-note point ① to describe the shipped `submitted OR streaming-with-nothing-rendered` rule, marked the old framing as superseded with the manual-testing rationale, deferred fuller reconciliation to DEV-108. | `artifacts/current/bdd-scenarios.md` |

## Not Fixed

None — all six issues in scope were fixable as scoped; no surprises requiring a stop.

## Tests Run

| Test Command | Result | Notes |
|--------------|--------|-------|
| `npm run test -- --run src/hooks/__tests__/useReasoningTimers.test.ts` | ✅ Pass (6/6) | |
| `npm run test -- --run src/components/pages/__tests__/ChatPanel.integration.test.tsx` | ✅ Pass (12/12) | Also manually verified the strengthened test *fails* against the pre-fix `ChatPanel.tsx` (via `git stash`), proving it locks the regression |
| `npm run test -- --run` (full frontend) | ✅ Pass (196/196, 24 files) | |
| `npx tsc -b` | ✅ Pass, no output | |
| `npx eslint <touched files>` | ✅ Pass, no output | |
| `npx prettier --write <touched ts/tsx>` | ✅ Unchanged (already formatted) | |
| `uv run pytest backend/tests/streaming backend/tests/agents` | ✅ Pass (221/221) | |
| `uv run pytest backend/tests/scripts` | ✅ Pass (14/14) | |
| `uv run pytest backend/tests/` (full backend) | ⚠️ 909 passed, 1 failed | The 1 failure (`test_baseline_integration.py::test_config_loading_from_yaml`) is pre-existing and unrelated — caused by an uncommitted, out-of-scope working-tree edit to `orchestrator_config.yaml` (model swapped to `google_genai:gemini-2.5-flash` for manual backend testing earlier in this session) that was already present in `git status` before the fixer started. Confirmed by stashing all fixer changes and re-running: same failure. Left untouched per scope rules — not part of this review's diff. |
| `uv run ruff check backend/` | ✅ All checks passed | |
| `uv run ruff format --check backend/` | ✅ 167 files already formatted | |

## Tests Added or Modified

| Test File | Added/Modified | What It Tests |
|-----------|----------------|---------------|
| `frontend/src/hooks/__tests__/useReasoningTimers.test.ts` | Added test | Observing an unrelated new turn's messages doesn't disturb an already-frozen past chip's duration (no `reset()` call in between) |
| `frontend/src/components/pages/__tests__/ChatPanel.integration.test.tsx` | Modified existing test | Added a real 1.2s delay before Stop + captured the exact "Stopped — thought for Ns" text pre-second-send, then asserted it's byte-for-byte unchanged after the second turn completes — replaces the old loose `/\d+s/` regex that also matched "0s" |
| `backend/tests/streaming/test_event_mapper.py` | Renamed + rewrote `test_tool_call_chunk_closes_open_reasoning_part` → `test_tool_call_chunk_does_not_close_open_reasoning_part`; added `test_tool_call_chunk_then_new_llm_call_closes_part_exactly_once` | New behavior: tool-call-chunk emits no `ReasoningEnd`; the part still closes exactly once, at the next round's LLM-call-id transition |

## Commits

- `010593b` — `fix(frontend): stop wiping chip timing map on every new turn (DEV-106 review fix)`
- `e9b32a9` — `docs(backend): fix reasoning-tail-removal doc/dead-code drift (F5 follow-up)`
- `9402463` — `fix(streaming): don't force-close open reasoning part on tool-call chunk (DEV-106 S-chip-06)`

Not pushed, per instructions.

## Items explicitly out of scope for this round (dispositioned, not touched)

- SP-1.1 (Claude run) / SP-1.5 (Codex rerun) — reload drops user prompt: accepted as expected, history hydration not built in this slice. No action.
- SP-1.1 (Codex rerun) — zero-delta wire emission: verified false positive (conflates S-parts-05 with S-chip-08). No action.
- SP-1.3 (Codex rerun) — `LiveStatusAnnouncer` in production: verified false positive (DEV-60's 2026-07-23 comment explicitly ratifies keeping it, out of F5 scope). No action.
- SP-1.3 / SP-1.4 (Claude run) — `PLACEHOLDER_GRACE_MS` as an undisclosed 4th non-derived store / `hooks/README.md`'s "Exactly three" wording: not included in this fix round's scope (not one of the four items the user approved fixing); still open for a future round if desired.
