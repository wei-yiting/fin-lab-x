# Fix Round 1

> Fixer: Claude (general-purpose subagent) | Date: 2026-07-30
> User rulings applied: all 6 issues mandatory; SP-1.4 keeps `--expect-aborted` (AC-2 requires the abort-case check); accumulator `"<unsupported>"`/`""` value semantics untouched (D4 contract).

### Fixed

| Issue ID | How Fixed | Files Changed |
|----------|-----------|---------------|
| FIX-1 (M-1.2 + SP-1.3) | Natural-completion path now does `closing_events = mapper.finalize()` → `accumulator.observe(...)` each → `root_span.update(...)` → yield closing events. Same observe-before-write applied to the `except Exception` error path. Deleted the factually wrong "finalize() never emits reasoning events (ratified F5 spec)" comment and replaced it with one explaining that finalize() closes a still-open reasoning part. | `backend/agent_engine/agents/base.py`, `backend/tests/agents/test_orchestrator_langfuse.py` |
| FIX-2 (M-1.1) | Wrapped the natural-completion `root_span.update` in its own try/except with `logger.exception("failed to write reasoning transcript on natural completion")`, mirroring the error-path guard. A Langfuse failure no longer converts a successful stream into `StreamError` + `Finish(error)`. | `backend/agent_engine/agents/base.py`, `backend/tests/agents/test_orchestrator_langfuse.py` |
| FIX-3 (M-1.3) | `value()` now renders `body` and `marker_suffix` separately; `_cap(body, marker_suffix)` bounds the FINAL value to `SIZE_CAP_BYTES` by reserving bytes for both the `... [truncated, original N bytes]` note and the `\n=== aborted ===` suffix, so oversized aborted transcripts still end with the marker. Truncate-tail-keep-head and UTF-8-boundary semantics preserved. | `backend/agent_engine/streaming/reasoning_transcript_accumulator.py`, `backend/tests/streaming/test_reasoning_transcript_accumulator.py` |
| FIX-4 (SP-1.1) | Renamed `run_name` `"chat-turn"` → `"chat_turn"` in all 7 occurrences across 6 files. `grep -rn "chat-turn" backend/ docs/` returns nothing. | `backend/agent_engine/agents/base.py`, `backend/tests/agents/test_orchestrator_langfuse.py`, `backend/agent_engine/README.md`, `backend/agent_engine/agents/README.md`, `backend/agent_engine/docs/streaming_observability_guardrails.md`, `docs/observability.md` |
| FIX-5 (SP-1.2) | Verified via Context7 (/langfuse/langfuse-docs) and against the installed SDK (langfuse 4.5.0): the v4 readback is `get_client().api.trace.get(trace_id)` returning `TraceWithFullDetails`. Replaced the urllib/Basic-auth fetch with the SDK call; `.dict()` serializes with camelCase aliases (`parentObservationId` — confirmed empirically), so `verify()` needed no changes. Kept the 5-attempt linear-backoff loop, catching `langfuse.api.core.ApiError` and `httpx.HTTPError`. Dropped manual auth/`LANGFUSE_API_BASE`; docs now cite `LANGFUSE_PUBLIC_KEY`/`LANGFUSE_SECRET_KEY`/`LANGFUSE_BASE_URL` (legacy `LANGFUSE_HOST`). Fake-fetch monkeypatch updated to the new `(trace_id)` signature. | `backend/scripts/validation/verify_langfuse_trace.py`, `backend/tests/scripts/test_verify_langfuse_trace.py`, `backend/scripts/validation/README.md` |
| FIX-6 (SP-1.4) | Removed `--expect-reasoning-off` / `--expect-unsupported` flags, their verify branches, and their tests. `--expect-reasoning-on` kept as an explicit required flag (missing-flag rejection test kept); `--expect-aborted` and the trailing `=== aborted ===` assertion kept; always-write-key assertion kept (added an explicit test that `--expect-reasoning-on` fails on the `"<unsupported>"` sentinel). Accumulator `"<unsupported>"`/`""` semantics untouched. Module docstring and README updated; no other docs referenced the removed flags. | `backend/scripts/validation/verify_langfuse_trace.py`, `backend/tests/scripts/test_verify_langfuse_trace.py`, `backend/scripts/validation/README.md` |

### Not Fixed (with reason)

| Issue ID | Reason |
|----------|--------|
| — | — |

### Reverted (fix broke tests)

| Issue ID | What Broke | Reverted Files | Suggested Alternative |
|----------|------------|----------------|----------------------|
| — | — | — | — |

### Tests Run

| Test Command | Result | Notes |
|--------------|--------|-------|
| `.venv/bin/python -m pytest backend/tests/streaming/test_reasoning_transcript_accumulator.py -q` | 16 passed | After FIX-3 |
| `.venv/bin/python -m pytest backend/tests/scripts/test_verify_langfuse_trace.py -q` | 10 passed | After FIX-5/6 |
| `.venv/bin/python -m pytest backend/tests/agents/test_orchestrator_langfuse.py -q` | 28 passed | After FIX-1/2/4 |
| `.venv/bin/python -m pytest backend/tests/ -q` | 882 passed, 48 deselected | Full suite, green (rerun after ruff format) |
| `.venv/bin/ruff check backend/` + `.venv/bin/ruff format backend/` (+ `--check`) | All checks passed | 2 files reformatted by ruff, re-verified after |

### Tests Added or Modified

| Test File | Added/Modified | What It Tests |
|-----------|----------------|---------------|
| `backend/tests/agents/test_orchestrator_langfuse.py` | Added `TestFinalizeFeedsAccumulator` (3 tests) | (1) Reasoning-only stream completes naturally → transcript written exactly once, no aborted marker; (2) CancelledError thrown while yielding closing events (after `ReasoningEnd`) → abort write carries `status="aborted"` but NOT `=== aborted ===`; (3) `span.update` raising on natural completion → stream still ends with `Finish("stop")`, no `StreamError` |
| `backend/tests/agents/test_orchestrator_langfuse.py` | Modified | `chat-turn` → `chat_turn` assertions (2 sites) |
| `backend/tests/streaming/test_reasoning_transcript_accumulator.py` | Modified + added | Over-cap value ≤ `SIZE_CAP_BYTES`; new `test_over_cap_aborted_still_ends_with_marker_within_cap` |
| `backend/tests/scripts/test_verify_langfuse_trace.py` | Modified | SDK-based `fetch_trace(trace_id)` signature; removed off/unsupported tests; added sentinel-rejection test |

Committed as `cff4236` on `feat/multi-provider-streaming-reasoning` (not pushed).
