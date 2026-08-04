# BDD Verification — Round 1

## Summary

- Total scenarios: 27 illustrative + 5 journey + 1 cross-feature = **33 scenario IDs** (counting J-* and S-cross-01 separately; PO-only S-stream-06 deferred and not counted)
- **PASS:** 11
- **FAIL:** 7 — `J-chan-01/S-chan-02`, `S-chan-01`, `S-chan-03`, `S-rsn-01/02`, `S-rsn-04`, `S-rsn-06`, `S-trace-05`, `S-rsn-13/J-rsn-02` (cluster of 7 failing specs covering 8 scenario IDs)
- **BLOCKED-LIVE-API:** 14
- **NOT-IMPLEMENTED:** 2 (`S-stream-02`, `S-rsn-14`)
- Test commands run:
  - Backend pytest: **307 passed / 0 failed**
  - Frontend tsc: **clean**
  - Frontend eslint: **0 errors / 1 warning** (unused-eslint-disable in `public/mockServiceWorker.js`, vendored MSW worker)
  - Frontend vitest: **216 passed / 0 failed** (23 files)
  - Frontend Playwright (chromium): **21 passed / 9 failed / 5 skipped** of 35 total

Plus 1 unrelated regression: `tests/e2e/critical/stop-preserves-partial.spec.ts` (timing failure on `composer-stop-btn` — long-text fixture finishes before stop click is reachable).

---

## Step 1 — Backend pytest

```
uv run pytest backend/tests/streaming backend/tests/agents backend/tests/api -v --tb=short --timeout=60
exit code: 0
```

`307 passed, 3 warnings in 52.35s`. All scenario-mapped backend tests passed:

- `test_orchestrator_dev_flags.py` (S-stream-04 mid-stream LLM fail) — PASS
- `test_orchestrator_invoke_reasoning_path.py` (S-stream-05 invoke reasoning) — PASS
- `test_reasoning_segmenter.py` (S-stream-09 80-char fallback) — PASS
- `test_event_mapper_dev_flags.py` (S-rsn-06 / S-rsn-12 / S-trace-05 / S-trace-09 fixtures at unit level) — PASS
- `test_reasoning_trace_callback.py` (S-trace-02 5-case schema) — PASS
- `test_sse_serializer.py` (S-chan-01 transient flag, S-chan-04 assert+warn) — PASS
- `test_sse_serializer_dev_flags.py` (S-chan-03 FORCE_REASONING_NON_TRANSIENT) — PASS
- `test_orchestrator_langfuse.py` (S-trace-06 abort cleanup `reasoning_tail_aborted`) — PASS

Full log: `artifacts/current/temp/round-1-step1-pytest.log`.

---

## Step 2 — Frontend tsc / lint / unit

```
pnpm exec tsc -b --noEmit         # exit 0, no diagnostics
pnpm exec eslint .                 # 0 errors, 1 warning
pnpm test                          # vitest: 23 files, 216 tests, all passed
```

ESLint warning (non-blocking, vendored file):

```
public/mockServiceWorker.js
  1:1  warning  Unused eslint-disable directive (no problems were reported)
```

Logs:
- `artifacts/current/temp/round-1-step2-tsc.log` (empty = clean)
- `artifacts/current/temp/round-1-step2-eslint.log`
- `artifacts/current/temp/round-1-step2-vitest.log`

---

## Step 3 — Frontend Playwright e2e (chromium)

```
pnpm exec playwright test --project=chromium --reporter=list
35 tests total — 21 passed, 9 failed, 5 skipped (3.2 min)
```

Webserver auto-built and started `pnpm run preview:e2e` on 5173 successfully. Backend was not running.

### Per-spec results

PASSED (21):
- `critical/gateway-sse-error.spec.ts` — gateway SSE error renders ErrorBlock+Retry
- `critical/error-recovery.spec.ts` — pre-stream error recovery
- `critical/mid-stream-error.spec.ts` — mid-stream error preserves partial text
- `critical/clear-then-send-new-chat-id.spec.ts` — Clear+chip-send uses post-Clear chatId
- `critical/pre-stream-409.spec.ts` — 409 surfaces retriable
- `critical/regenerate-double-click.spec.ts` — double-click dispatches single regenerate
- `critical/refresh-invariant.spec.ts` — refresh produces clean state
- `critical/multi-tool-partial-failure.spec.ts` — 3 parallel tools attribute correctly
- `critical/regenerate-retry.spec.ts` — regenerate retry succeeds w/o duplicate
- `critical/multi-provider-matrix.spec.ts` — Gemini ON row only (5 others self-skipped, expected)
- `security/xss-source-link.spec.ts` (×2) — XSS sanitized
- `smoke/app-shell.spec.ts`, `smoke/clear-session.spec.ts`, `smoke/scroll-behavior.spec.ts` (×2), `smoke/slow-start-stream.spec.ts`
- `lifecycle/reasoning-indicator-states.spec.ts:40` — **S-rsn-03** indicator clears on text-start (PASS)
- `lifecycle/reasoning-indicator-states.spec.ts:77` — **S-rsn-08** indicator clears on finish (PASS)
- `lifecycle/reasoning-late-events.spec.ts` — **S-rsn-12** late events ignored (PASS)
- `lifecycle/trace-no-reasoning-blocks.spec.ts` — **S-trace-09** content_blocks regression UI (PASS)

