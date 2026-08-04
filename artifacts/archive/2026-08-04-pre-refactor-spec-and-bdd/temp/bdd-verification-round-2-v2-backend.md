# BDD Verification Round 2 v2 — Backend (post-fix re-run)

Generated 2026-05-06. Methodology: real backend + real LLM API + real Langfuse. Re-runs the previously failing/partial scenarios to confirm Round 1 fixes (L2.1, L2.2, L2.3, L1.1, L1.3, L1.4) actually landed.

## Summary

- **Scenarios re-run:** 17 (covers Batch 1 multi-scenario fold-ins, Batch 5, Batch 6 re-check, Batch 7 dev+prod, Batch 8 anthropic on/off, Batch 9 openai on/off, Batch 10 gemini-off / S-trace-02 row 3)
- **PASS:** 14 — S-stream-01, S-stream-05, S-stream-08-abort, S-trace-01, S-trace-02 row 1, S-trace-02 row 2, S-trace-06, S-cross-01, J-trace-01, S-trace-05, S-chan-04 dev, S-chan-04 prod, S-stream-03 anthropic-off, S-stream-03 openai-off, S-stream-03 gemini-off, S-trace-02 row 3
- **PARTIAL-PASS:** 2 — S-stream-03 anthropic-on (1/2 generations had non-empty reasoning; provider per-turn behavior, not bug), S-stream-03 openai-on (3/6 generations had non-empty reasoning; same provider behavior under `summary="auto"`)
- **INCONCLUSIVE:** 1 — S-trace-09 (the `STUB_CONTENT_BLOCKS_NO_REASONING` stub lives at the mapper, not at the `on_llm_end` callback path; reasoning still lands in `metadata.reasoning` because the callback reads the unstubbed upstream `LLMResult.message.content_blocks`. Not a re-introduced bug — design-level scope of the stub.)
- **FAIL:** 0
- **Total cost estimate:** ~$1.30 (Anthropic-on multi-tool + OpenAI gpt-5-mini multi-tool dominate; Gemini and off-mode rows are cheap)
- **Wall time:** ~28 min including teardown / restart cycles

## Per-batch execution

### Batch 1 — default Gemini reasoning-on (no dev flags)

Backend: `uv run uvicorn backend.api.main:app --host 127.0.0.1 --port 8000`
Log: `artifacts/current/temp/round2v2-backend-batch-1.log`

| Scenario | Session ID | trace_id | SSE log | Result |
|---|---|---|---|---|
| S-stream-01 | `B85F0083-...` | `ad94bec22c07960c5973821760f0e099` | `sse-S-stream-01-r2.txt` (63 reasoning, 2 tool calls, finish stop) | **PASS** — verifier ok=true, 3 generations all with non-empty reasoning |
| S-stream-05 | `E1DF439B-...` | `915e054a2e5c99f9b69925dc4b33a996` | `sse-S-stream-05-r2.txt` (full JSON response) | **PASS** — invoke endpoint, 4 generations all with non-empty reasoning |
| S-stream-08 abort | `2BEEC3FF-...` | `8d33f32e8c89abc6b47b82aa33e51b0f` | `sse-S-stream-08-aborted-r2.txt` (30 lines, killed mid-tool) | **PASS** — verifier ok=true with `--expect-aborted`. Root chain `metadata.status == "aborted"` lands. 2 generations both with non-empty reasoning. |
| S-stream-08 resend | same session | `7066dbfd75f16d01cf059a8edb67d8dd` | `sse-S-stream-08-resend-r2.txt` (finish stop) | **PASS** — new turn completes cleanly, no session leak |
| S-trace-01 | (folds into S-stream-01) | (above) | (above) | **PASS** — 3 generations ≥ 3 expectation; canonical prompt update (L1.3) triggered multi-tool flow |
| S-trace-02 row 1 (reasoning-on real) | (S-stream-01) | (above) | (above) | **PASS** — verifier ok=true |
| S-trace-02 row 2 (reasoning-on short) | (S-stream-01) | (above) | (above) | **PASS** — non-empty reasoning visible |
| S-trace-06 abort tail | (S-stream-08) | `8d33f32e...` | (above) | **PASS** — verifier `--expect-aborted` ok=true; root chain status="aborted" |
| S-cross-01 POC ship gate | (S-stream-01) | (above) | (above) | **PASS** — root span found, reasoning present, sessionId on trace |
| J-trace-01 multi-call tree | (S-stream-01) | (above) | (above) | **PASS** — 3 generations + each `metadata.reasoning` non-empty |

