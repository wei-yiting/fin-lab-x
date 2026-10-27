# Hooks

Custom React hooks scoped to the streaming chat lifecycle. All hooks are pure consumers of the `useChat` data stream — they never own the `useChat` instance itself (`pages/ChatPanel.tsx` does). Atoms and molecules must not consume these hooks directly; they receive derived props from `ChatPanel`.

## Files

| File                       | Responsibility                                                                                                                                                                                                                                                                                                                                                                                                        |
| -------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `useStallTimer.ts`         | Global single stall stopwatch. Wall-clock based; any stream part arrival resets it via `notifyActivity()`; flips `stalled=true` after `STALL_THRESHOLD_MS` (10s, from `lib/timing.ts`) of silence. Degraded copy consumers: the dead-air placeholder and the streaming chip header.                                                                                                                                   |
| `useReasoningTimers.ts`    | Client-side "Thought for Xs" measurement per chip: clock starts when the reasoning part first appears, freezes at the arrival of the round's next part (first tool-start — tool execution excluded), abort samples at Stop. Wall-clock delta, keyed by `chipKey(messageId, partIndex)`.                                                                                                                               |
| `useDeadAirPlaceholder.ts` | Placeholder visibility for the three dead-air windows: submit → first renderable content (`submitted`, plus `streaming` while the turn has painted nothing — reasoning deltas can lag `reasoning-start` by seconds); chip collapse → reply text; and tool round complete → next content. The latter two anchor on the last _renderable_ part and are held behind `PLACEHOLDER_GRACE_MS` so micro-gaps never flash it. |
| `useToolProgress.ts`       | Accumulates `data-tool-progress` SSE events into a `{ toolCallId: message }` map for `ToolCard` display.                                                                                                                                                                                                                                                                                                              |
| `useFollowBottom.ts`       | Auto-scrolls a scrollable element while the user is within 100px of the bottom. `forceFollowBottom()` re-latches after a new user submit.                                                                                                                                                                                                                                                                             |

## Non-derived state budget

The chips system derives everything from `useChat`'s `(status, messages)` — native `reasoning` parts included. Four non-derived stores are allowed, owned by `ChatPanel` or the hook that needs them:

1. **Chip timing map** (`useReasoningTimers`'s `timings` state map, owned by the hook) — reasoning parts carry no timestamps on the wire, so a chip's "Thought for Xs" duration can only be measured client-side against wall-clock time (ADR-0015 records this as deliberate non-derived state).
2. **Global stall stopwatch** (`useStallTimer`, owned by the hook) — no timestamps travel on the wire, so silence is measured client-side against wall-clock time.
3. **Expand/collapse override map** (`Map<chipKey, boolean>` in `ChatPanel` state) — the user's toggle beats the tail-only expansion derivation; cleared on every new turn / regenerate / retry.
4. **Placeholder grace timer** (`useDeadAirPlaceholder`'s `elapsedGapKey` + `setTimeout`-backed `PLACEHOLDER_GRACE_MS`, owned by the hook) — the wire gives no lookahead, so a short grace window is needed to distinguish "chip/tool round done → next tool call" from "→ reply text" without flashing the placeholder on that micro-gap.

Aborted-**chip** detection needs no store: an aborted chip is simply a reasoning part whose `state` is still `"streaming"` after the chat status left the active pair (no `reasoning-end` reached the wire).

`ChatPanel` also keeps the turn interruption record (`interruptedMessages`) and the tool-abort set (`abortedTools`) — see `components/pages/README.md`.

## Testing

`__tests__/useStallTimer.test.ts` locks the 10s default with fake timers; `__tests__/useReasoningTimers.test.ts` covers freeze-at-tool-start, abort sampling, and reset; `__tests__/useDeadAirPlaceholder.test.ts` covers all three dead-air windows plus the grace-delay suppression. Exactly one ChatPanel integration case (mocked small threshold + MSW real time) verifies the stall wiring in `components/pages/__tests__/ChatPanel.integration.test.tsx`.
