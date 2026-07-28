---
# Code Review Round 1

> Reviewer: gpt-5.5 | Date: 2026-07-28

## Summary

| Metric | Count |
|--------|-------|
| Total issues | 5 |
| Blocking | 0 |
| Major | 1 |
| Minor | 4 |
| Suggestion | 0 |
| Library checks | 4 |

## Issues

### [Major] M-1.1: New-turn reset corrupts existing reasoning chip durations
- **File:** `frontend/src/components/pages/ChatPanel.tsx` L124
- **Problem:** `resetForNewTurn()` clears the entire chip timing map on every send/regenerate/retry. Existing transcript chips still render, so `useReasoningTimers.observe()` re-creates their timings from the current wall clock and can turn prior `Thought for 3s` / `Stopped — thought for 4s` labels into `0s` or live-changing values during the next turn. This breaks the transcript's displayed history; the current integration test only checks `/\d+s/`, so it misses the regression.
- **Fix:** Do not clear the whole timing map on ordinary new sends. Keep timings keyed by `message.id:partIndex`, and only prune timings for assistant messages actually removed by regenerate/retry. Add a test that a completed chip and an aborted chip keep the same seconds label after a subsequent send.
- **Context7:** N/A. This is local state lifetime, not AI SDK API misuse.

### [Minor] m-1.1: Top-level verifier docstring contradicts the implemented reasoning-on contract
- **File:** `backend/scripts/validation/verify_langfuse_trace.py` L9
- **Problem:** The docstring says every GENERATION must have `--expect-reasoning-on` as a non-empty string, but `_check_reasoning_on()` deliberately allows empty reasoning on some generations as long as at least one generation has text.
- **Fix:** Update the docstring bullets to match the implemented per-trace contract.

### [Minor] m-1.2: Validation README still documents removed `reasoning_tail_aborted` abort contract
- **File:** `backend/scripts/validation/README.md` L59
- **Problem:** The README says `--expect-aborted` requires root `metadata.status == "aborted"` and latest GENERATION `metadata.reasoning_tail_aborted`. The script now checks only the root status marker.
- **Fix:** Rewrite the `--expect-aborted` row and assertion list to root-status-only, matching `verify_langfuse_trace.py`.

### [Minor] m-1.3: Agents README still says abort cleanup drains the deleted segmenter
- **File:** `backend/agent_engine/agents/README.md` L5
- **Problem:** The map entry says `_handle_abort_cleanup()` "drains the segmenter tail", but `reasoning_segmenter.py` was deleted and abort cleanup no longer drains reasoning tail.
- **Fix:** Update the map entry to say abort cleanup stamps root Langfuse `metadata.status="aborted"` only.

### [Minor] m-1.4: Dead `_latest_generation()` helper survived the abort-contract deletion
- **File:** `backend/scripts/validation/verify_langfuse_trace.py` L160
- **Problem:** `_latest_generation()` is no longer referenced after removing the per-generation abort-tail assertion. Leaving dead helper code makes the old contract look partially alive.
- **Fix:** Delete `_latest_generation()`.

## Documentation Gaps

| Folder | Missing |
|--------|---------|
| `backend/scripts/validation/` | README still describes the removed abort-tail contract. |
| `backend/agent_engine/agents/` | README map still mentions segmenter-tail draining. |
| `backend/tests/scripts/` | README still says `reasoning_tail_aborted` is required, which contradicts current tests and script behavior. |

## Official Standards Check

| Library | Version | API Used | Status | Notes |
|---------|---------|----------|--------|-------|
| Vercel AI SDK `ai` | `^6.0.142` | `reasoning-start` / `reasoning-delta` / `reasoning-end` | ✅ Current | Backend emits ordered start/delta/end sequences and closes reasoning before error/finish on non-abort paths. |
| Vercel AI SDK `ai` | `^6.0.142` | Reasoning/text part IDs | ✅ Current | Backend uses turn-unique `reasoning-{n}` / `text-{n}` counters, so it does not rely on SDK per-step ID uniqueness. |
| `@ai-sdk/react` | `^3.0.144` | `useChat.status` | ✅ Current | Code uses the 4 documented statuses and `useDeadAirPlaceholder()` does not treat `status === "streaming"` alone as proof that content has arrived. |
| Vercel AI SDK `ai` | `^6.0.142` | `ReasoningUIPart.state` | ✅ Current | Code derives local `ChipState="aborted"` from `state === "streaming"` after chat leaves active status; it does not expect the SDK to send a native `aborted` state. |

