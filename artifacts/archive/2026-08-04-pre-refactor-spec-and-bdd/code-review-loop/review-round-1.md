# Code Review Round 1

> Reviewer: gpt-5.5 | Date: 2026-07-30

## Summary

| Metric | Count |
|--------|-------|
| Total issues | 3 |
| Blocking | 0 |
| Major | 3 |
| Minor | 0 |
| Suggestion | 0 |
| Library checks | 1 |

Tests could not be executed in this read-only sandbox because Python/pytest had no writable temporary directory.

## Issues

### [Major] M-1.1: Langfuse metadata write failure turns a successful stream into a user-visible error
- **File:** `backend/agent_engine/agents/base.py` L529
- **Problem:** The natural-completion `root_span.update(metadata=...)` is inside the broad stream `try`. If Langfuse span update raises after `agent.astream()` already completed successfully, control falls into the generic `except Exception` path and emits `StreamError` + `Finish(error)`. That violates the existing resilience contract described in `test_langfuse_resilience.py`: observability failure must not break the user stream. This is inside design envelope §4 Observability, so the shortcut is under-engineering.
- **Fix:** Make the natural transcript write best-effort like the error and abort paths: catch/log `root_span.update` failures, then still yield normal `mapper.finalize()` events. Add a unit test where `span.update.side_effect` raises on natural completion and the stream still finishes with `Finish(stop)`.
- **Context7:** Langfuse v4 `span.update(metadata=...)` on a held span reference is the correct non-deprecated API; the issue is exception isolation around that call.

### [Major] M-1.2: Transcript state is written before observing `finalize()` reasoning-end events
- **File:** `backend/agent_engine/agents/base.py` L525
- **Problem:** The comment says `finalize()` never emits reasoning events, but `StreamEventMapper.finalize()` explicitly closes an open reasoning part via `ReasoningEnd` before `Finish` (`backend/agent_engine/streaming/event_mapper.py` L259). Because the accumulator is not fed those final events, it can still think a segment is open after the model has actually completed. If cancellation lands while yielding the closing frames, `_handle_abort_cleanup()` will append `=== aborted ===` even though the segment was not cut mid-flight, violating the explicit abort-marker contract.
- **Fix:** Compute `final_events = mapper.finalize()`, feed those events through `accumulator.observe(...)`, perform the best-effort root span update, then yield the already-computed final events. Add a regression test for a stream whose last provider chunk is reasoning-only and cancellation occurs during closing-event yield.
- **Context7:** N/A.

### [Major] M-1.3: The 500KB cap is not actually a whole-transcript cap and can drop the abort marker
- **File:** `backend/agent_engine/streaming/reasoning_transcript_accumulator.py` L93
- **Problem:** `_cap()` slices the encoded transcript to `SIZE_CAP_BYTES` and then appends `... [truncated, original N bytes]`, so the returned metadata value exceeds the advertised 500KB whole-transcript cap. On aborted oversized transcripts, the abort marker is appended before `_cap()`, then tail truncation can remove it; the verifier requires aborted reasoning transcripts to end with `=== aborted ===`.
- **Fix:** Enforce the cap on the final rendered value, including the truncation suffix. For aborted transcripts, reserve space so the final value still ends with `=== aborted ===` while staying within `SIZE_CAP_BYTES`. Add tests for final byte length and oversized aborted transcripts.
- **Context7:** N/A.

## Documentation Gaps

| Folder | Missing |
|--------|---------|
| None | None |

## Official Standards Check

| Library | Version | API Used | Status | Notes |
|---------|---------|----------|--------|-------|
| langfuse | 4.5.0 | `propagate_attributes(...)`, `get_client().start_as_current_observation(as_type="span", name="chat_turn")`, held `span.update(metadata=...)`, `CallbackHandler` | Pass with implementation defect | No deprecated `update_current_trace()` / `span.update_trace()`, no private `CallbackHandler._runs`, and the held-span update follows the official v4 pattern. The remaining defect is local error handling around the official call. |

---

# Spec Conformance Round 1

> Reviewer: gpt-5.5 | Date: 2026-07-30

## Summary

| Metric | Count |
|--------|-------|
| Total findings | 4 |
| Missing | 0 |
| Scope creep | 1 |
| Misimplemented | 3 |

## Findings

### [Blocking] SP-1.1: `chat-turn` span name still violates snake_case
- **Type:** Misimplemented
- **Spec:** "Backend 全套測試綠;observability span 命名遵循 snake_case 慣例" (DEV-107 issue description / Acceptance criteria)
- **File:** `backend/agent_engine/agents/base.py` L690
- **Problem:** The new self-owned root span is named `chat_turn`, but LangChain config still sets `run_name` to `chat-turn`, and tests assert that hyphenated value. If this run name becomes a Langfuse observation/span name, the changeset still emits non-snake_case observability span naming.
- **Fix:** Rename `run_name` to `chat_turn` and update the rewritten tests/README expectations accordingly.