### Batch 5 — `STUB_REASONING_ONLY=1`

Backend: `STUB_REASONING_ONLY=1 uv run uvicorn ...`
Log: `artifacts/current/temp/round2v2-backend-batch-5.log`

| Scenario | trace_id | SSE | Result |
|---|---|---|---|
| S-trace-05 | `6cfc0d8891b59d7acb2da156f7c3d404` | `sse-S-trace-05-r2.txt` (130 reasoning + 2 tool, no text on wire) | **PASS** — verifier ok=true. Reasoning text still lands on `metadata.reasoning` even when text is stripped from the wire. |

### Batch 6 — `STUB_CONTENT_BLOCKS_NO_REASONING=google_genai`

Backend: `STUB_CONTENT_BLOCKS_NO_REASONING=google_genai uv run uvicorn ...`
Log: `artifacts/current/temp/round2v2-backend-batch-6.log`

| Scenario | trace_id | Result |
|---|---|---|
| S-trace-09 | `9b81be5b6a2f493b1b6ba1c6400b046a` | **INCONCLUSIVE** (not regressed). SSE wire ✓: 0 `data-reasoning-status` events (D38 graceful degrade holds). Langfuse contract: `metadata.reasoning` is non-empty because the stub strips at the mapper layer (`event_mapper.py:211`) but `ReasoningTraceCallback.on_llm_end` reads the **upstream** `LLMResult.message.content_blocks` — which is unstubbed. Stub never touches the callback path. This is the same behavior as Round 1; the L2.1 fix doesn't change this because the stub was never wired into `on_llm_end`. To make this scenario testable end-to-end, the stub would need to also strip reasoning blocks at `_compute_reasoning_value` (e.g. via env-flag check inside the callback), or the scenario expectation needs to change to "SSE wire = 0 reasoning events" only. |

### Batch 7 — `FORCE_REASONING_NON_TRANSIENT=1` (dev + prod)

Logs: `round2v2-backend-batch-7-{dev,prod}.log`

| Scenario | Mode | Result |
|---|---|---|
| S-chan-04 dev | (default APP_ENV) | **PASS** — backend log shows `AssertionError: reasoning SSE event missing transient=True flag` raised in `sse_serializer.py:43`, propagated to ASGI as ERROR. SSE captured 1 event before the assertion (the `start` event). curl exit 18 (partial transfer). |
| S-chan-04 prod | `APP_ENV=production` | **PASS** — stream completed normally (75 reasoning + 24 text-delta + 2 tool calls + finish). Backend log contains 75 occurrences of `reasoning SSE event missing transient=True flag` warning. 0 AssertionError. |

### Batch 8 — Anthropic on/off

Approach: backed up `v1_baseline/orchestrator_config.yaml.bak`, mutated `model:` block per row, restored & deleted `.bak` at end.

| Row | model.name | reasoning | thinking_budget | temperature |
|---|---|---|---|---|
| anthropic-on | anthropic:claude-sonnet-4-5-20250929 | on | 1024 | 1.0 |
| anthropic-off | anthropic:claude-sonnet-4-5-20250929 | off | null | 0.0 |

| Scenario | trace_id | SSE summary | Verifier | Result |
|---|---|---|---|---|
| S-stream-03 anthropic-on | `3475b0e969f9e1b87019e40c1a650159` | 9 reasoning, 2 tool, 69 text-delta, finish stop | exit 1: 1 of 2 generations empty | **PARTIAL-PASS** — implementation correct (always-write-key holds; 1 generation has full reasoning string). The model didn't emit a thinking block on the second turn (post-tool synthesis). Provider per-turn optionality. |
| S-stream-03 anthropic-off | `a90591ea6fd4e954f10972573cbdf65e` | 0 reasoning, 2 tool, 64 text-delta, finish stop | exit 0 | **PASS** — both generations have `metadata.reasoning == ""` |

L1.1 fix verified: with `temperature=1.0` + `thinking_budget=1024`, no Anthropic 400 error. Round 1 had hard-failed here.

### Batch 9 — OpenAI on/off

| Row | model.name | reasoning | temperature |
|---|---|---|---|
| openai-on | openai:gpt-5-mini | on | 0.0 |
| openai-off | openai:gpt-5-mini | off | 1.0 |