SKIPPED (5): the 5 non-Gemini matrix rows (anthropic-on/off, openai-on/off, gemini-off — runtime-override gated). Expected per `executable-verification.md`.

FAILED (9 specs):

1. `critical/stop-preserves-partial.spec.ts` — `getByTestId('composer-stop-btn')` not present at click time. Root cause: `long-text-stream` fixture (50 chunks × 50 ms = ~2.5 s total) finishes before the test waits for `Paragraph 0.` and clicks Stop, so the Composer has already flipped back to `ready` and the stop button is gone. **Not in BDD scope** but a real regression.

2. `journeys/abort-then-resend.spec.ts` — **J-rsn-02 / S-rsn-13**: spec calls `chat.gotoFixture("long-reasoning-then-text")` — fixture does not exist in `frontend/src/__tests__/msw/fixtures/index.ts`.

3. `lifecycle/reasoning-channel-isolation.spec.ts:26` — **J-chan-01 / S-chan-02**: spec calls `chat.gotoFixture("reasoning-then-text")` — fixture does not exist. Handler returns HTTP 500 with `{"error":"unknown fixture"}`, message-list flips to `data-status="error"`, `waitReady()` times out.

4. `lifecycle/reasoning-channel-isolation.spec.ts:46` — **S-chan-01**: same missing `reasoning-then-text` fixture. HTTP 500 → status=error.

5. `lifecycle/reasoning-channel-isolation.spec.ts:82` — **S-chan-03**: same missing `reasoning-then-text` fixture. HTTP 500 → status=error.

6. `lifecycle/reasoning-indicator-states.spec.ts:19` — **S-rsn-01 / S-rsn-02**: spec calls `chat.gotoFixture("happy-text")` then asserts `reasoning-indicator` is visible. The `happy-text` fixture only emits `text-start/text-delta/text-end/finish` — no `data-reasoning-status` events at all, so the indicator never mounts.

7. `lifecycle/reasoning-indicator-states.spec.ts:59` — **S-rsn-04**: spec calls `chat.gotoFixture("tool-call-then-text")` — fixture does not exist (the actual fixture name is `happy-tool-then-text`). Handler returns HTTP 500.

8. `lifecycle/reasoning-stalled.spec.ts:20` — **S-rsn-06**: spec calls `chat.gotoFixture("happy-text")` (tension flagged in plan) and asserts indicator visible — `happy-text` emits no reasoning events, indicator never mounts.

9. `lifecycle/trace-tail-stream-only.spec.ts:18` — **S-trace-05**: spec calls `chat.gotoFixture("happy-text")` and asserts indicator visible — same root cause: no reasoning events in the fixture.

First 10 lines of representative failures:

> `S-chan-01` (locator=message-list, expected=ready, received=error, 13 retries against `<div data-status="error" data-testid="message-list">`). Caused by handlers.ts returning `HttpResponse.json({error:"unknown fixture: reasoning-then-text"}, status:500)`.

> `S-rsn-01/02` (locator=reasoning-indicator, expected=visible, "element(s) not found" after 10 s). Caused by `happy-text` fixture emitting only text frames.

> `stop-preserves-partial` (locator=composer-stop-btn, "Test timeout of 30000ms exceeded" waiting for click target). Caused by long-text fixture finishing too quickly.

Full log: `artifacts/current/temp/round-1-step3-playwright.log`.

---

## Per-scenario classification

### Provider Streaming Pipeline

