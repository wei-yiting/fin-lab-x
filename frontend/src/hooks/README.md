# Hooks

Custom React hooks scoped to the streaming chat lifecycle. All hooks are pure consumers of the `useChat` data stream — they never own the `useChat` instance itself (`pages/ChatPanel.tsx` does). Atoms and molecules must not consume these hooks directly; they receive derived props from `ChatPanel`.

## Files

| File                    | Responsibility                                                                                                                                                                                                                                                |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `useReasoningStatus.ts` | Tracks ephemeral reasoning sentences from `data-reasoning-status` SSE events. Owns three race guards + a `STALLED_THRESHOLD_MS = 10000` polling timer that flips `stalled=true` after 10s of silence (D14). |
| `useToolProgress.ts`    | Accumulates `data-tool-progress` SSE events into a `{ toolCallId: message }` map for `ToolCard` display.                                                                                                                                                     |
| `useFollowBottom.ts`    | Auto-scrolls a scrollable element while the user is within 100px of the bottom. `forceFollowBottom()` re-latches after a new user submit.                                                                                                                    |

## `useReasoningStatus` — Race Guards

Reasoning text shown to the user is ephemeral (`transient: true` on the SSE wire; filtered out of `message.parts` by `AssistantMessage`'s D39.b guard). Three refs guard the visible races:

| Ref               | Latched by                                | Released by         | Effect when latched                                                                                                                                                                |
| ----------------- | ----------------------------------------- | ------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `clearedRef`      | `clearReasoningStatus()` (user clears)    | `resetForNewTurn()` | All subsequent `data-reasoning-status` events are dropped — the clear is final until a new turn is sent.                                                                            |
| `finishedRef`     | `handleData({type:"finish" / "error"})`   | `resetForNewTurn()` | Late `data-reasoning-status` events arriving after the SSE close (e.g. provider tail buffered behind disconnect; dev flag `EMIT_LATE_REASONING` exercises this) are silently dropped. |
| `lastUpdateAtRef` | each `data-reasoning-status` event        | (interval reads it) | Polled every 1000ms while `reasoningStatusText !== null`; flips `stalled=true` after `STALLED_THRESHOLD_MS` of no chunks (D14 — visual signal that the model is alive but slow).    |

The two non-update refs use `useRef` (not `useState`) so the synchronous `handleData` can short-circuit without waiting for a re-render after `clear` / `finish`.

### `hideReasoningStatus()` vs `clearReasoningStatus()`

Both blank the displayed text, but they differ in whether `clearedRef` is latched. Mixing them up causes a bug that does not look like one — the next turn's reasoning never renders.

| Action                       | When to call                                                                                                                              | Effect                                                                                                |
| ---------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| `hideReasoningStatus()`      | Mid-turn — a text / tool part lands and the next LLM call may still emit reasoning. `ChatPanel`'s `useLayoutEffect` calls this on `parts.length` growth. Also called by `ChatPanel.handleStop` so the next turn can still show reasoning. | Blanks displayed text only. `clearedRef` stays unlatched, so the next reasoning chunk shows again.    |
| `clearReasoningStatus()`     | User pressed Clear (explicit conversation reset).                                                                                         | Blanks text AND latches `clearedRef`. Any buffered SSE events still in flight are dropped.            |
| `resetForNewTurn()`          | New send / regenerate / retry begins.                                                                                                     | Blanks text and clears both `clearedRef` + `finishedRef`. **Required before the next stream starts.** |

`ChatPanel.handleStop` deliberately calls `hideReasoningStatus()` (not `clearReasoningStatus()`) — latching `clearedRef` on user stop would prevent the next turn's reasoning from rendering at all.

`ChatPanel.handleRetry` calls `resetForNewTurn()` so the prior `finishedRef` latch (set by the `error`/`finish` that triggered the retry) does not block reasoning on the retried turn.

## Testing

Race guards have heavy unit coverage in `__tests__/useReasoningStatus.test.ts`. Add cases there when changing any of the three refs above; integration coverage for the `ChatPanel`-level interactions (`handleStop`, `handleRetry`, `useLayoutEffect` auto-hide) lives in `components/pages/__tests__/ChatPanel.integration.test.tsx`.