---

# Spec Conformance Round 1

> Reviewer: claude-sonnet-5 | Date: 2026-07-28

## Summary

| Metric | Count |
|--------|-------|
| Total findings | 4 |
| Missing | 1 |
| Scope creep | 1 |
| Misimplemented | 2 |

## Findings

### [Major] SP-1.1: Reload during in-flight stream drops the user's own prompt, not just the assistant turn
- **Type:** Missing
- **Spec:** "串流中 reload → **丟掉進行中的 assistant turn**（無部分文字/chips/error 面；user prompt 留著）" (2026-07-26 comment §B, decision 9; also `bdd-scenarios.md` S-chip-10: "her own user prompt stays")
- **File:** `frontend/src/components/pages/ChatPanel.tsx` (whole file — no hydration path exists)
- **Problem:** The decision's specific promise is that on reload mid-turn, the assistant's partial turn disappears **but the preceding user prompt message remains visible**. Confirmed via grep across `frontend/src` that there is no `localStorage`/`sessionStorage`/`initialMessages`/history-fetch/hydration code anywhere in the app — `chatId` is freshly generated (`crypto.randomUUID()`) on every mount and `useChat` starts with empty `messages`. A real browser reload therefore wipes the **entire** conversation, including the user's own prompt and any previously completed assistant turns — not just the in-flight turn. `bdd-scenarios.md`'s S-chip-09/S-chip-10 scenarios assume "frontend 從 backend 重新 hydrate messages," which does not happen anywhere in the shipped code, and neither scenario has any automated test. The 2026-07-28 12:10 comment calls this a "vacuous pass" for the chips-only sub-claim, but the broader, explicitly-worded "user prompt stays" promise is not vacuously true — it is actually false on a real reload.
- **Fix:** Either (a) scope decision 9 down in the issue/BDD artifacts to "no history hydration exists yet; reload clears the whole session, tracked as a known gap for the ticket that adds hydration," or (b) if user-prompt persistence was intended to ship in this slice, add minimal session/message persistence so the completed prefix (including the last user message) survives a reload. As shipped, the decision as literally written is not satisfied.
- **User disposition (2026-07-28):** Accepted as expected — history hydration was never built in this slice; this is a known, out-of-scope gap, not a bug to fix here. No action.

