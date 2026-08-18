# Tool-call arrival closes the reasoning part; terminal-tool dead air gets a third placeholder window

Status: accepted (2026-08-04) — DEV-109 rulings 9/10, supersedes ADR-0015's "same-round `tool_call_chunk` does not close the reasoning part" consequence and its two-window placeholder model.

Two ADR-0015 decisions did not survive manual BDD verification against real providers:

1. **Chip close timing.** ADR-0015 (via the ratified S-chip-05 overlap allowance) assumed a same-round tool-call chunk should leave the reasoning chip open, on the theory that a provider may emit tool-call args before `reasoning-end` and the chip should stay open so the tool card renders below it. In practice, on the project's default provider this overlap happens on *every* round, not rarely — the chip stayed open through the entire tool execution, which manual testing surfaced as a visible bug (tool card rendered, chip still expanded). `StreamEventMapper` now closes the open reasoning part the moment ANY tool-call representation arrives — both `content_blocks` shapes the pinned langchain-core translator produces (`tool_call_chunk`: OpenAI/Anthropic normalized; `tool_call`: Gemini normalized). Arrival order on the wire is unchanged, so the tool card still renders below the now-collapsed chip.

2. **Placeholder window count.** ADR-0015 named two dead-air windows (submit → first content; chip collapse → reply text). Manual testing surfaced a third: when every tool part in the round has reached a terminal state (`output-available` / `output-error`) and nothing renderable has arrived yet, there was no placeholder covering the wait for the next LLM call — a visible gap with no "thinking" affordance. `useDeadAirPlaceholder` gained window C for this case, anchored on the same grace-delay mechanism as window B.

**Why.** Both fixes come from the same root cause: ADR-0015's placeholder/chip model was designed against an idealized single-provider timing assumption that real multi-provider streaming didn't match. Rather than patch each symptom locally, the mapper normalizes to one dispatch pass over `content_blocks` (no cross-provider special-casing) and the placeholder hook anchors on the last *renderable* part (not the raw last part), so both fixes generalize instead of hard-coding a specific provider's timing.

## Considered options

1. **Provider-specific timing patches** (e.g. only close the chip early for Gemini) — rejected: reintroduces the per-provider branching ADR-0015 was already trying to avoid, and the overlap-every-round behavior was observed on the default provider too.
2. **Close on tool-call arrival for every representation; add window C** — chosen.

## Consequences

- ADR-0015's "Consequences" bullet describing the activity indicator's two dead-air windows is superseded by this ADR's three-window model (`backend/agent_engine/streaming/README.md` and `frontend/src/hooks/README.md` carry the current, mutable description — this ADR records the decision, not the maintained spec).
- `S-chip-05`'s original "overlap is rare, keep chip open" allowance is retired; the mapper's overlap-handling test coverage lives in `backend/tests/streaming/test_event_mapper.py::TestReasoningPartBoundaries`.
- The chip-collapse → reply-text gap (window B) is near-zero on the wire by construction, since the mapper closes the reasoning part at the same moment the next text block is dispatched — this is why window B's grace delay never actually fires in that direction. The chip-collapse → tool-card gap is a separate, unconditional invariant (ruling 10 / S-place-02): the placeholder must never appear there regardless of timing, not because the gap happens to be near-zero.
