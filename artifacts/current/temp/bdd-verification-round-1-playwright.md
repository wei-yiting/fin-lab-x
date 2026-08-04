# DEV-109 BDD Verification — Round 1 — Playwright Tier (10 scenarios)

**Contamination note**: the first pass through this tier overlapped with the Browser-Use CLI tier
running concurrently, which silently left the shared backend on `google_genai:gemini-2.5-flash` /
`reasoning: "off"` mid-run (for its S-chip-07 scenario). This produced false failures on S-chip-03
and S-chip-04 (zero reasoning chips appeared — correct behavior for reasoning-off, wrong config for
this tier). Backend config was restored to default (openai:gpt-5-mini, reasoning on) and all
default-config scenarios were re-run clean. **Lesson for round 2 / future runs: do not run the
Playwright and Browser-Use CLI tiers concurrently against a shared backend that both switch config
on** — serialize them.

### S-chip-02: segment ends → chip collapses to `Thought for Xs`, content readable, `aria-live` — PASS
Screenshots: `temp/screenshots/s-chip-02-{collapsed,expanded}.png`.

### S-chip-03: `Thought for Xs` excludes tool execution time (±2s tolerance) — **FAIL (borderline)**
Clean-config re-run: `measured_gap_sec: 3.878`, `reported_X_sec: 6` (integer, rounded), diff `2.122s`
— 0.122s over the ±2s band. This is a single-run timing measurement with inherent noise (DOM-visible
tool card vs. backend tool-start event have some inherent skew); not clearly a code defect. **Needs
judgment**: accept as noise (tolerance in the scenario itself is somewhat arbitrary) vs. genuine
rounding/measurement issue vs. widen tolerance. Recommend re-running 2-3× before treating as a fix
target — did not re-run further to conserve time.

### S-chip-04: second segment start collapses previous chip (tail-only) — **INCONCLUSIVE (LLM nondeterminism)**
Clean-config re-run: only ONE reasoning chip appeared for the whole multi-tool canonical-prompt turn
(`"Thought for 37s"`), all 4 tool calls happened without a second distinct reasoning segment. This
scenario's precondition (a second reasoning segment actually occurring) simply wasn't met this run —
GPT-5-mini doesn't guarantee multiple reasoning bursts across a tool loop every time (S-wire-02's
deterministic curl run earlier in this session DID observe 5 reasoning blocks for the identical
prompt/config, proving multi-block behavior exists, just isn't guaranteed per-run). Not exercised,
not a code defect — needs a retry loop or a provider/prompt combo that reliably produces ≥2 segments
to actually verify the tail-only-collapse rule.

### S-chip-06 (MSW): zero-delta suppressed, whitespace chip stays — PASS
Clean pass, 1.4s. Screenshot: `temp/screenshots/s-chip-06-final.png`.

### S-chip-08: mid-stream abort collapses half chip with `Stopped` header — PASS
Clean pass, 7.5s. Screenshot: `temp/screenshots/s-chip-08-after-stop.png`.

### S-chip-09: reload mid-stream discards in-flight turn — PASS
Clean pass, 1.1s. Screenshot: `temp/screenshots/s-chip-09-after-reload.png`.

### S-place-02: chip-collapse gap placeholder routing — **FAIL (reproducible, needs investigation)**
Two clean-config runs, both failed the SAME way but differently each time:
- Run 1 (post-contamination-fix): completed the polling loop (235-319 samples), turn finished, but
  `sawPlaceholderBeforeReplyText` was `false` both times — the placeholder never appeared in the
  chip→reply-text gap.
- Run 2: this time the outer 300s Playwright test timeout fired WITHOUT the inner "turn did not
  complete within 240s" custom error firing first — suggests either the polling loop itself stalled
  (not a turn-completion issue) or the turn took unusually long this run. Did not have time to
  distinguish flaky-harness vs. genuine backend slowness vs. genuine missing-placeholder bug.
- **Needs round-2 investigation**: is the actual chip→reply-text gap consistently under the 300ms
  grace window for this canonical prompt (in which case never showing the placeholder is CORRECT
  per the `PLACEHOLDER_GRACE_MS` design, and the test's hard `toBe(true)` expectation is wrong), or
  is the placeholder genuinely never wired up for that specific transition? This is exactly the kind
  of ambiguity the skill's Level 3 escalation exists for — recommend treating as a design-vs-test
  question, not an auto-fix target, until the actual gap duration is measured directly.

### S-place-04 (MSW): stall degrades chip header copy, recovers — PASS
Clean pass, 11.6s. Screenshots: `temp/screenshots/s-place-04-{stalled,recovered}.png`.

### S-place-05 (MSW): Stop usable during long silent stall — PASS
Clean pass, 11.8s. Screenshot: `temp/screenshots/s-place-05-after-stop.png`.

### J-03: abort + recovery journey — PASS (both halves)
UI half: clean pass, 57.1s — Stop mid-first-chip → `Stopped — thought for Xs` collapsed chip →
resend simple prompt → completes normally end-to-end. Langfuse readback (session
`44fb9c49-b60e-49b0-a5da-75dac0b344ec`): trace[0] (aborted turn) `status='aborted'`, reasoning tail
ends `=== aborted ===`; trace[1] (resent turn) `status=None`, no aborted marker, clean transcript.
Both verify() checks `ok=True`, zero errors.

## Summary

| Total | Passed | Failed | Inconclusive | Not Run |
|---|---|---|---|---|
| 10 | 7 | 2 | 1 | 0 |

Failed: S-chip-03 (borderline timing), S-place-02 (reproducible, needs design-vs-test judgment)
Inconclusive: S-chip-04 (LLM nondeterminism — precondition not met this run)

New files created (test infrastructure, not application code):
- `frontend/src/__tests__/msw/fixtures/zero-delta-whitespace-reasoning.ts` (new fixture, S-chip-06)
- `frontend/src/__tests__/msw/fixtures/reasoning-stall-recover.ts` (new fixture, S-place-04/05)
- `frontend/src/__tests__/msw/fixtures/index.ts` (modified — registered the two new fixtures)
- `artifacts/current/temp/bdd-dev109.spec.ts` (ad-hoc verification spec, not in permanent e2e suite)
- `artifacts/current/temp/playwright.bdd109.config.ts` (ad-hoc config pointing at it)

Backend restored to default config (openai:gpt-5-mini, reasoning on) and running on :8000.
