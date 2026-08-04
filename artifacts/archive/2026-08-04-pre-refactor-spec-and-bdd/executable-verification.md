# Executable Verification Plan (V2 — real backend + Claude in Chrome)

Generated 2026-05-06. Methodology pivot: **MSW/Playwright fixtures are implementation-phase concerns; BDD verification uses real backend + real LLM API + real Langfuse trace + browser automation against real services.**

## Resolved facts

| Item | Resolution |
|---|---|
| Backend stream endpoint | `POST http://127.0.0.1:8000/api/v1/chat` (body: `{id, messages:[{role,parts:[{type:"text",text}]}], trigger:"submit-message"}`) |
| Backend invoke endpoint | `POST http://127.0.0.1:8000/api/v1/chat/invoke` (body: `{message, session_id?}`) |
| Backend default agent | `v1_baseline` (Gemini 2.5 Flash, reasoning=on) — bound at FastAPI startup, no per-request override |
| Frontend dev server | `http://localhost:5173` via `pnpm run dev`; `/api/*` proxies to `http://localhost:8000` |
| Langfuse trace verifier CLI | `uv run python -m backend.scripts.validation.verify_langfuse_trace <trace_id> --expect-{reasoning-on,reasoning-off,unsupported,aborted}` |
| .env keys available | GOOGLE_API_KEY, ANTHROPIC_API_KEY, OPENAI_API_KEY, LANGFUSE_*, BRAINTRUST_API_KEY, TAVILY_API_KEY, EDGAR_IDENTITY |
| Dev flags implemented | `FORCE_LLM_FAIL`, `FORCE_REASONING_NON_TRANSIENT`, `EMIT_DELAYED_REASONING`, `EMIT_LATE_REASONING`, `STUB_REASONING_ONLY`, `STUB_CONTENT_BLOCKS_NO_REASONING=<provider>` — set as env on backend launch |
| Frontend testid contract | `composer-textarea`, `composer-send-btn`, `composer-stop-btn`, `composer-clear-btn`, `message-list[data-status=submitted/streaming/ready/error]`, `assistant-message`, `reasoning-indicator` (with `.reasoning-status.stalled` modifier), `tool-card[data-tool-state]`, `error-title`, `chat-panel` |

## NOT-IMPLEMENTED (blocked at code level)

| Scenario | Why blocked |
|---|---|
| S-stream-02 | No per-session agent-switch endpoint exists |
| S-rsn-14 (manual portion) | No screen reader available in this environment |

## Verification batches (real-backend topology)

Each batch starts the backend on :8000 with a specific env profile, runs the in-batch scenarios, then tears down before the next batch.

### Batch 1 — default Gemini reasoning-on (no dev flags)

Backend launch:
```bash
uv run uvicorn backend.api.main:app --host 127.0.0.1 --port 8000
```

Scenarios:
- **S-stream-01** — default agent canonical SEC query → curl + Langfuse `--expect-reasoning-on`
- **S-stream-05** — `Orchestrator.invoke` reasoning trace → Python script + Langfuse
- **S-stream-07** — multi-tab concurrency → 2 parallel curls, two distinct trace_ids
- **S-stream-08** — abort + resend → curl with sleep+kill, trace `--expect-aborted`, then new curl completes
- **S-trace-01** — multi-call N spans → S-stream-01 trace tree shape assertion
- **S-trace-02 row 1** — reasoning-on real → `--expect-reasoning-on`
- **S-trace-02 row 2** — reasoning-on but short prompt → `--expect-reasoning-on` allows empty
- **S-trace-06** — abort tail → same as S-stream-08 trace
- **S-cross-01** — POC ship gate → S-stream-01 + verify `session_id`/`user_id` propagation
- **S-rsn-01/02** — frontend lifecycle dots→text → Claude in Chrome
- **S-rsn-04** — long CJK reasoning render → Claude in Chrome
- **S-rsn-08** — abort sub-states (5 phases) → Claude in Chrome
- **S-rsn-09** — error sub-states → blocked (errors injected via Batch 2 / network kill)
- **S-rsn-11** — clear during in-flight → Claude in Chrome
- **S-rsn-13 / J-rsn-02** — abort + resend UI → Claude in Chrome
- **S-chan-01** — transient flag mid-stream DOM → Claude in Chrome (poll DOM during stream)
- **S-chan-02** — page reload no leak → Claude in Chrome
- **J-chan-01** — channel isolation full → Claude in Chrome
- **J-rsn-01** — 10-state journey → Claude in Chrome
- **J-trace-01** — trace tree assertion → curl + Langfuse trace tree

### Batch 2 — `FORCE_LLM_FAIL=1`

Backend launch:
```bash
FORCE_LLM_FAIL=1 uv run uvicorn backend.api.main:app --host 127.0.0.1 --port 8000
```

