# DEV-109 BDD Verification — Round 1 — Browser-Use CLI Tier (12 scenarios)

Ran in two passes: an initial dispatch that raced with the Playwright tier on shared backend config
(stopped early once discovered), then a clean serial re-run. Config was restored to default
(openai:gpt-5-mini, reasoning on) after every provider-switch, confirmed via `git diff` clean +
health check.

### S-chip-01: reasoning chip appears and grows with streaming plain text — PASS
Expanding block appeared shortly after submit, grew line-by-line, plain preformatted text (no
markdown), collapsed to "Thought for 7s" after ~7s.

### S-chip-05: chips/tool cards interleaved order — PASS
1 collapsed reasoning block + 4 tool-call cards observed in top-to-bottom order matching the
part-arrival-order rule.

### S-chip-07 (Gemini reasoning-off): zero reasoning blocks — **INCONCLUSIVE**
v1 attempt: agent didn't finish (`is_done: False`). Retry: browser-use's own Chrome instance failed
to load `localhost:5173` at all after 44s (empty DOM) — an infra/tooling flake, not an app signal
either way. Genuinely unverified this round; needs a clean re-run.

### S-place-01: placeholder appears on submit, persists until first content — PASS
"Thinking…" visible within 1-2s of submit, before any reasoning/answer content.

### S-place-03: no placeholder during tool execution — **mixed/needs a closer look**
Agent report: observed "Thinking…" indicator visible AT THE SAME TIME as completed tool cards on
screen. The scenario expects placeholder to be ABSENT while tool cards are actively executing — the
agent's phrasing ("completed tool cards remain visible while chat bubble displays 'Thinking...'")
is ambiguous about whether this was during active tool execution or in the gap after tools finished
but before the next segment (which per S-place-02 IS a legitimate placeholder window). Not confident
enough to call PASS or FAIL — recording as ambiguous evidence, not a clean pass.

### S-pres-01: tool card lifecycle (in-progress → result) — PASS
Cards show in-progress state then completed/result state with visual distinction.

### S-pres-02: Stop settles cleanly, resend works — PASS
No stuck spinners after Stop; resent message completed normally end-to-end.

### S-pres-03: `FORCE_LLM_FAIL` legible error, input stays usable — PASS
"Something went wrong. Please try again." with Retry option shown; successfully typed and sent a
second message afterward, confirming input remained functional.

### S-pres-04: regenerate replays full flow — PASS (from v1; retry attempt was agent-side flakiness)
v1 (first pass, clean config): full replay confirmed — placeholder → reasoning chip (Thought for
25s) → 4 tool cards → answer streaming, matching first-generation sequence. v2 retry this round
failed to locate the regenerate control (hover-reveal UI likely tripped up the agent) — treating v1
as the trustworthy result since it's a complete, positive observation, not discarding it for a
weaker null result.

### S-pres-05: answer text streams incrementally — PASS
Direct observation mid-generation showed answer text ending mid-sentence (open parenthesis),
confirming incremental streaming rather than a single paste.

### J-01 (Gemini reasoning-on): full mainline journey — PASS
All 7 steps observed in order: placeholder → first reasoning chip streaming → collapse (`Thought for
1s`) → tool cards → second reasoning chip (`Thought for 27s`) → answer streaming → completion. Both
chips expanded successfully with non-empty readable content.

### J-02 (GPT reasoning-on, default config): full mainline journey — PASS
All 6 checked items confirmed, same behavioral sequence as J-01 — provider-agnostic abstraction
holds.

## Summary

| Total | Passed | Failed | Inconclusive/Ambiguous |
|---|---|---|---|
| 12 | 9 | 0 | 3 (S-chip-07, S-place-03, and S-pres-04's retry noise absorbed by v1) |

Effectively: **9 clean PASS**, **1 needs re-run** (S-chip-07 — tooling flake, not app evidence
either way), **1 ambiguous evidence needing a tighter re-check** (S-place-03).

Backend restored to default config (openai:gpt-5-mini, reasoning on), running on :8000, confirmed
via clean `git diff` on the config file and a 200 health check.
