# Hooks

Custom React hooks scoped to the streaming chat lifecycle. All hooks are pure consumers of the `useChat` data stream — they never own the `useChat` instance itself (`pages/ChatPanel.tsx` does). Atoms and molecules must not consume these hooks directly; they receive derived props from `ChatPanel`.

## Files

| File                       | Responsibility                                                                                                                                                                                                                                                                                       |
| -------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `useStallTimer.ts`         | Global single stall stopwatch (F6). Wall-clock based; any stream part arrival resets it via `notifyActivity()`; flips `stalled=true` after `STALL_THRESHOLD_MS` (10s, from `lib/timing.ts`) of silence. Degraded copy consumers: the activity placeholder and the streaming chip header.             |
| `useReasoningTimers.ts`    | Client-side "Thought for Xs" measurement per chip (decision 2): clock starts when the reasoning part first appears, freezes at the arrival of the round's next part (first tool-start — tool execution excluded), abort samples at Stop. Wall-clock delta, keyed by `chipKey(messageId, partIndex)`. |
| `useDeadAirPlaceholder.ts` | Placeholder visibility for the two dead-air windows: `status === "submitted"` → first content, and chip collapse → reply text (held behind `PLACEHOLDER_GRACE_MS` so the chip→tool micro-gap never flashes it — decision 5).                                                                         |
| `useToolProgress.ts`       | Accumulates `data-tool-progress` SSE events into a `{ toolCallId: message }` map for `ToolCard` display.                                                                                                                                                                                             |
| `useFollowBottom.ts`       | Auto-scrolls a scrollable element while the user is within 100px of the bottom. `forceFollowBottom()` re-latches after a new user submit.                                                                                                                                                            |

## Non-derived state budget (F6′ / ADR-0006)

The chips system derives everything from `useChat`'s `(status, messages)` — native `reasoning` parts included. Exactly three non-derived stores are allowed, all owned by `ChatPanel`:

1. **Chip timing map** (`useReasoningTimers`) — parts carry no timestamps, so duration is measured client-side.
2. **Global stall stopwatch** (`useStallTimer`).
3. **Expand/collapse override map** (`Map<chipKey, boolean>` in `ChatPanel` state) — the user's toggle beats the tail-only expansion derivation; cleared on every new turn / regenerate / retry (QA16).

Abort detection needs no store: an aborted chip is simply a reasoning part whose `state` is still `"streaming"` after the chat status left the active pair (no `reasoning-end` reached the wire).

## Testing

`__tests__/useStallTimer.test.ts` locks the 10s default with fake timers (F6 ruling); `__tests__/useReasoningTimers.test.ts` covers freeze-at-tool-start, abort sampling, and per-turn reset; `__tests__/useDeadAirPlaceholder.test.ts` covers both windows plus the grace-delay suppression. Exactly one ChatPanel integration case (mocked small threshold + MSW real time) verifies the stall wiring in `components/pages/__tests__/ChatPanel.integration.test.tsx`.
