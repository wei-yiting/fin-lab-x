# BDD Verification Round 1 v2 — Backend (real LLM + Langfuse)

Generated 2026-05-06. Methodology: real backend + real LLM API + real Langfuse trace. Each batch starts uvicorn with the right env, runs scenarios, tears down before the next batch.

## Summary

- **Scenarios attempted:** 13 backend-side scenarios + 6 matrix rows (5 ran; 1 already-covered skipped)
- **PASS:** 4 (S-stream-04, S-stream-07, S-stream-08-resend, S-trace-09 SSE event count)
- **FAIL:** 0 implementation crashes; HOWEVER 100% of `--expect-reasoning-on/off` Langfuse verifier runs failed due to a **systemic bug** in `ReasoningTraceCallback` integration (see Failure Analysis L2.1 — `metadata.reasoning` never lands on Langfuse generations). Treating the verifier exit code at face value, that's 9 FAIL.
- **BLOCKED-NEEDS-CHROME:** S-rsn-* (all visual lifecycle), S-chan-01/02/03, J-chan-01, J-rsn-01/02 — main thread will run.
- **DEFERRED:** S-trace-02 rows 4-5, S-trace-03, S-trace-04, S-trace-07, S-trace-08 (per scope decisions in executable-verification.md).
- **INCONCLUSIVE:** S-chan-04 dev + prod (cannot trigger the assert/warn path with default Gemini model — the stub flag operates inside `serialize_event(ReasoningStatus)`, which is never called when upstream emits zero reasoning blocks; would need a model that actually emits `data-reasoning-status` events under default Gemini config to exercise the assert path).
- **Estimated cost:** ~$0.40-0.80 (Anthropic-on with multi-tool flow was the most expensive; Gemini one-shot pushbacks are nearly free).
- **Wall time:** ~50 min including teardown / restart cycles.

## Per-batch execution

### Batch 1 — default Gemini reasoning-on (no dev flags)

Backend launch:
```
uv run uvicorn backend.api.main:app --host 127.0.0.1 --port 8000
```
Log: `artifacts/current/temp/round1v2-backend-batch-1.log`

Scenarios run:

| Scenario | Session ID | trace_id | SSE log path | Result |
|---|---|---|---|---|
| S-stream-01 | `A5F6772E-...` | `c429c4a88dc37e1ea6912150ce98f1f8` | `sse-S-stream-01.txt` | partial: stream completed `finish(stop)` ✓; **but** Gemini took a one-shot pushback ("10-K is annual not quarterly") so 0 tool calls / 0 reasoning. Verifier returned exit 1: `metadata.reasoning` missing on the single generation. |
| S-stream-05 | `9D1DD83B-...` | `f8c9fadfeb9f67f491406babdc82950b` | `sse-S-stream-05.txt` | invoke endpoint returned final response JSON; same Gemini pushback path. Verifier exit 1. |
| S-stream-07 | A: `37DED764-...`, B: `4027BDCA-...` | A: `ee1020a0...`, B: `0534a4d9...` | `sse-S-stream-07-{A,B}.txt` | **PASS**: two distinct trace_ids; A SSE log contains 0 "Microsoft" hits; B SSE log contains 0 "Apple" hits. D33 isolation verified at SSE wire level. |
| S-stream-08 abort | `BEC3F4DF-...` | `ecfce6b2c6d11981fcbf3fc04f1f7586` | `sse-S-stream-08-aborted.txt` | curl killed mid-stream after 7 tool calls + 251 text-deltas; SSE log lacks `text-end` and `finish`. Verifier with `--expect-aborted`: exit 1 (root span not found + 7 generations missing reasoning + status not flipped to "aborted"). See Failure Analysis L2.2. |
| S-stream-08 resend | same session, new turn | (not captured) | `sse-S-stream-08-resend.txt` | **PASS**: new turn completed cleanly with `finish(stop)`; tool call invoked; no inheritance of stale state. Session-busy 409 not encountered (cleanup ran). |
| S-trace-01 | (folds into S-stream-01) | (above) | (above) | INCONCLUSIVE — Gemini pushback path produced only 1 chat_model span, not the multi-call shape the scenario asserts. Cannot test "≥3 chat_model spans" with this prompt + model combo. |
| S-trace-02 row 1 (reasoning-on real) | (S-stream-01) | (above) | (above) | FAIL via verifier (`metadata.reasoning` missing). See L2.1. |
| S-trace-02 row 2 (reasoning-on short) | (S-stream-01) | (above) | (above) | per scenario, empty reasoning is acceptable; verifier currently treats missing key as failure regardless. INCONCLUSIVE under current verifier semantics. |
| S-trace-06 abort tail | (S-stream-08) | (above) | (above) | FAIL via verifier (status not "aborted" on root span; root span not found). See L2.2. |
| S-cross-01 POC ship gate | (S-stream-01) | (above) | (above) | FAIL: verifier reports root span not classifiable + no reasoning metadata. Trace-level `session_id` IS set on the trace itself (Langfuse `sessionId="A5F6772E-..."`), so contextvars partial PASS for `session_id` propagation; but the rest of the contract fails. |
| J-trace-01 | (S-stream-01) | (above) | (above) | FAIL: tree shape doesn't match §6.3 example because Gemini one-shot pushback produced only 1 chat_model span (no `agent.run` span by that name; root is `chat-turn` of type CHAIN). |