| Scenario ID | Status | Evidence | Notes |
|---|---|---|---|
| S-stream-01 | BLOCKED-LIVE-API | needs Gemini call + Langfuse `ls_model_name` | Multi-provider matrix Gemini-ON UI smoke passes. |
| S-stream-02 | NOT-IMPLEMENTED | no per-session agent-switch endpoint | per `executable-verification.md` |
| S-stream-03 | BLOCKED-LIVE-API | matrix self-skips 5/6 rows | Gemini-ON row passes. |
| S-stream-04 | PASS | `test_orchestrator_dev_flags.py` (FORCE_LLM_FAIL) | mid-stream + pre-SSE branches covered. |
| S-stream-05 | PASS | `test_orchestrator_invoke_reasoning_path.py` | invoke path writes `metadata.reasoning`. |
| S-stream-06 | DEFERRED | moved out of scope per spec | not counted. |
| S-stream-07 | BLOCKED-LIVE-API | multi-tab + Langfuse | -- |
| S-stream-08 | BLOCKED-LIVE-API | abort+resend with Langfuse | backend abort cleanup unit test passes (`test_orchestrator_langfuse.py::TestAstreamAbortCleanup`). |
| S-stream-09 | PASS | `test_reasoning_segmenter.py` (CJK 80-char fallback) | -- |
| J-stream-01 | BLOCKED-LIVE-API | full 6-case matrix needs all keys | -- |

### Reasoning Channel Isolation

| Scenario ID | Status | Evidence | Notes |
|---|---|---|---|
| S-chan-01 | FAIL | `reasoning-channel-isolation.spec.ts:46` | missing `reasoning-then-text` MSW fixture; backend `test_sse_serializer.py` PASSES. |
| S-chan-02 | FAIL | covered by `J-chan-01` spec | missing fixture. |
| S-chan-03 | FAIL | `reasoning-channel-isolation.spec.ts:82` | missing fixture; backend `test_sse_serializer_dev_flags.py` PASSES. |
| S-chan-04 | PASS | `test_sse_serializer.py` assert+warn | -- |
| J-chan-01 | FAIL | `reasoning-channel-isolation.spec.ts:26` | missing fixture. |

### Reasoning Indicator Lifecycle

| Scenario ID | Status | Evidence | Notes |
|---|---|---|---|
| S-rsn-01 | FAIL | `reasoning-indicator-states.spec.ts:19` | `happy-text` fixture emits no reasoning events → indicator never mounts. |
| S-rsn-02 | FAIL | same spec | same root cause as S-rsn-01. |
| S-rsn-03 | PASS | `reasoning-indicator-states.spec.ts:40` | indicator clears on text-start (no reasoning needed for assertion). |
| S-rsn-04 | FAIL | `reasoning-indicator-states.spec.ts:59` | calls `tool-call-then-text` — fixture name does not exist (actual is `happy-tool-then-text`). |
| S-rsn-05 | NOT-COVERED | no e2e/unit spec maps to Anthropic Option B re-entry | requires Anthropic live or new MSW fixture. |
| S-rsn-06 | FAIL | `reasoning-stalled.spec.ts:20` | `happy-text` fixture emits no reasoning → no indicator → can never apply `.stalled`. Backend unit test PASSES. |
| S-rsn-07 | NOT-COVERED | no spec for D15 idle text | no MSW fixture for post-tool gap. |
| S-rsn-08 | PASS (partial) | `reasoning-indicator-states.spec.ts:77` covers indicator-clears-on-finish | full 5-row table not exercised. |
| S-rsn-09 | NOT-COVERED | no spec for stream-error sub-states | -- |
| S-rsn-10 | BLOCKED-LIVE-API | hold-and-flush ordering needs live model | -- |
| S-rsn-11 | NOT-COVERED | no spec for clearedRef guard | -- |
| S-rsn-12 | PASS | `reasoning-late-events.spec.ts` + `test_event_mapper_dev_flags.py::EMIT_LATE_REASONING` | -- |
| S-rsn-13 | FAIL | covered by `abort-then-resend.spec.ts` | missing `long-reasoning-then-text` fixture. |
| S-rsn-14 | NOT-IMPLEMENTED | requires LiveStatusAnnouncer — no spec found | screen-reader test not wired. |
| J-rsn-01 | NOT-COVERED | journey lifecycle requires reasoning fixtures | depends on missing reasoning fixtures. |
| J-rsn-02 | FAIL | `abort-then-resend.spec.ts` | missing fixture. |

### Langfuse Reasoning Persistence