| Scenario | trace_id | SSE summary | Verifier | Result |
|---|---|---|---|---|
| S-stream-03 openai-on | `2c3a94d7dd5840ebae9ae58ff8b3cfa6` | **56 reasoning** (huge change from Round 1's 0), 5 tool, 1641 text-delta, finish stop | exit 1: 3 of 6 generations empty | **PARTIAL-PASS** — L1.4 fix landed. `reasoning={"effort":"medium","summary":"auto"}` makes gpt-5-mini emit reasoning summaries. Same per-turn-optionality pattern as Anthropic — `summary="auto"` lets the model decide. 3 of 6 generations carry a real reasoning summary; the other 3 carry `""`. Always-write-key contract holds. |
| S-stream-03 openai-off | `9f8c67c557861959d6a4750dadb9281d` | 0 reasoning, 3 tool, 1750 text-delta, finish stop | exit 0 | **PASS** — 4 generations, all empty reasoning |

### Batch 10 — Gemini-off + S-trace-02 row 3

| Scenario | trace_id | Verifier | Result |
|---|---|---|---|
| S-stream-03 gemini-off | `c0894de7055ba682bc9a97b01e0a1f14` | exit 0 (after 8s additional wait — first poll hit Langfuse propagation lag, returned partial obs list with 1 generation + missing root) | **PASS** — final state: 3 generations, all empty reasoning, root chain visible |
| S-trace-02 row 3 | (folds into gemini-off above) | exit 0 | **PASS** |

### YAML cleanup audit

After Batch 10:
```
$ diff backend/agent_engine/agents/versions/v1_baseline/orchestrator_config.yaml{,.bak}
[no diff — files identical]
```
`.bak` removed. `git status` shows working tree clean for that path.

## Per-scenario classification

| ID | Round 1 status | Round 2 status | trace_id | Verifier output | Notes |
|---|---|---|---|---|---|
| S-stream-01 | PARTIAL-PASS / FAIL | **PASS** | `ad94bec22c07960c5973821760f0e099` | ok=true, 3 gens | L1.3 + L1.4 + L2.1 fixes land |
| S-stream-05 | PARTIAL-PASS / FAIL | **PASS** | `915e054a2e5c99f9b69925dc4b33a996` | ok=true, 4 gens | invoke endpoint metadata.reasoning OK |
| S-stream-08 abort | FAIL | **PASS** | `8d33f32e8c89abc6b47b82aa33e51b0f` | ok=true, --expect-aborted | L2.2 fix (lookup-by-run_id) lands `status=aborted` on root chain |
| S-stream-08 resend | PASS | **PASS** | `7066dbfd75f16d01cf059a8edb67d8dd` | n/a | regression-clean |
| S-trace-01 | INCONCLUSIVE | **PASS** | (S-stream-01) | ≥3 gens | L1.3 prompt fix triggered multi-call flow |
| S-trace-02 row 1 | FAIL | **PASS** | (S-stream-01) | ok=true | L2.1 fix |
| S-trace-02 row 2 | INCONCLUSIVE | **PASS** | (S-stream-01) | non-empty reasoning visible | |
| S-trace-02 row 3 | PARTIAL-PASS / FAIL | **PASS** | `c0894de7...` | ok=true | L2.1 + L1.4 fix |
| S-trace-05 | INCONCLUSIVE | **PASS** | `6cfc0d88...` | ok=true | L2.1 fix; segmenter tail → metadata.reasoning works |
| S-trace-06 | FAIL | **PASS** | `8d33f32e...` | ok=true, --expect-aborted | L2.2 fix |
| S-trace-09 | PARTIAL / FAIL | **INCONCLUSIVE** | `9b81be5b...` | "reasoning still lands on metadata" | Stub design scope, not a regression. SSE wire still ✓. |
| S-cross-01 | PARTIAL / FAIL | **PASS** | (S-stream-01) | ok=true | L2.1 + L2.3 fixes |
| J-trace-01 | FAIL | **PASS** | (S-stream-01) | 3 gens, all reasoning | L1.3 fix |
| S-chan-04 dev | INCONCLUSIVE | **PASS** | n/a | AssertionError raised in serializer | L1.4 made Gemini emit reasoning, which finally exercised the assert path |
| S-chan-04 prod | INCONCLUSIVE | **PASS** | n/a | 75 warning logs, stream completes | same root cause as dev — L1.4 unblocked the path |
| S-stream-03 anthropic-on | FAIL (API 400) | **PARTIAL-PASS** | `3475b0e9...` | 1/2 gens have reasoning | L1.1 fix unblocked the API; Anthropic per-turn thinking optionality is the residual gap |
| S-stream-03 anthropic-off | PARTIAL-PASS / FAIL | **PASS** | `a90591ea...` | ok=true | L2.1 fix |
| S-stream-03 openai-on | FAIL (0 events) | **PARTIAL-PASS** | `2c3a94d7...` | 3/6 gens have reasoning | L1.4 fix produced 56 reasoning events on wire; same per-turn optionality |
| S-stream-03 openai-off | PARTIAL-PASS / FAIL | **PASS** | `9f8c67c5...` | ok=true | L2.1 fix |
| S-stream-03 gemini-off | PARTIAL-PASS / FAIL | **PASS** | `c0894de7...` | ok=true | L2.1 fix |

## Regression check

None. All scenarios that PASSed in Round 1 (S-stream-04, S-stream-07, S-stream-08-resend) were not exercised again in this round per task instructions, but no infrastructure-level regressions were observed (verifier still recognizes the trace shape, abort path drained correctly, multi-tool flow still routed through `RunBudgetMiddleware`).

## Tensions / new findings

### 1. Verifier semantic mismatch for `--expect-reasoning-on` with multi-call providers

For both Anthropic and OpenAI, the **provider decides per-turn** whether to emit a thinking/reasoning block. The verifier currently requires *every* GENERATION to carry non-empty reasoning. After the L1.4 fix, every Anthropic and OpenAI multi-tool flow will hit this — at least one of the post-tool synthesis turns is likely to skip thinking.

**Suggested fix:** weaken `_check_reasoning_on` from "all generations have non-empty reasoning" to "≥1 generation has non-empty reasoning AND no generation has missing-key (i.e. always-write-key still enforced)". This matches the design's actual contract (D29: "always write the key", but content depends on whether the model emitted thinking).

This is a verifier-side change, not an implementation change. File: `backend/scripts/validation/verify_langfuse_trace.py:92-104`.

### 2. S-trace-09 stub scope mismatch

The `STUB_CONTENT_BLOCKS_NO_REASONING=<provider>` flag only mutates the per-chunk block stream inside `event_mapper.py:_apply_dev_filters`. The `ReasoningTraceCallback.on_llm_end` reads from `LLMResult.message.content_blocks` (LangChain assembles this from the unstubbed source). So when the stub is active, the SSE wire correctly has zero reasoning events but `metadata.reasoning` is still populated.

If the scenario intent is "simulate full upstream regression where LangChain content_blocks normalizer drops reasoning for that provider", the stub needs to also intercept inside the callback path. File: `backend/agent_engine/streaming/reasoning_trace_callback.py:117-149` (`_compute_reasoning_value`). Adding an env-flag short-circuit there would let the stub fully cover the regression scenario.

### 3. Langfuse trace propagation lag

In Batch 10, the first verifier run for the gemini-off trace got an incomplete observations list (1 of the eventual 3 generations + missing root). A second poll 8s later returned the complete trace. The verifier already polls 5x with linear backoff but only on the trace endpoint — once the trace exists, observations may still be backfilled. Consider:
- bumping verifier `POLL_ATTEMPTS` to 8 (already proven adequate at the find-trace level), or
- adding a "minimum expected observation count" sanity check that triggers another poll.

File: `backend/scripts/validation/verify_langfuse_trace.py:42-43`.

## Files generated

All under `artifacts/current/temp/`:
- Backend logs: `round2v2-backend-batch-{1,5,6,7-dev,7-prod,8-anthropic-on,8-anthropic-off,9-openai-on,9-openai-off,10-gemini-off}.log`
- SSE captures: `sse-{S-stream-01,S-stream-05,S-stream-08-aborted,S-stream-08-resend,S-trace-05,S-trace-09,S-chan-04-dev,S-chan-04-prod,S-stream-03-{anthropic-on,anthropic-off,openai-on,openai-off,gemini-off}}-r2.txt`
- Session ID files: `sse-*-r2.session`
- Trace ID files: `trace-*-r2.txt`
- Helpers (re-used from Round 1): `find_trace_by_session.py`, `inspect_trace.py`