### Batch 2 — `FORCE_LLM_FAIL=1`

Backend launch: `FORCE_LLM_FAIL=1 uv run uvicorn ...`
Log: `artifacts/current/temp/round1v2-backend-batch-2.log`

| Scenario | Result |
|---|---|
| S-stream-04 mid-stream | **PASS**: SSE stream contains exactly `error` event with text "FORCE_LLM_FAIL: simulated provider failure" + `finish(error)`, no reasoning/text/tool events. SSE: `sse-S-stream-04.txt`. |

### Batch 5 — `STUB_REASONING_ONLY=1`

Backend launch: `STUB_REASONING_ONLY=1 uv run uvicorn ...`
Log: `artifacts/current/temp/round1v2-backend-batch-5.log`

| Scenario | trace_id | Result |
|---|---|---|
| S-trace-05 | `2bfaa6091e3b14f96f846e926d934083` | INCONCLUSIVE: SSE produced only `start` + `finish` (no reasoning events because Gemini emits zero reasoning blocks under default config; the stub strips text/tool which leaves nothing). The scenario expectation "trace metadata.reasoning contains all reasoning text" cannot be tested when the upstream emits no reasoning. SSE: `sse-S-trace-05.txt`. |

### Batch 6 — `STUB_CONTENT_BLOCKS_NO_REASONING=google_genai`

Backend launch: `STUB_CONTENT_BLOCKS_NO_REASONING=google_genai uv run uvicorn ...`
Log: `artifacts/current/temp/round1v2-backend-batch-6.log`

| Scenario | trace_id | Result |
|---|---|---|
| S-trace-09 | `0a48138eb44b63bb03127e78f29ac8c6` | **partial PASS**: SSE log has 0 `data-reasoning-status` events ✓ (D38 graceful degrade at wire level); text/finish flow normally ✓. **FAIL on Langfuse contract**: scenario expects `metadata.reasoning == ""` (empty string) but actual is missing key entirely (verifier reports `got None`). SSE: `sse-S-trace-09.txt`. |

### Batch 7 backend portion — `FORCE_REASONING_NON_TRANSIENT=1`

Logs: `round1v2-backend-batch-7-{dev,prod}.log`

| Scenario | Mode | Result |
|---|---|---|
| S-chan-04 dev | (default APP_ENV) | INCONCLUSIVE: backend launched, prompt sent, Gemini pushback returned with 0 reasoning events. The stub flag operates *inside* `serialize_event(ReasoningStatus)`, so when the mapper never produces a `ReasoningStatus`, the assert is never reached. No `AssertionError` propagated to the SSE stream; `error` event count = 0. SSE: `sse-S-chan-04-dev.txt`. |
| S-chan-04 prod | `APP_ENV=production` | INCONCLUSIVE for the same reason. Backend log inspection: zero "reasoning SSE event missing transient flag" warning lines. SSE: `sse-S-chan-04-prod.txt`. |

### Batch 8-10 — Multi-provider matrix via v1_baseline.yaml edits

Approach: **single switching vehicle**. Backed up `v1_baseline/orchestrator_config.yaml` as `.bak` once; restored at the end (verified no diff vs. bak; bak file deleted).

Per-row edits applied to the `model:` block of `v1_baseline/orchestrator_config.yaml`:

| Row | model.name | reasoning | thinking_budget | temperature | Notes |
|---|---|---|---|---|---|
| gemini-on | google_genai:gemini-2.5-flash | on | null | 0.0 | already covered by Batch 1 — SKIP |
| gemini-off | google_genai:gemini-2.5-flash | off | null | 0.0 | ran |
| anthropic-on | anthropic:claude-sonnet-4-5-20250929 | on | 1024 | **1.0** | ran (had to bump temperature from 0.0 → 1.0 because Anthropic API rejects `temperature != 1` when thinking is enabled — see Tensions section) |
| anthropic-off | anthropic:claude-sonnet-4-5-20250929 | off | null | 0.0 | ran |
| openai-on | openai:gpt-5-mini | on | null | 1.0 | ran |
| openai-off | openai:gpt-5-mini | off | null | 1.0 | ran |

OpenAI model resolution: `model_context_registry.yaml` only lists `gpt-4o`, `gpt-4o-mini`, `gemini-2.5-flash`. The model name `openai:gpt-5-mini` is NOT in the registry, but `init_chat_model` accepted it (registry lookup just emitted a fallback warning). Used `openai:gpt-5-mini` as the canonical reasoning-on OpenAI option.

Per-row results:

| Row | Session | trace_id | SSE event summary | Verifier result | Result classification |
|---|---|---|---|---|---|
| gemini-off | `sse-S-stream-03-gemini-off.session` | `f34109b9b6d4316b9154dcd74d2ccb39` | 21 text-delta + 4 tool calls + 0 reasoning ✓; finish(stop) | exit 1: "expected empty reasoning, got None" + root span not found | partial PASS at SSE wire level; FAIL at Langfuse contract |
| anthropic-on | `sse-S-stream-03-anthropic-on.session` | `6204213010f5091b24c735a1b7398210` | 80 text-delta + **13 data-reasoning-status** + 4 tool calls + finish(stop) ✓ | exit 1: "missing metadata.reasoning" on single generation + root span not found | **partial PASS at SSE wire level (real reasoning emitted)**; FAIL at Langfuse contract |
| anthropic-off | `sse-S-stream-03-anthropic-off.session` | `a9ffd7bc414d86f47aae1cd6a0509847` | 80 text-delta + 2 tool calls + 0 reasoning ✓ | exit 1: "expected empty reasoning, got None" | partial PASS at SSE wire level; FAIL at Langfuse contract |
| openai-on | `sse-S-stream-03-openai-on.session` | `7015181f9f0b49593c6508c983478d32` | 2173 text-delta + 4 tool calls + 0 reasoning | exit 1: 5 generations all missing metadata.reasoning | UNEXPECTED: gpt-5-mini reasoning-on emitted **0 reasoning events at SSE wire level** (no `data-reasoning-status`). Implementation may not extract OpenAI reasoning blocks via `content_blocks`. |
| openai-off | `sse-S-stream-03-openai-off.session` | `208d515c9b411a0e688f5b2a1ac143a7` | 1676 text-delta + 4 tool calls + 0 reasoning ✓ | exit 1: 3 generations all missing metadata.reasoning | partial PASS at SSE wire level; FAIL at Langfuse contract |

S-trace-02 row 3 (reasoning-off mode → empty `metadata.reasoning`): folds into the gemini-off row. Same FAIL classification.

S-rsn-07 backend portion: skipped (purely visual idle text — main thread does it).

### YAML diff for audit

The matrix mutated only the `model:` block of `v1_baseline/orchestrator_config.yaml`. Verified after Batch 10 cleanup:

```
$ diff backend/agent_engine/agents/versions/v1_baseline/orchestrator_config.yaml{,.bak}
[no output — files identical]
```

Bak file removed after verification. `git status` and `git diff` show no diff under `backend/agent_engine/agents/versions/v1_baseline/`.

## Per-scenario classification (combined)