| Scenario ID | Status | Evidence | Notes |
|---|---|---|---|
| S-trace-01 | BLOCKED-LIVE-API | needs Langfuse + live LLM | -- |
| S-trace-02 | PASS | `test_reasoning_trace_callback.py` (5 schema rows) | -- |
| S-trace-03 | BLOCKED-LIVE-API | operator queries against seeded traces | -- |
| S-trace-04 | BLOCKED-LIVE-API | judge model exclusion needs Braintrust+Langfuse | -- |
| S-trace-05 | FAIL (UI) / PASS (backend) | `test_event_mapper_dev_flags.py::STUB_REASONING_ONLY` PASSES; `trace-tail-stream-only.spec.ts` FAILS because `happy-text` MSW fixture doesn't simulate STUB_REASONING_ONLY | classify FAIL since UI assertion is the spec contract. |
| S-trace-06 | PASS (backend) / BLOCKED-LIVE-API (Langfuse query) | `test_orchestrator_langfuse.py::TestAstreamAbortCleanup` PASSES (writes `reasoning_tail_aborted`+`status="aborted"`) | full operator query needs live trace. |
| S-trace-07 | BLOCKED-LIVE-API | UX/trace divergence comparison | -- |
| S-trace-08 | BLOCKED-LIVE-API | multi-tab Langfuse | -- |
| S-trace-09 | PASS | `test_event_mapper_dev_flags.py` + `trace-no-reasoning-blocks.spec.ts` | both layers green. |
| J-trace-01 | BLOCKED-LIVE-API | full trace tree | -- |

### Cross-Feature

| Scenario ID | Status | Evidence | Notes |
|---|---|---|---|
| S-cross-01 | BLOCKED-LIVE-API | POC ship gate needs live LLM + Langfuse | -- |

---

## Failure analysis

### Cluster A — Missing MSW fixtures (Level 1)

5 specs reference fixture names that do not exist in `frontend/src/__tests__/msw/fixtures/index.ts`. The handler returns HTTP 500 (`{"error":"unknown fixture: <name>"}`), which flips `message-list` to `data-status="error"`. Affected scenarios: `J-chan-01`, `S-chan-01`, `S-chan-02`, `S-chan-03`, `S-rsn-04`, `S-rsn-13`, `J-rsn-02`.

| Spec | Requested fixture | Closest existing |
|---|---|---|
| `reasoning-channel-isolation.spec.ts` (×3) | `reasoning-then-text` | none — needs new fixture |
| `reasoning-indicator-states.spec.ts:59` (S-rsn-04) | `tool-call-then-text` | likely typo for `happy-tool-then-text` |
| `journeys/abort-then-resend.spec.ts` (J-rsn-02 / S-rsn-13) | `long-reasoning-then-text` | none — needs new fixture |

- **Expected:** spec navigates to a fixture that streams `data-reasoning-status` (and for `tool-call`, a tool block) so the assertions can run.
- **Actual:** MSW handler 500 because the fixture is unknown.
- **Suspected root cause:** lifecycle specs were authored against a planned fixture set that was never added to `frontend/src/__tests__/msw/fixtures/`. The fixtures index lists 21 fixtures, none of which emit `data-reasoning-status`. None of the existing fixtures cover the reasoning channel at all.
- **Likely files to edit:** `frontend/src/__tests__/msw/fixtures/index.ts` + new fixture files (`reasoning-then-text.ts`, `long-reasoning-then-text.ts`, optional rename `happy-tool-then-text` → `tool-call-then-text` or fix the spec). Each must emit `{type:"data-reasoning-status", transient: true, status:"…"}` SSE frames in addition to text/tool blocks.
- **Level 1.**

### Cluster B — Specs use happy-text but expect reasoning UI (Level 1)

3 specs call `chat.gotoFixture("happy-text")` then assert `reasoning-indicator` becomes visible. The `happy-text` fixture is text-only — there is no `data-reasoning-status` event in its 6 chunks, so `useReasoningStatus` never receives a payload and `ReasoningIndicator` never renders.

Affected scenarios: `S-rsn-01`, `S-rsn-02`, `S-rsn-06`, `S-trace-05`.

This matches the tension already flagged in `executable-verification.md`: the SETUP comment claims real backend with dev flags (`EMIT_DELAYED_REASONING=1` etc.), but the body activates MSW with `happy-text`. The dev flag never runs; the MSW happy-text stream contains nothing reasoning-related.

- **Expected:** indicator surfaces (and for S-rsn-06, gains `.stalled` after 11 s).
- **Actual:** indicator never mounts at all because no reasoning event is delivered.
- **Suspected root cause:** spec authors meant to point at a reasoning-emitting MSW fixture (or to wire backend with the dev flag in test setup). Neither happened.
- **Likely files to edit:** add reasoning-emitting MSW fixtures (overlaps with Cluster A) and update each spec's `gotoFixture()` argument; OR introduce a Playwright `webServer` config that boots the backend with the appropriate dev flag and rewrite the spec to drive the real `/api/v1/chat`.
- **Level 1** for "the test as written cannot pass against the current implementation"; the implementation itself (indicator mount, stalled-class apply, finalize hold-and-flush) appears correct based on backend unit tests.

