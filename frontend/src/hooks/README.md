# Hooks

Custom React hooks scoped to the streaming chat lifecycle. All hooks are pure consumers of the `useChat` data stream — they never own the `useChat` instance itself (`pages/ChatPanel.tsx` does). Atoms and molecules must not consume these hooks directly; they receive derived props from `ChatPanel`.

## Files

| File                       | Responsibility                                                                                                                                                                                                                                                                                                                                                                                                        |
| -------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `useStallTimer.ts`         | Global single stall stopwatch. Wall-clock based; any stream part arrival resets it via `notifyActivity()`; flips `stalled=true` after `STALL_THRESHOLD_MS` (10s, from `lib/timing.ts`) of silence. Degraded copy consumer: the dead-air placeholder.                                                                                                                                                                  |
| `useReasoningTimers.ts`    | Client-side "Thought for Xs" measurement per reasoning chip: clock starts when the reasoning part first appears, freezes at the arrival of the round's next part (first tool-start — tool execution excluded), abort samples at Stop. Wall-clock delta, keyed by `chipKey(messageId, partIndex)`. Not yet wired into a page — `ChatPanel` picks it up when reasoning is turned on.                                    |
| `useDeadAirPlaceholder.ts` | Placeholder visibility for the three dead-air windows: submit → first renderable content (`submitted`, plus `streaming` while the turn has painted nothing — reasoning deltas can lag `reasoning-start` by seconds); chip collapse → reply text; and tool round complete → next content. The latter two anchor on the last _renderable_ part and are held behind `PLACEHOLDER_GRACE_MS` so micro-gaps never flash it. |
| `useToolProgress.ts`       | Accumulates `data-tool-progress` SSE events into a `{ toolCallId: message }` map for `ToolCard` display.                                                                                                                                                                                                                                                                                                              |
| `useFollowBottom.ts`       | Auto-scrolls a scrollable element while the user is within 100px of the bottom. `forceFollowBottom()` re-latches after a new user submit.                                                                                                                                                                                                                                                                             |

## Non-derived state budget

The placeholder derives everything from `useChat`'s `(status, messages)`. Two non-derived stores are allowed so far, each owned by the hook that needs it:

1. **Global stall stopwatch** (`useStallTimer`) — no timestamps travel on the wire, so silence is measured client-side against wall-clock time.
2. **Placeholder grace timer** (`useDeadAirPlaceholder`'s `elapsedGapKey` + `setTimeout`-backed `PLACEHOLDER_GRACE_MS`) — the wire gives no lookahead, so a short grace window is needed to distinguish "chip/tool round done → next tool call" from "→ reply text" without flashing the placeholder on that micro-gap.

`ChatPanel` also keeps the turn interruption record (`interruptedMessages`) and the tool-abort set (`abortedTools`) — see `components/pages/README.md`.

## Testing

`__tests__/useStallTimer.test.ts` locks the 10s default with fake timers; `__tests__/useDeadAirPlaceholder.test.ts` covers all three dead-air windows plus the grace-delay suppression. Exactly one ChatPanel integration case (mocked small threshold + MSW real time) verifies the stall wiring in `components/pages/__tests__/ChatPanel.integration.test.tsx`.