| ID | Status | trace_id | Verifier output | Notes |
|---|---|---|---|---|
| S-stream-01 | PARTIAL-PASS / FAIL | c429c4a88dc37e1ea6912150ce98f1f8 | exit 1 missing reasoning + root span | Stream completed cleanly; pushback prompt path |
| S-stream-04 | **PASS** | n/a | n/a | Error event + Finish(error) per spec |
| S-stream-05 | PARTIAL-PASS / FAIL | f8c9fadfeb9f67f491406babdc82950b | exit 1 missing reasoning | Invoke completed with response JSON |
| S-stream-07 | **PASS** | ee1020a0..., 0534a4d9... | n/a | No cross-contamination, distinct trace_ids |
| S-stream-08 abort | PARTIAL / FAIL | ecfce6b2c6d11981fcbf3fc04f1f7586 | exit 1 status not aborted | Stream killed mid-flow but cleanup didn't flip status |
| S-stream-08 resend | **PASS** | n/a | n/a | Resend completed cleanly after abort |
| S-trace-01 | INCONCLUSIVE | (S-stream-01) | n/a | Pushback path produced only 1 chat_model span |
| S-trace-02 row 1 | FAIL | (S-stream-01) | exit 1 missing reasoning | Systemic L2.1 |
| S-trace-02 row 2 | INCONCLUSIVE | (S-stream-01) | exit 1 (verifier doesn't allow empty for reasoning-on) | Verifier semantic mismatch |
| S-trace-02 row 3 | PARTIAL-PASS / FAIL | f34109b9b6d4316b9154dcd74d2ccb39 | exit 1: got None, expected empty | gemini-off; SSE OK; Langfuse missing key |
| S-trace-05 | INCONCLUSIVE | 2bfaa6091e3b14f96f846e926d934083 | n/a | Cannot test without upstream reasoning blocks |
| S-trace-06 | FAIL | ecfce6b2c6d11981fcbf3fc04f1f7586 | exit 1 status not aborted | L2.2 abort cleanup not landing on root span |
| S-trace-09 | PARTIAL-PASS / FAIL | 0a48138eb44b63bb03127e78f29ac8c6 | exit 1: got None, expected empty | SSE: 0 reasoning events ✓; Langfuse contract drift |
| S-cross-01 | PARTIAL / FAIL | (S-stream-01) | exit 1 | session_id propagation OK; reasoning metadata FAIL |
| J-trace-01 | FAIL | (S-stream-01) | n/a | Tree shape doesn't match §6.3 (one-shot pushback) |
| S-chan-04 dev | INCONCLUSIVE | n/a | n/a | Cannot trigger assert without upstream reasoning |
| S-chan-04 prod | INCONCLUSIVE | n/a | n/a | Cannot trigger warning without upstream reasoning |
| S-stream-03 gemini-off | PARTIAL-PASS / FAIL | f34109b9b6d4316b9154dcd74d2ccb39 | exit 1 | SSE OK, Langfuse FAIL |
| S-stream-03 anthropic-on | PARTIAL-PASS / FAIL | 6204213010f5091b24c735a1b7398210 | exit 1 | **SSE shows real reasoning** (13 events), Langfuse missing |
| S-stream-03 anthropic-off | PARTIAL-PASS / FAIL | a9ffd7bc414d86f47aae1cd6a0509847 | exit 1 | SSE OK, Langfuse FAIL |
| S-stream-03 openai-on | UNEXPECTED / FAIL | 7015181f9f0b49593c6508c983478d32 | exit 1 | OpenAI gpt-5-mini reasoning-on emitted 0 wire-level reasoning |
| S-stream-03 openai-off | PARTIAL-PASS / FAIL | 208d515c9b411a0e688f5b2a1ac143a7 | exit 1 | SSE OK, Langfuse FAIL |
| S-rsn-* (all visual) | BLOCKED-NEEDS-CHROME | n/a | n/a | Main thread |
| S-chan-01/02/03 | BLOCKED-NEEDS-CHROME | n/a | n/a | Main thread |
| J-chan-01, J-rsn-01/02 | BLOCKED-NEEDS-CHROME | n/a | n/a | Main thread |
| S-trace-02 rows 4-5 | DEFERRED | n/a | n/a | unit tests cover; no agent config |
| S-trace-03 | DEFERRED | n/a | n/a | operator query; minimal value |
| S-trace-04 | DEFERRED | n/a | n/a | Braintrust eval batch |
| S-trace-07 | DEFERRED | n/a | n/a | folded into S-trace-06 |
| S-trace-08 | DEFERRED | n/a | n/a | covered by S-stream-07 |

## Failure analysis

### L2.1 — Systemic: `metadata.reasoning` never lands on Langfuse generations

**Suspected level:** L2 (integration / contract drift between `ReasoningTraceCallback` and Langfuse `CallbackHandler`'s contextvars stack).

**Evidence:**
- 100% of verifier runs across 3 providers × 2 modes report `metadata.reasoning` missing (treated as `None` in raw JSON, not `""`).
- Even the **anthropic-on row that emitted 13 real `data-reasoning-status` events at the SSE wire** (proving `ReasoningSegmenter` and the mapper saw reasoning blocks in the same astream loop) shows `metadata.reasoning: null` on the corresponding Langfuse generation.
- Inspect script (`artifacts/current/temp/inspect_trace.py`) confirms generation observations carry `ls_*` and `langgraph_*` metadata keys but no `reasoning` key.
- The mismatch is between the segmenter/mapper path (works) and the `on_llm_end` callback path (broken).

**Suspected root causes (in priority order):**
1. **Callback ordering on async dispatch.** Despite `run_inline = True` in `ReasoningTraceCallback`, the Langfuse async OpenTelemetry stack may pop the generation off contextvars in `on_llm_end_async` BEFORE our sync `on_llm_end` is dispatched. The `Context error: No active span in current context` warning visible in Batch 7 backend logs is a smoking gun — `update_current_generation` is being called when no observation is active.
2. **Trace observation filtering.** Langfuse may aggregate / collapse multiple `update_current_generation` calls into a single observation snapshot at flush time, and our metadata write loses the race against subsequent callback writes from `langfuse.langchain.CallbackHandler`.
3. **Wrong target span.** `update_current_generation` may be targeting the chain `model` span (CHAIN type) instead of the GENERATION-typed `ChatGoogleGenerativeAI` / `ChatAnthropic` span, since the contextvars stack at `on_llm_end` time may already have moved up.

**Suspected files:**
- `backend/agent_engine/streaming/reasoning_trace_callback.py:71-86` — `on_llm_end` handler
- `backend/agent_engine/agents/base.py:594-643` — `_build_langfuse_config` callback ordering
- (possible) Langfuse SDK 4.x async stack interaction

**Recommended next step:** add a debug log in `ReasoningTraceCallback.on_llm_end` printing `client.get_current_observation_id()` immediately before `update_current_generation` to confirm whether the contextvars-current observation is the expected GENERATION at write time. If not, switch to writing via the `run_id`-correlated handler API instead of `update_current_generation`.

### L2.2 — Abort cleanup status flag not landing on root span

**Evidence:** S-trace-06 / S-stream-08 abort case. `_handle_abort_cleanup` calls `client.update_current_span(metadata={"status": "aborted"})` — same contextvars race likely applies. Verifier reports `metadata.status == None` on root span instead of `"aborted"`.

**Same root-cause family as L2.1.** Likely fixed by the same investigation.

### L2.3 — Verifier `_root_span` looking for type=="SPAN" but Langfuse classifies the LangChain root as type=="CHAIN"

**Suspected level:** L2 (contract drift between verifier and the actual Langfuse 4.x observation classification for `langfuse.langchain.CallbackHandler` chain runs).

**Evidence:** Every single trace inspected shows the LangChain root run classified as `type=="CHAIN"` with `name=="chat-turn"`. The verifier's `_root_span()` filters for `type=="SPAN"` and so always returns None, producing the duplicate "root span not found" error in every result.

**Suspected files:**
- `backend/scripts/validation/verify_langfuse_trace.py:82-86` — `_root_span` should accept `type in ("SPAN","CHAIN")` or filter by name only.

**Note:** this bug is purely in the verifier helper — the actual implementation is fine. Worth a quick fix before next round so genuine failures aren't drowned in this noise.

### L1.1 — Anthropic `temperature` validation gap

**Suspected level:** L1 (config/validation gap).

When binding `anthropic:claude-sonnet-4-5-20250929` with `reasoning="on"` and `temperature=0.0`, Anthropic API returns 400: "`temperature` may only be set to 1 when thinking is enabled". `_init_model` validates `thinking_budget >= 1024` but doesn't validate the temperature constraint. Discoverable only at runtime — first SSE event becomes an `error`.

**Suspected files:** `backend/agent_engine/agents/base.py:118-138` — anthropic branch of `_init_model`.

**Recommended:** add a validation in `_init_model` that raises ValueError at startup if anthropic + reasoning="on" + temperature != 1.0 (the API doesn't accept anything else). Same defensive pattern as the existing `thinking_budget` validation.

### L1.2 — gpt-5-mini reasoning-on emits zero wire-level reasoning events

**Suspected level:** L1 or L2 (provider integration).

**Evidence:** gpt-5-mini with `reasoning_effort="medium"` + `use_responses_api=True` emitted 2173 text-delta events but 0 `data-reasoning-status` events at the SSE wire level — meaning `StreamEventMapper` did not see any `reasoning` content blocks from the upstream `astream()`. This contradicts the design's expectation that OpenAI gpt-5 series surfaces reasoning under the responses API.

**Possible explanations:**
1. gpt-5-mini may emit reasoning summaries through a different content_block shape that the mapper doesn't recognize.
2. The `use_responses_api=True` kwarg may not be triggering reasoning-summary streaming in the current `langchain-openai` version.
3. Reasoning summaries may only land on `on_llm_end` (full payload) and not stream incrementally.

**Suspected files:** 
- `backend/agent_engine/streaming/event_mapper.py` — content_blocks handling for OpenAI provider.
- `backend/agent_engine/agents/base.py:140-145` — openai branch of `_init_model` (verify `use_responses_api` is the right kwarg name; LangChain may have renamed it).

### L1.3 — Default Gemini canonical prompt triggers one-shot pushback

**Suspected level:** L1 (test-data / prompt engineering, not implementation).

**Evidence:** D25 canonical prompt "Compare Apple's 10-K Q3 2024 vs Q3 2023 risk factors..." — Gemini 2.5 Flash with reasoning-on responds with a single text turn explaining "10-K is annual, not quarterly" and asks the user to clarify. No tool calls, no multi-call shape, no reasoning_blocks. This breaks scenarios that asserts `≥3 chat_model spans` (S-trace-01) or multi-call abort timing (S-stream-08 had to use a different prompt).

**Recommended:** consider adopting a more tool-forcing canonical prompt for reasoning-on Gemini scenarios, e.g. explicitly instruct "Use the SEC filing tools to fetch sections X, Y, Z and compare". Or pin S-trace-01 / S-stream-08 / J-trace-01 to a known-multi-call prompt distinct from D25.

## Tensions surfaced for parent thread

1. **`StreamChatRequest` rejects same-session concurrent (HTTP 409)** but the design doc S-stream-07 says "same session two tabs". I ran with two distinct session IDs as the closest practical equivalent. The tension: real "two tabs same session" cannot exist with the current `_active_sessions` set guard. Either the design needs to drop the same-session constraint, or the active-sessions guard needs to relax to allow concurrent reads / multiple in-flight per session. Currently neither is wrong on its own, but they're inconsistent.

2. **Verifier exit codes do not distinguish "implementation broken" from "verifier-vs-Langfuse contract drift"**. Most "FAIL" exit codes in this round are L2.3 noise (root-span type mismatch) plus L2.1 (real metadata bug). Hard to triage without manual trace inspection. Recommend fixing the verifier's `_root_span` filter before next round.

3. **OpenAI gpt-5-mini integration unverified at wire level** for reasoning-on. The design assumes all three providers emit reasoning events under reasoning-on, but only Anthropic actually does in this round. Either the OpenAI integration needs a fix (L1.2) or the design should call out OpenAI reasoning visibility as best-effort.

4. **Anthropic temperature constraint** (L1.1) — unobvious until you hit the API. Worth a startup-time validation.

5. **`STUB_REASONING_ONLY` and `S-chan-04` flag scenarios are not testable with default Gemini** because Gemini doesn't emit reasoning blocks under default config. They need either a known-emitting model (Anthropic) or a deeper stub that injects reasoning blocks at the segmenter level rather than at the serializer level.

6. **`S-stream-08` abort timing is fragile** — with a fast-finishing prompt, the curl kill arrives after `finish` and the test becomes invalid. I had to use a longer multi-tool-forcing prompt and 4-second sleep to actually catch the stream mid-flow. Document this in the operator runtime guide.

## Files generated

All under `artifacts/current/temp/`:
- Backend logs: `round1v2-backend-batch-{1,2,5,6,7-dev,7-prod,8-anthropic-on,8-anthropic-off,9-openai-on,9-openai-off,10-gemini-off}.log`
- SSE captures: `sse-{S-stream-01,S-stream-04,S-stream-05,S-stream-07-A,S-stream-07-B,S-stream-08-aborted,S-stream-08-resend,S-trace-05,S-trace-09,S-chan-04-dev,S-chan-04-prod,S-stream-03-gemini-off,S-stream-03-anthropic-on,S-stream-03-anthropic-off,S-stream-03-openai-on,S-stream-03-openai-off}.txt`
- Session ID files: `sse-*.session`
- Trace ID files: `trace-*.txt`
- Helpers: `find_trace_by_session.py`, `inspect_trace.py`