### [Major] SP-1.2: Placeholder's first dead-air window silently extended beyond the ratified `status === 'submitted'` keying
- **Type:** Misimplemented
- **Spec:** "The placeholder's first dead-air window keys on `status === 'submitted'` (explicitly NOT 'streaming AND parts empty')." (2026-07-26 comment §C, implementation-binding contract)
- **File:** `frontend/src/hooks/useDeadAirPlaceholder.ts` L40-43
- **Problem:** Commit `5ddb0f6` changed `windowA` from `status === "submitted"` to `status === "submitted" || (status === "streaming" && !turnHasRenderableContent(last))` — exactly the "streaming AND (effectively) empty parts" pattern the binding contract explicitly rejected. The commit and the 2026-07-28 13:50 Linear comment both justify this as a real bug fix (measured up to ~8s of blank screen between the wire's `start` frame and the first renderable reasoning delta / a zero-delta reasoning block that never renders anything), and both explicitly flag it as contradicting the C-line and `bdd-scenarios.md` L451's design note, deferring formal reconciliation to DEV-108. The underlying bug is real (reasoning deltas can legitimately lag `reasoning-start` by seconds, and a fully-suppressed zero-delta block never paints), so the *direction* of the fix is defensible — the original C-line ratification appears to have been made without accounting for this timing gap. However: (1) it was shipped as a unilateral post-hoc override of a binding decision rather than through re-ratification, (2) the spec-of-record (`bdd-scenarios.md`) still states the old, now-false rule with no superseded marker, and (3) `hooks/README.md` (kept in sync) documents the new behavior while the Linear issue/BDD artifact do not — so two review surfaces now disagree about a decision that was supposedly locked. This is a real spec/artifact drift even though the code-level engineering judgment looks sound.
- **Fix:** Land a DEV-108 (or equivalent) update to `bdd-scenarios.md`'s design note and the DEV-106/DEV-105 decision table amending the C1 text to the corrected window-(a) definition, so the binding artifact matches shipped behavior instead of silently diverging from it.

### [Minor] SP-1.3: Unratified `PLACEHOLDER_GRACE_MS` timer adds a fourth non-derived store not accounted for in the spec's state inventory
- **Type:** Scope creep
- **Spec:** "there are actually ≥3 non-derived stores: the chip timing ref, the global 10s stall stopwatch, and a user expand/collapse override `Map<partId,bool>`" (2026-07-26 comment §A) — no ratified decision anywhere mentions a placeholder grace/debounce delay.
- **File:** `frontend/src/lib/timing.ts` L21 (`PLACEHOLDER_GRACE_MS = 300`); `frontend/src/hooks/useDeadAirPlaceholder.ts` L37, L53-57 (`elapsedGapKey` state + `setTimeout`)
- **Problem:** To distinguish "chip collapsed → tool card next" (no placeholder) from "chip collapsed → reply text next" (placeholder wanted) — a real ambiguity, since the wire gives no lookahead — the implementation adds a 300ms debounce with its own `useState`/`setTimeout`, a state store beyond the three the spec explicitly enumerated. The 2026-07-28 12:10 comment self-discloses this as "an unratified mechanism," and `hooks/README.md` L14 still describes the budget as "Exactly three non-derived stores are allowed" — internally inconsistent with the code's actual fourth store. This is defensible plumbing in service of an explicit requirement ("tool 執行中不出現" / decision 5), not a new capability, so not blocking, but the mechanism was never run past Three Amigos / human ratification the way the other three stores were.
- **Fix:** Either fold this into a follow-up ratification (update `bdd-scenarios.md` decision list to acknowledge a 4th store), or correct `hooks/README.md`'s "Exactly three" line to "at least three" / enumerate the fourth explicitly so the doc stops contradicting the code it describes.

### [Major] SP-1.4: `hooks/README.md` non-derived-state count drifts from the actual implementation
- **Type:** Misimplemented
- **Spec:** "動到的模組 README（streaming、hooks、agents、atoms/pages）與新 code 同步，無 drift" (DEV-106 description, acceptance criterion 5)
- **File:** `frontend/src/hooks/README.md` ("Non-derived state budget" section, "Exactly three non-derived stores are allowed")
- **Problem:** Same root cause as SP-1.3 from the documentation-conformance angle: this README makes an "exactly three" closed-world claim about non-derived state, but `useDeadAirPlaceholder.ts` maintains a fourth (`elapsedGapKey` + its timeout ref) that the same README's own `useDeadAirPlaceholder.ts` row describes two paragraphs earlier ("held behind `PLACEHOLDER_GRACE_MS`"). The document contradicts itself, which is exactly the kind of README/code drift this AC exists to prevent.
- **Fix:** Reword the "Non-derived state budget" section to either say "at least three" (matching the spec's own "≥3" phrasing) or explicitly list the placeholder grace timer as a fourth, acknowledged store.

## Covered Requirements

- ✅ Three domain events `ReasoningStart`/`ReasoningDelta`/`ReasoningEnd`, verbatim delta passthrough — `backend/agent_engine/streaming/domain_events_schema.py` L58-71, `event_mapper.py` L156-172
- ✅ Wire serialization to AI SDK v6 `reasoning-start`/`reasoning-delta`/`reasoning-end` — `backend/agent_engine/streaming/sse_serializer.py` L110-124
- ✅ One provider reasoning block = one part; D12 `\n`-join logic removed — `backend/agent_engine/streaming/event_mapper.py` L156-172; `test_event_mapper_reasoning_integration.py`
- ✅ Reasoning part `id` turn-unique (not step-local) — `event_mapper.py` L48-64 (`_reasoning_id_counter` never reset across LLM-call boundaries); `test_event_mapper.py::test_new_llm_call_closes_part_and_opens_new_id` (S-parts-01)
- ✅ `ReasoningSegmenter`, D28 hold-and-flush, D39 guard, transient reasoning channel, 5 reasoning dev flags removed; `FORCE_LLM_FAIL` kept — confirmed via diff stat + repo-wide grep — `backend/agent_engine/agents/base.py` L480-487
- ✅ Abort stays wire-silent; abort-cleanup tail write removed (moved to DEV-107) — `backend/agent_engine/agents/base.py` `_handle_abort_cleanup` L523-571
- ✅ Error path emits `reasoning-end` before `error`+`finish` — `backend/agent_engine/agents/base.py` L516-521
- ✅ Frontend pure derivation from `(status, messages)`; old onData reasoning branch / dual guard refs / `useLayoutEffect` auto-hide / onFinish-onError latch deleted — `frontend/src/components/pages/ChatPanel.tsx`, diff stat confirms deletions
- ✅ `useChat.status` treated as exactly 4 values — used consistently across `useDeadAirPlaceholder.ts`, `useStallTimer.ts`, `ChatPanel.tsx`
- ✅ `ReasoningChip`: streaming full-text pinned-bottom auto-scroll, collapsed `Thought for Xs` — `frontend/src/components/molecules/ReasoningChip.tsx` L42-46, L87-95
- ✅ Only tail chip expanded; prior chips collapse on next part arrival — `frontend/src/lib/reasoning-chips.ts` L70-85, `AssistantMessage.tsx` L113-114
- ✅ Aborted half-chip: `Stopped — thought for Xs` — `frontend/src/lib/reasoning-chips.ts` L70-95
- ✅ ≥3 non-derived stores — `useReasoningTimers.ts`, `useStallTimer.ts`, `ChatPanel.tsx` L98 (see SP-1.3/SP-1.4 for undisclosed 4th store)
- ✅ `ActivityIndicator` reduced to 3-state placeholder, never shown during tool execution or chip streaming — `useDeadAirPlaceholder.ts`, `ActivityPlaceholder.tsx`
- ✅ Global single 10s stall stopwatch, reset by any stream part — `useStallTimer.ts`, `timing.ts` L10
- ✅ Exactly one ChatPanel integration test case for stall wiring — `ChatPanel.integration.test.tsx` L737
- ✅ Copy strings `Thinking…` / `Still working…` / `Thought for Xs` — `reasoning-chips.ts` L87-95, `ActivityPlaceholder.tsx`
- ✅ `AssistantMessage` reasoning filter → chip renderer, parts interleaved in arrival order — `AssistantMessage.tsx` L107-144
- ✅ Chip/tool-card overlap: tool card placed below still-open chip — `AssistantMessage.tsx`
- ✅ Empty reasoning block: only zero-delta suppressed; whitespace-only chips stay — `reasoning-chips.ts` L53-61
- ✅ Timing freeze at first tool-start / abort samples at Stop; wall-clock delta — `useReasoningTimers.ts`
- ✅ Streaming chip body uses `white-space: pre-wrap` — `ReasoningChip.tsx` L82-84
- ✅ Minimal `aria-live="polite"` on placeholder + chip header — `ActivityPlaceholder.tsx` L16, `ReasoningChip.tsx` L62
- ✅ Chips do not survive reload (v1) — no reasoning-part replay path exists
- ✅ Old 19-state file group, frozen `STOPPED` indicator, `abortedMessages` deleted outright — confirmed via diff stat + grep
- ✅ Test-folder READMEs deleted per design-envelope §6 named precedent — `backend/tests/agents/README.md`, `backend/tests/streaming/README.md` removed
- ✅ Backend + frontend full test suites, `tsc -b`, `ruff check`, `prettier --check` green — verified directly (ruff clean, tsc clean, 195/195 frontend, 234 backend streaming/agents/scripts tests, prettier clean)
- ✅ Streaming module README updated in sync with F5 — `backend/agent_engine/streaming/README.md`

---

# Spec Conformance Round 1 (Codex rerun — per explicit user request to use Codex for this axis too)

> Reviewer: gpt-5.5 | Date: 2026-07-28
>
> Note: this is a second, independent Spec Conformance pass over the same diff, requested by
> the user after the Claude-authored pass above. Per Rule 8 (preserve all records) the original
> Claude pass is kept above rather than overwritten. The orchestrator spot-checked the two
> Blocking findings below directly against the code before relaying results — see annotations.

## Summary

| Metric | Count |
|--------|-------|
| Total findings | 5 |
| Missing | 1 |
| Scope creep | 1 |
| Misimplemented | 3 |

## Findings

### [Blocking] SP-1.1: Zero-delta reasoning still emits native reasoning wire parts
- **Type:** Misimplemented
- **Spec:** "reasoning-off / 空 reasoning → 0 parts" (`artifacts/current/verification-plan.md`, S-parts-05)
- **File:** `backend/agent_engine/streaming/event_mapper.py` L164
- **Problem:** `_handle_reasoning_block()` opens a `ReasoningStart` before knowing whether the block has any delta. For `reasoning=""`, the backend emits `reasoning-start` and later `reasoning-end`; the frontend suppresses the chip, but the wire still violates the zero-parts requirement.
- **Fix:** Defer opening the reasoning part until the first non-empty delta. Preserve whitespace-only deltas as real deltas/chips, but emit nothing for truly zero-delta blocks.
- **Orchestrator annotation — VERIFIED, false positive.** Ran `uv run pytest tests/streaming/test_event_mapper.py -k test_empty_delta_not_emitted -v`: passes. That test (line 351) asserts exactly this behavior (`ReasoningStart` emitted, no `ReasoningDelta`, for a zero-length reasoning block) and its own docstring cites it as intentional: `"A zero-length reasoning block opens the part but emits no delta — the frontend suppresses zero-delta chips (S-chip-08)."` S-parts-05 (`verification-plan.md`) is a different scenario — reasoning disabled at the config level (or a prompt short enough the LLM never attempts reasoning at all), where the `reasoning`-type content block never appears in the stream in the first place, so `_handle_reasoning_block` never runs. This finding conflates two distinct spec lines. Not accepted — no fix needed.

### [Blocking] SP-1.2: Tool-call chunks force-close reasoning before the spec's overlap case
- **Type:** Misimplemented
- **Spec:** "Chip/tool-card time overlap (e.g. Gemini sends tool args before `reasoning-end`): the tool card is placed **below the still-open chip**, preserving arrival order — do not force early collapse." (2026-07-26 comment §B; `bdd-scenarios.md` S-chip-06)
- **File:** `backend/agent_engine/streaming/event_mapper.py` L195
- **Problem:** `_handle_tool_call_chunk_block()` immediately calls `_close_reasoning_part()`. That forces `reasoning-end` before the tool path can render below an open chip, directly contradicting the overlap ruling. The unit test at `backend/tests/streaming/test_event_mapper.py` L386 (`test_tool_call_chunk_closes_open_reasoning_part`) also locks in the wrong behavior as the expected one.
- **Fix:** Do not close an open reasoning part merely because a tool-call chunk arrived. Preserve arrival order by letting the tool part appear while the reasoning part remains open, and close reasoning only at the actual block boundary.
- **Orchestrator annotation:** Independently confirmed by reading `event_mapper.py` L192-202 and the locking unit test directly. This is real: S-chip-06 explicitly requires the wire to keep reasoning open (no `reasoning-end`) while a tool call's parameters arrive from the same round, and the shipped code does the opposite unconditionally. Previously uncaught by both the two-axis-review that ran before this loop and the Claude-authored Spec pass above (both only inspected frontend rendering logic for the overlap case, not backend wire-close timing).

### [Major] SP-1.3: `LiveStatusAnnouncer` and an `onFinish` latch remain in production
- **Type:** Scope creep
- **Spec:** "Screen-reader: the deleted LiveStatusAnnouncer is replaced by **minimal `aria-live="polite"`** (placeholder + chip header) — not zero accessibility." (2026-07-26 comment §B)
- **File:** `frontend/src/components/pages/ChatPanel.tsx` L72
- **Problem:** `ChatPanel` still owns `lastSSEEvent`, wires `onFinish`, and renders `LiveStatusAnnouncer` at L305. That keeps a separate lifecycle announcer and finish latch beyond the placeholder + chip-header aria-live surface the spec asked for.
- **Fix:** Remove `LiveStatusAnnouncer`, `lastSSEEvent`, and the `onFinish` announcement latch unless DEV-106 is explicitly amended to keep lifecycle announcements.
- **Orchestrator annotation — VERIFIED, false positive.** Fetched DEV-60's full comment history. The 2026-07-23 F5-scope comment (id `8498adba`) explicitly lists what F5 does NOT touch: `"保留不動（非 F5 專屬，F7/其他議題）: ... LiveStatusAnnouncer（ARIA 公告，無 reasoning 專屬邏輯）"` — i.e. `LiveStatusAnnouncer` was ratified to stay, on the record, three days before the 07-26 comment this finding cites. The later 07-26 comment's "被刪的 LiveStatusAnnouncer" ("the deleted LiveStatusAnnouncer") phrase is simply an inaccurate description in that one comment — it does not override the earlier explicit "keep, out of scope" ruling, and the shipped code matches the earlier ruling exactly (component kept, no reasoning-specific logic added to it). Not accepted — no fix needed.

### [Major] SP-1.4: Placeholder window (a) keys on `streaming` with no renderable content
- **Type:** Misimplemented
- **Spec:** "The placeholder's first dead-air window keys on `status === 'submitted'` (explicitly NOT "streaming AND parts empty")." (2026-07-26 comment §C)
- **File:** `frontend/src/hooks/useDeadAirPlaceholder.ts` L40
- **Problem:** `windowA` returns waiting for `status === "submitted"` or `status === "streaming"` while the last assistant turn has no renderable content. This matches the later manual-test rationale, but it is still an unratified contradiction of the binding §C contract.
- **Fix:** Either revert window (a) to `status === "submitted"` only, or update the authoritative DEV-106/BDD spec before accepting this behavior.
- **Orchestrator annotation:** Same finding independently reached by the Claude-authored Spec pass above (SP-1.2 there). Two independent reviewers converging on this strengthens confidence it's real — already known/flagged by the author's own 2026-07-28 13:50 sync comment as pending DEV-108 reconciliation.

### [Major] SP-1.5: In-flight reload does not preserve the user prompt
- **Type:** Missing
- **Spec:** "Reload during an in-flight stream ... **drop the entire in-flight assistant turn** (no partial text/chips/error panel; the user's prompt message itself stays)." (2026-07-26 comment §B)
- **File:** `frontend/src/components/pages/ChatPanel.tsx` L38
- **Problem:** `ChatPanel` generates a fresh `chatId` on mount and passes no hydrated initial messages to `useChat`, so reload drops the whole transcript, including the user prompt. That is a vacuous "no chips survive reload" pass, not the specified in-flight reload behavior.
- **Fix:** Add or use history hydration that restores committed user messages while filtering the in-flight assistant turn, or amend the spec to say this app intentionally has no reload persistence.
- **Orchestrator annotation:** Same finding independently reached by the Claude-authored Spec pass above (SP-1.1 there) — a genuinely new gap neither prior manual testing nor the two-axis-review had surfaced. Both reviewers agree this is real and previously undisclosed.
- **User disposition (2026-07-28):** Accepted as expected — history hydration was never built in this slice; this is a known, out-of-scope gap, not a bug to fix here. No action.

## Covered Requirements

✅ AI SDK native `reasoning-start/delta/end` serialization — `backend/agent_engine/streaming/sse_serializer.py`
✅ Three domain events `ReasoningStart` / `ReasoningDelta` / `ReasoningEnd` exist — `backend/agent_engine/streaming/domain_events_schema.py`
✅ Provider reasoning deltas pass through without `\n` joining/segmenting — `backend/agent_engine/streaming/event_mapper.py`
✅ Reasoning ids are turn-unique via a per-request counter — `backend/agent_engine/streaming/event_mapper.py`
✅ Error path finalizes open reasoning before `error` + `finish` — `backend/agent_engine/agents/base.py`
✅ Abort path remains wire-silent and does not synthesize `reasoning-end` — `backend/agent_engine/agents/base.py`
✅ `FORCE_LLM_FAIL` remains in place — `backend/agent_engine/agents/base.py`
✅ Old `ReasoningSegmenter` source and reasoning dev-flag tests were deleted — git diff range
✅ `useChat.status` is modeled as exactly `submitted | streaming | ready | error` — `frontend/src/models.ts`
✅ Reasoning chips render native reasoning parts interleaved with tool cards — `frontend/src/components/organisms/AssistantMessage.tsx`
✅ Aborted half-chip header is `Stopped — thought for Xs` — `frontend/src/lib/reasoning-chips.ts`
✅ Streaming chip body uses raw `white-space: pre-wrap` and a ~4-line pinned window — `frontend/src/components/molecules/ReasoningChip.tsx`
✅ Global stall default is 10s and wall-clock based — `frontend/src/hooks/useStallTimer.ts` / `frontend/src/lib/timing.ts`
✅ Exactly one ChatPanel integration case verifies stall wiring with mocked threshold — `frontend/src/components/pages/__tests__/ChatPanel.integration.test.tsx`