Scenarios:
- **S-stream-04 mid-stream** — first LLM call raises → curl, expect SSE error event + `Finish(error)`

### Batch 3 — `EMIT_DELAYED_REASONING=1`

Scenarios:
- **S-rsn-06** — stalled visual after 11s silence → Claude in Chrome (wait 11s, assert `.stalled` class)

### Batch 4 — `EMIT_LATE_REASONING=1`

Scenarios:
- **S-rsn-12** — late event after finish → Claude in Chrome (assert indicator stays hidden)

### Batch 5 — `STUB_REASONING_ONLY=1`

Scenarios:
- **S-trace-05** — reasoning-only stream tail → curl, Langfuse trace verify reasoning content not lost

### Batch 6 — `STUB_CONTENT_BLOCKS_NO_REASONING=google_genai`

Scenarios:
- **S-trace-09** — content_blocks failure graceful degrade → curl, count `data-reasoning-status` = 0, Langfuse `metadata.reasoning == ""`

### Batch 7 — `FORCE_REASONING_NON_TRANSIENT=1` + dev mode

Scenarios:
- **S-chan-03** — frontend filter blocks non-transient → Claude in Chrome (assert reasoning text NOT in transcript)
- **S-chan-04** — backend assert in dev raises → curl, expect SSE error or visible warning log

### Batch 8 — Anthropic agent (temp YAML edit on v2_reader)

Scope decision: temporarily edit `backend/agent_engine/agents/versions/v2_reader/orchestrator_config.yaml` to bind `anthropic:claude-sonnet-4-5-20250929` (claude 4.x sonnet) reasoning=on, restart backend with `DEFAULT_WORKFLOW_VERSION=v2_reader` env (need to verify `main.py` honors this — currently hardcoded). **If env override not honored, edit `main.py:25` temporarily for verification, restore after.**

Scenarios:
- **S-stream-03 anthropic-on row** — curl + Langfuse expect-reasoning-on
- **S-rsn-05** — interleaved reasoning↔text → Claude in Chrome
- **S-stream-03 anthropic-off row** — same backend with `reasoning: "off"` YAML edit, expect-reasoning-off

### Batch 9 — OpenAI agent (temp YAML edit)

Bind v3_quant to `openai:gpt-5-mini-responses` (model name needs verification against current OpenAI naming).

Scenarios:
- **S-stream-03 openai-on / openai-off** — same pattern as Batch 8

### Batch 10 — Gemini reasoning-off (temp YAML edit)

Bind v4_graph to gemini-2.5-flash reasoning=off.

Scenarios:
- **S-stream-03 gemini-off row** — curl + Langfuse expect-reasoning-off
- **S-rsn-07** — reasoning-off post-tool idle text → Claude in Chrome (assert "Synthesizing"/"Thinking" idle text)
- **S-trace-02 row 3** — reasoning-off mode → expect-reasoning-off

### Manual / blocked

- **S-stream-02** — NOT-IMPLEMENTED (no agent-switch endpoint)
- **S-rsn-14** — manual screen reader (NOT-RUNNABLE in this environment)
- **S-trace-02 row 4** (`<unsupported>` sentinel) — needs an agent config with `reasoning: "unsupported"` (none exist in tree); decide: skip or add config
- **S-trace-02 row 5** (oversize 500KB truncate) — needs deliberate large reasoning; covered by unit test, integration impractical without stub
- **S-trace-03 (operator query)** — read-only Langfuse SQL on seeded data; minimal value to re-run if all S-trace-01/02 pass
- **S-trace-04 (judge model exclusion)** — needs Braintrust eval batch run; defer to dedicated eval pass
- **S-trace-07 (UX/trace divergence)** — folded into S-trace-06 abort-with-tail comparison
- **S-trace-08 (multi-tab Langfuse)** — covered by S-stream-07 + Langfuse trace_id check

## Sequence

1. Backend curl batches first (Batches 1-7 backend curl portions, then 5/6/9/10) — delegate to Verifier subagent (read-only, bash + curl).
2. Frontend Claude-in-Chrome scenarios — done by main thread (Claude in Chrome MCP scoped to main session).
3. Combine results into `artifacts/current/temp/bdd-verification-round-1-v2.md`.

## Risks / scope decisions to flag

- **YAML edits for matrix (Batches 8-10)** mutate real config files. Will revert after verification. Flag any test failure that the user might want to discuss before YAML revert.
- **LLM cost**: each curl run = one Gemini/Anthropic/OpenAI session with multi-tool synthesis (~3-5 LLM calls + tool calls). Estimated ~$0.05-0.15 per scenario × ~15 LLM-calling scenarios = **~$1-2 total**.
- **Langfuse propagation lag**: verify_langfuse_trace.py polls 5×1s linear backoff; if a trace doesn't show up in 15s, mark scenario as INCONCLUSIVE rather than FAIL.
