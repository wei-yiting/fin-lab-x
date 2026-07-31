# Code Review Round 2

> Reviewer: gpt-5.5 | Date: 2026-07-30

## Summary

| Metric | Count |
|--------|-------|
| Total issues | 2 |
| Blocking | 0 |
| Major | 1 |
| Minor | 1 |
| Suggestion | 0 |
| Library checks | 1 |

## Previous Round Status

| # | Issue ID | Status | Notes |
|---|----------|--------|-------|
| 1 | M-1.1 | ✅ Fixed | Natural-completion `root_span.update(...)` is now wrapped in its own best-effort `try/except`; stream still yields `Finish(stop)` on update failure. |
| 2 | M-1.2 | ✅ Fixed | `mapper.finalize()` is materialized, its events are observed by the accumulator before the metadata write, then yielded. |
| 3 | M-1.3 | ✅ Fixed | `_cap()` now bounds the final rendered value including truncation note and reserves space for the aborted marker. |
| 4 | SP-1.1 | ✅ Fixed | `run_name` is now `chat_turn`; no remaining `chat-turn` references found in touched backend/docs paths. |
| 5 | SP-1.2 | ✅ Fixed | Verifier readback now uses `get_client().api.trace.get(trace_id).dict()` and catches `ApiError` / `httpx.HTTPError`. |
| 6 | SP-1.3 | ✅ Fixed | Same root cause as M-1.2; fixed by observe-before-write ordering. |
| 7 | SP-1.4 | ✅ Fixed | `--expect-reasoning-off` and `--expect-unsupported` branches were removed; `--expect-aborted` kept for the abort acceptance path. |

## Issues

### [Major] M-2.1: Zero-delta reasoning parts create a false non-empty Langfuse transcript
- **File:** `backend/agent_engine/streaming/reasoning_transcript_accumulator.py` L80
- **Problem:** The accumulator renders every `ReasoningStart` as a segment, even if no `ReasoningDelta` ever arrived before `ReasoningEnd`. The mapper intentionally emits start/end for zero-delta reasoning blocks, and the frontend suppresses those chips. This means Langfuse can get `metadata.reasoning == "=== segment 1 ===\n"` for a turn with no reasoning text, and `verify_langfuse_trace.py --expect-reasoning-on` will pass because it only checks non-empty + marker. That breaks the ADR's "full reasoning text" contract and the README claim that segments map one-to-one to frontend chips.
- **Fix:** Do not render zero-delta segments into the transcript. Preserve whitespace-only deltas, but filter truly empty completed segments and renumber rendered segments from the kept list. Add an accumulator test for `ReasoningStart` + `ReasoningEnd` with no delta returning `""`, plus a verifier test that marker-only empty segment does not satisfy `--expect-reasoning-on`.
- **Context7:** N/A.

### [Minor] m-2.2: Agents README documents the pre-fix natural-completion ordering
- **File:** `backend/agent_engine/agents/README.md` L46
- **Problem:** The README says natural termination writes `metadata.reasoning`, then `mapper.finalize()` closes the open reasoning/text blocks. Current code correctly does the opposite: `finalize()` first, accumulator observes closing events, then metadata is written. This is exactly the M-1.2 fix, so the touched README now teaches the stale ordering.
- **Fix:** Reword the natural-termination bullet to say `mapper.finalize()` closes pending events first, those events are observed by the accumulator, then the root span metadata is written before yielding the closing frames.
- **Context7:** N/A.

## Documentation Gaps

| Folder | Missing |
|--------|---------|
| `backend/agent_engine/agents/` | README natural-completion ordering still says write-before-finalize. |
| `backend/agent_engine/streaming/` | README oversize row still says "first 500KB + suffix"; after the fix, the final value including suffix is capped at 500KB. |

## Official Standards Check

| Library | Version | API Used | Status | Notes |
|--------|---------|----------|--------|-------|
| langfuse | 4.5.0 | `get_client().api.trace.get(trace_id)` | ✅ Current | Context7 confirms this is the supported v4 SDK trace readback path returning `TraceWithFullDetails`; `.dict()` camelCase serialization and `ApiError` / `httpx.HTTPError` handling match the changed verifier. |

---

# Spec Conformance Round 2

> Reviewer: gpt-5.5 | Date: 2026-07-30

## Summary

| Metric | Count |
|--------|-------|
| Total findings | 0 |
| Missing | 0 |
| Scope creep | 0 |
| Misimplemented | 0 |

## Previous Spec Findings Status

| # | Finding | Status | Notes |
|---|---------|--------|-------|
| SP-1.1 | `chat-turn` span name still violates snake_case | ✅ Fixed | `base.py` now uses `name="chat_turn"` and `run_name: "chat_turn"`; targeted `rg "chat-turn"` has no backend/docs hits. |
| SP-1.2 | Langfuse readback verifier uses raw HTTP, not SDK readback | ✅ Fixed | `verify_langfuse_trace.py` now imports `get_client` and reads via `client.api.trace.get(trace_id).dict()`; raw `urllib` path is gone. |
| SP-1.3 | Abort marker can be written after a segment has already ended | ✅ Fixed | `astream_run()` now finalizes, feeds `closing_events` into the accumulator, then writes metadata before yielding closing events. Late cancellation no longer leaves the segment open. |
| SP-1.4 | Verify script retains capability/abort matrix beyond "root trace has full text" | ✅ Fixed | `--expect-reasoning-off` and `--expect-unsupported` were removed. `--expect-aborted` remains, matching the user ruling and abort acceptance criterion. |

## Findings

None.

## Covered Requirements

✅ Snake_case root/span naming is restored for both owned root span and LangChain run name — `backend/agent_engine/agents/base.py`
✅ SDK readback path verifies root-span `metadata.reasoning` with segment marker checks — `backend/scripts/validation/verify_langfuse_trace.py`
✅ Abort-case verifier checks `metadata.status == "aborted"` and transcript tail marker — `backend/scripts/validation/verify_langfuse_trace.py`
✅ Finalize/abort ordering prevents `=== aborted ===` after an already closed reasoning segment — `backend/agent_engine/agents/base.py`
✅ Unsupported/off verifier branches were removed while preserving the ratified abort check — `backend/scripts/validation/verify_langfuse_trace.py`
✅ `_runs` private-state implementation and contract test path are deleted from executable backend scope — `backend/agent_engine/streaming/reasoning_trace_callback.py`
✅ `langfuse_internal_contract` marker is gone — `pyproject.toml`

---

## Orchestrator Notes

- M-2.1 fact-checked: `event_mapper._handle_reasoning_block` emits `ReasoningStart` on block arrival and `ReasoningDelta` only when delta text is non-empty — zero-text blocks do produce phantom segments in the accumulator. Confirmed real; dispatched to fix round 2.
- Spec axis is clean (0 findings, 4/4 previous fixed); per skill dispatch criteria it will not be re-dispatched in round 3 unless fix round 2 touches spec-relevant behavior.
