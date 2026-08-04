# Executable Verification Plan — DEV-109 (BIND-AT-RUN resolved)

Source: `artifacts/current/verification-plan.md` (DEV-108, clean-room). This file resolves every
`[BIND-AT-RUN: ...]` marker against the actual codebase as of branch `feat/multi-provider-streaming-reasoning`
@ `aada958`. Resolution research recorded below each item; **negative findings** (plan assumption
didn't match code) are called out explicitly per the plan's own rule: "綁不上本身就是 finding".

## Environment facts (resolved)

| Fact | Plan assumed | Actual |
|---|---|---|
| Backend stream endpoint | `POST http://localhost:8000/api/v1/chat/stream` | **`POST http://localhost:8000/api/v1/chat`** (finding: path differs) |
| Backend port | 8000 | 8000 (confirmed) |
| Frontend dev port | 5173 | 5173 (confirmed, `vite.config.ts`) |
| Stream request body | unspecified | `{"id": "<session-id>", "messages": [{"role":"user","parts":[{"type":"text","text":"<prompt>"}]}], "trigger":"submit-message"}` — see `backend/api/routers/chat.py:33-73` (`StreamChatRequest`) |
| Non-streaming invoke endpoint | assumed exists | `POST /api/v1/chat/invoke`, body `{"message": str, "session_id": str | null}`, resp `{"response","tool_outputs","session_id","version"}` (`backend/api/routers/chat_invoke.py`) |
| Session/thread id field | assumed one field | `id` on `/chat`, `session_id` on `/chat/invoke` and Langfuse — **same underlying value**, different field name per layer (finding, cosmetic) |
| Provider/reasoning config | admin runtime setting | **Static YAML + backend restart**, no env var / no runtime toggle (finding — heavier than plan assumed). File: `backend/agent_engine/agents/profiles/baseline/orchestrator_config.yaml`. Schema: `ModelConfig.reasoning: Literal["on","off","unsupported"]` (`config_loader.py:10-36`) |
| Current default (no override) | unspecified | OpenAI `gpt-5-mini`, `reasoning: "on"`, `temperature: 0.0` — i.e. **default = GPT reasoning-on**, all 5 shipped profiles identical |
| Gemini reasoning-on | `[BIND-AT-RUN]` | edit `orchestrator_config.yaml`: `name: "google_genai:gemini-2.5-flash"`, `reasoning: "on"`, `thinking_budget: 8192`; restart backend |
| Gemini reasoning-off | `[BIND-AT-RUN]` | same `name`, `reasoning: "off"` (forces `thinking_budget=0`) |
| GPT reasoning-on | `[BIND-AT-RUN]` | already the shipped default — no edit needed |
| unsupported | `[BIND-AT-RUN]` | **no shipped profile uses it, but the schema accepts it** — set `reasoning: "unsupported"` on any model in the YAML (same edit-and-restart mechanism as every other state); treated as resolvable, not a finding, since OQ2's fallback ("record as finding if unproducible") doesn't apply — it IS producible |
| `FORCE_LLM_FAIL` | assumed can fail mid-reasoning | **Cannot** — raises `RuntimeError` in `base.py:502-503` **before** `agent.astream()` is ever called, so no reasoning part can be open when it fires (`backend/tests/agents/test_orchestrator_dev_flags.py` confirms by design). **Finding, per ratified OQ6**: S-wire-04's precondition ("if error occurs while reasoning part is open") is never met by this env var in this environment. Also only wired into the streaming path, not `/chat/invoke`. |
| Langfuse root span | assumed name `chat_turn` | confirmed — `start_as_current_observation(as_type="span", name="chat_turn")` (`base.py:491-493`), **streaming path only**; `/chat/invoke` has no equivalent named span (finding: S-iso-03 "no transcript write" is trivially true for a structural reason — no `chat_turn` span exists at all on invoke, not because the key is absent from an existing span) |
| Langfuse trace lookup | assumed trace id or session id | **by `session_id`** (+ `trace_name` = `f"{profile}_{mode}"` e.g. `baseline_stream`, + time window) — no trace id is ever returned in the HTTP response |
| Reasoning transcript key | `reasoning` | confirmed, `ReasoningTranscriptAccumulator.METADATA_KEY = "reasoning"` (`reasoning_transcript_accumulator.py:43`) |
| Abort status key | `[BIND-AT-RUN]` | confirmed — `metadata.status = "aborted"` on the **same** `chat_turn` root span object as `metadata.reasoning` (`base.py:592-599`), only set on `asyncio.CancelledError` |
| Reasoning chip container | `[BIND-AT-RUN]` | `data-testid="reasoning-chip"` (+ `data-state`, `data-round`); header `data-testid="reasoning-chip-header"` carries `aria-live="polite"` (`ReasoningChip.tsx:52-62`) |
| Chip body | — | `data-testid="reasoning-chip-body"` (`ReasoningChip.tsx:80`) |
| Tool card | `[BIND-AT-RUN]` | `data-testid="tool-card"` (+ `data-tool-call-id`, `data-tool-state`); expand trigger `data-testid="tool-card-expand"`. No separate "Tool progress" testid — progress text is inline in `ToolRow` (finding: scope by `[data-tool-state="input-streaming"]` instead) |
| Activity indicator | `[BIND-AT-RUN]` | `data-testid="activity-placeholder"`, carries `aria-live="polite"` (`ActivityPlaceholder.tsx:14-17`) |
| Stop control | `[BIND-AT-RUN]` | `data-testid="composer-stop-btn"`, `aria-label="Stop response"` (`Composer.tsx:71-73`) |
| Regenerate control | `[BIND-AT-RUN]` | exists — `data-testid="regenerate-btn"` (`RegenerateButton.tsx:9-10`) |
| Chip header text | assumed `Thought for Xs` / `Stopped — thought for Xs` | confirmed exactly, `reasoning-chips.ts:88-96` — streaming not-stalled `"Thinking…"`, streaming stalled `"Still working…"`, aborted `` `Stopped — thought for ${s}s` ``, done `` `Thought for ${s}s` `` |
| Stall timer | 10s | confirmed, `STALL_THRESHOLD_MS = 10_000` (`timing.ts:10`), wall-clock (`Date.now()` deltas) in `useStallTimer.ts` |
| `PLACEHOLDER_GRACE_MS` | 300ms | confirmed, `timing.ts:21` = `300` |
| Route-mock mechanism | assumed Playwright `page.route()` | **use existing MSW fixture pattern instead** — `frontend/src/__tests__/msw/fixtures/*.ts` registry + `chat.gotoFixture(name)` helper (`frontend/tests/e2e/fixtures.ts:14-16`); closest analogs: `slow-start-stream.ts` (placeholder/stall) and `long-reasoning-then-text.ts` (chip edge cases). New fixtures needed for S-chip-06/S-place-04/S-place-05. |

## Adjustments to scenario execution (from findings above)

- **S-wire-04 / S-pres-03**: `FORCE_LLM_FAIL` cannot satisfy the "reasoning part open at error time" precondition. Execute with `FORCE_LLM_FAIL` as specified anyway (it's still a valid, simpler error-path check: error before any reasoning), record actual event order, and mark the *mid-reasoning* ordering claim as **not-exercised / known gap** rather than force a fail — consistent with the ratified handling of unresolvable binds (findings, not invented mocks) unless a trivial route-level mock is cheap to add.
- **S-trace-03 unsupported / S-wire-05 off**: both achievable via YAML edit + restart.
- **S-iso-03**: verify against `/api/v1/chat/invoke`; expect no `chat_turn`-named span at all (structural absence), not just an absent `reasoning` key on an existing span — note this nuance in the PASS rationale.
- All `curl` commands target `POST http://localhost:8000/api/v1/chat` (not `/chat/stream`).

---

## Automated Verification — Deterministic

(carries forward S-wire-01..05, S-trace-01..03, S-iso-01..03 from `verification-plan.md` verbatim,
with the endpoint path, request schema, and config-switch mechanism above substituted wherever
`[BIND-AT-RUN]` appeared.)

## Automated Verification — Playwright

(carries forward S-chip-02/03/04/06/08/09, S-place-02/04/05, J-03 verbatim, with selectors above
substituted. S-chip-06/S-place-04/S-place-05 use the MSW fixture mechanism, not `page.route()` —
new fixture files to be added under `frontend/src/__tests__/msw/fixtures/` if not already present.)

## Automated Verification — Browser-Use CLI

(carries forward S-chip-01/05/07, S-place-01/03, S-pres-01..05, J-01, J-02 verbatim, targeting real
backend at the resolved endpoint/ports, with the config-switch mechanism above for provider changes.)

Full scenario text (Given/When/Then + Method/Steps/Expected) is unchanged from
`artifacts/current/bdd-scenarios.md` + `artifacts/current/verification-plan.md` — this file is the
resolution index, not a duplicate. The Verifier subagent must read both plus this file.
