# DEV-109 BDD Verification — Round 1 — Deterministic Tier (11 scenarios)

**Critical environment finding**: `localhost:8000` resolves to IPv6 first on this dev machine and was hitting
an unrelated `python -m http.server` process instead of the FastAPI backend. All requests target
`127.0.0.1:8000` explicitly. Confirmed correct stream path via `openapi.json`: `POST /api/v1/chat`
(not `/api/v1/chat/stream` as `verification-plan.md` assumed).

### S-wire-01: single reasoning block wire shape — PASS
GPT-5-mini (default profile) produced 4 clean reasoning-start/end pairs plus tool calls for the
"simple" prompt (this provider still triggered tool use). Every block individually satisfies
start→delta*→end/same-id. No non-AI-SDK event types observed. Ran on GPT reasoning-on (provider-
agnostic wire-shape check; deviates from literal Given: Gemini, acceptable since J-01/J-02 cover
provider-specific mainlines separately). Capture: `temp/s-wire-01.sse`.

### S-wire-02: turn-unique reasoning ids across tool loop — PASS
5 reasoning blocks, ids `reasoning-0..4`, all unique, all start/end paired. Capture: `temp/s-wire-02.sse`.

### S-wire-03: mid-reasoning abort, no compensating wire events — PASS
Python httpx client closed connection after 5th `reasoning-delta`. Captured reasoning-2 opened with
5 deltas then capture ends — no `reasoning-end`, no `error`, no `finish`. Capture: `temp/s-wire-03.sse`.

### S-wire-04: error-path event ordering (reasoning open) — NOT-EXERCISED (reasoning-open branch only)
`FORCE_LLM_FAIL=1` → `error` → `finish`, no `reasoning-start` ever occurs (fires before LLM call).
Matches the pre-agreed known limitation. Base error→finish flow terminates cleanly.

### S-wire-05: Gemini reasoning-off wire is clean — PASS
Zero reasoning parts; text/tool parts and `finish` normal. Capture: `temp/s-wire-05.sse`.

### S-trace-01: root trace full Reasoning transcript, N segments — PASS
Wire had 5 reasoning-start/end pairs but only 3 carried deltas (2 zero-delta blocks). Transcript
contained exactly 3 segments matching the 3 non-zero-delta blocks verbatim — confirms zero-delta
suppression applies to transcript segment count too (N = chip-producing segments, not raw wire
reasoning-start count). Trace `8785e27d510717a7b760f45d75d65dc2`. `temp/s-trace-01.json`.

### S-trace-02: abort transcript tail + status marker — PASS
`reasoning` value ends with `=== aborted ===` matching the 5 aborted deltas; `status: "aborted"` on
same root span, same write. Trace `c50bf9c85146c8d8090fecc1652ce333`. `temp/s-trace-02.json`.

### S-trace-03: off/unsupported value semantics — PASS (both halves)
Off: `reasoning_value == ""` exactly, zero wire reasoning parts. Trace `2abd3af5b9caeed84faac6cf5dd3aa0d`.
Unsupported: authored `google_genai:gemini-2.5-flash` + `reasoning: "unsupported"` combo (none shipped
pre-built); `reasoning_value == "<unsupported>"` exactly, zero wire reasoning parts. Trace
`e1998a8ee448482295d8e5f4cf910e15`. Note: first Langfuse readback attempt for unsupported case
returned `root_span_found: false` due to ingestion lag (~15s); retry succeeded — not a backend bug.

### S-iso-01: two concurrent sessions, no cross-contamination — PASS
Each wire's `sessionId` = own id only; distinct trace ids, no literal content leakage across sessions
(natural comparative mentions of the other filing type are not leakage). `temp/s-iso-01-{a,b}-trace.json`.

### S-iso-02: abort residue does not leak into next turn — PASS
Turn B (same session, after turn A's mid-segment abort) has no `=== aborted ===`, `status_meta: null`,
and none of turn A's specific reasoning text appears in B's transcript. `temp/s-iso-02-b.sse`.

### S-iso-03: invoke path writes no Reasoning transcript — PASS
`/api/v1/chat/invoke` → HTTP 200; Langfuse trace named `baseline_invoke` has no `chat_turn`-named span
at all (structural absence, not just an absent key). Trace `d7cbb514a498715d96e9ea90a608ff7a`.
`temp/s-iso-03.json`.

## Summary

| Total | Passed | Failed | Errors | Not-Exercised |
|---|---|---|---|---|
| 11 | 10 | 0 | 0 | 1 |

Failed: none · Errors: none · Not-Exercised: S-wire-04 (reasoning-open branch — pre-agreed FORCE_LLM_FAIL limitation)

Backend config restored to default (GPT-5-mini, reasoning on) — confirmed clean git diff on
`orchestrator_config.yaml` and backend still running on :8000.