### Cluster C — `stop-preserves-partial` timing regression (Level 1)

`tests/e2e/critical/stop-preserves-partial.spec.ts` waits for the assistant message to contain `Paragraph 0.`, then clicks `composer-stop-btn`. The `long-text-stream` fixture has 50 chunks × 50 ms = ~2.5 s total (plus assertion wait), and the `Paragraph 0.` text appears in the first delta — by the time the assertion resolves and the click is dispatched the stream has already finished and the stop button is unmounted.

- **Expected:** stop button is clickable mid-stream.
- **Actual:** the test reaches `composer-stop-btn` after the stream finishes; locator never resolves; test times out at 30 s.
- **Suspected root cause:** fixture chunk count or per-chunk delay is too small; or the spec needs to click stop earlier (e.g. as soon as the assistant message is visible, not after `Paragraph 0.`).
- **Likely files to edit:** `frontend/src/__tests__/msw/fixtures/long-text-stream.ts` (raise chunks to 200 or per-chunk delay to ~200 ms); or change the spec to click stop right after first text-delta.
- **Level 1.** This is the only critical-tag failure not connected to the reasoning fixture gap.

### No Level 2 / Level 3 failures detected

Every failure traces back to test-fixture / test-setup defects, not to behavioural bugs in the implementation. Backend unit tests for the same scenarios (S-rsn-06 / S-rsn-12 / S-trace-05 / S-trace-09 / S-chan-01 / S-chan-03 / S-chan-04 / S-trace-06) are all green.

---

## Tension flags

1. **Lifecycle specs SETUP comment vs. MSW gotoFixture mismatch.** Already noted in `executable-verification.md`. Round-1 confirms the tension is destructive: 4 specs (S-rsn-01/02, S-rsn-06, S-trace-05) and 3 spec methods in `reasoning-channel-isolation.spec.ts` (J-chan-01/S-chan-02, S-chan-01, S-chan-03) cannot pass against MSW because the chosen fixtures emit no reasoning events. Decision needed:
   - **Option A:** add reasoning-emitting MSW fixtures (`reasoning-then-text`, `long-reasoning-then-text`, `tool-call-then-text` or rename to existing `happy-tool-then-text`, plus a stalled / late / reasoning-only variant) and update spec arguments. Cheapest. MSW-only coverage is acceptable per project memory `feedback_msw_vs_real_backend.md`.
   - **Option B:** wire Playwright `webServer` to boot the backend with the correct dev flags per spec. Heavier — requires test orchestration to spawn N uvicorn instances, or a single shared backend that switches behaviour by query param.

   Recommendation: **Option A** — the dev flags already work at the backend (unit tests prove this); duplicating their effect via MSW chunks is straightforward. This also aligns with how the existing 5 reasoning specs that DO pass (`S-rsn-03`, `S-rsn-08`, `S-rsn-12`, `S-trace-09`) are MSW-driven.

2. **`tool-call-then-text` likely typo.** `S-rsn-04` references this name; the existing fixture is `happy-tool-then-text`. Either rename the existing fixture or update the spec — note `happy-tool-then-text` already streams tool blocks, so it could plausibly satisfy S-rsn-04 once the name matches.

3. **`long-text-stream` fixture is too short for `stop-preserves-partial`.** Needs more chunks or longer per-chunk delay. Independent of reasoning rework.

4. **Missing scenario coverage.** Even after the fixture gap is fixed, the following scenarios have no automated test today and were not flagged BLOCKED-LIVE-API:
   - `S-rsn-05` (Anthropic Option B re-entry)
   - `S-rsn-07` (post-tool idle text "Synthesizing"/"Thinking")
   - `S-rsn-09` (stream-error sub-states 3-row table)
   - `S-rsn-11` (clearedRef guard against 200 ms drain race)
   - `S-rsn-14` (LiveStatusAnnouncer ARIA hybrid)
   - `J-rsn-01` (10-state lifecycle journey)

   These should be classified by the user as either "new tests needed" or "deferred to later PR". For Round 1 they appear in the table as `NOT-COVERED` / `NOT-IMPLEMENTED`.

5. **Vendored MSW worker eslint warning.** `public/mockServiceWorker.js` is generated by `msw init`; the warning is benign. Either update the eslint config to ignore the file or run `pnpm exec msw init public/ --save` to refresh it. Not blocking.