### [Blocking] SP-1.2: Langfuse readback verifier uses raw HTTP, not SDK readback
- **Type:** Misimplemented
- **Spec:** "真實對話後以 Langfuse SDK 讀回:root trace metadata 見 reasoning 全文,含 per-call 分隔標記" (DEV-107 issue description / Acceptance criteria)
- **File:** `backend/scripts/validation/verify_langfuse_trace.py` L50
- **Problem:** The verifier implements readback with `urllib.request` against `/api/public/traces/{trace_id}` rather than the Langfuse SDK. The abort acceptance criterion also explicitly says SDK readback, but the same verifier path is raw HTTP.
- **Fix:** Use the Langfuse SDK readback path for the real-trace verifier, or add a separate SDK-backed live validation path for both completed and aborted traces.

### [Major] SP-1.3: Abort marker can be written after a segment has already ended
- **Type:** Misimplemented
- **Spec:** "Transcript semantics: markers delimit segments (`=== segment N ===`, one per reasoning part, matching frontend chips one-to-one); `=== aborted ===` appears only when the conversation aborts mid-segment and marks transcript integrity, while conversation-level aborts stay owned by the separate `status: \"aborted\"` key." (ADR-0007 / Consequences)
- **File:** `backend/agent_engine/agents/base.py` L529
- **Problem:** `astream_run()` writes/uses the accumulator before observing `mapper.finalize()` events. `finalize()` can emit `ReasoningEnd`, but those events are yielded without `accumulator.observe(event)`. If the model stream naturally ends with reasoning and the client disconnects after the yielded `ReasoningEnd` but before `Finish`, `_handle_abort_cleanup()` still sees the accumulator as open and writes `=== aborted ===`, even though the segment already ended.
- **Fix:** Build `closing_events = mapper.finalize()`, feed those events through `accumulator.observe(...)` before the root-span update and before yielding them, then write metadata and yield the closing events.

### [Major] SP-1.4: Verify script retains capability/abort matrix beyond "root trace has full text"
- **Type:** Scope creep
- **Spec:** "verify script 大幅簡化,驗證項只剩「root trace 有全文」。" (DEV-107 issue description / What to build)
- **File:** `backend/scripts/validation/verify_langfuse_trace.py` L148
- **Problem:** The simplified verifier still exposes `--expect-reasoning-off`, `--expect-unsupported`, and `--expect-aborted`, and still validates sentinel/status-specific branches. That keeps a capability matrix and abort-specific verifier surface the spec explicitly tried to remove under the 達標即止 constraint.
- **Fix:** Reduce the verifier to the single required assertion class: root `chat_turn` trace/span carries the full `metadata.reasoning` transcript with segment markers.

## Covered Requirements

✅ Reasoning collection moved from per-LLM-call callback to stream-side accumulator observing reasoning domain events — `backend/agent_engine/streaming/reasoning_transcript_accumulator.py`

✅ `ReasoningTraceCallback` retired and per-generation `on_llm_end` persistence removed — `backend/agent_engine/streaming/reasoning_trace_callback.py`

✅ `_runs` private-state access removed from executable backend implementation — `backend/agent_engine/agents/base.py`

✅ Self-owned `chat_turn` root span added and used for deterministic end-of-conversation metadata writes — `backend/agent_engine/agents/base.py`

✅ Single `reasoning` metadata key with in-value `=== segment N ===` markers implemented — `backend/agent_engine/streaming/reasoning_transcript_accumulator.py`

✅ Mid-segment abort path writes reasoning tail plus `status: "aborted"` in one root-span update — `backend/agent_engine/agents/base.py`

✅ `langfuse_internal_contract` pytest marker removed — `pyproject.toml`

---

## Orchestrator Notes (post-review fact check, not part of reviewer output)

- M-1.2 / SP-1.3 share one root cause and the factual claim is VERIFIED: `event_mapper.finalize()` does emit `ReasoningEnd` for an open part (`event_mapper.py` `finalize()`); the base.py comment asserting otherwise misread the S-chip-06 comment in `_handle_tool_call_chunk_block`.
- M-1.1 VERIFIED by code inspection: natural-completion `root_span.update` sits inside the broad `try`, unlike the guarded error/abort paths.
- M-1.3 factual but note: the suffix-exceeds-cap behavior is inherited verbatim from the pre-existing per-call implementation; the aborted+oversized interaction is new.
- SP-1.1: `run_name="chat-turn"` predates this changeset (existing contract, documented in READMEs/guardrails); the AC wording arguably pulls it into scope.
- SP-1.2: the urllib fetch plumbing was inherited from the pre-existing verifier; readback goes through the same public REST endpoint the SDK's API client wraps.
- SP-1.4: strict reading conflicts with acceptance criterion #2, which itself requires an abort-case readback check (needs `--expect-aborted`); the `--expect-reasoning-off` / `--expect-unsupported` branches are the part genuinely beyond the "root trace has full text" bar.
