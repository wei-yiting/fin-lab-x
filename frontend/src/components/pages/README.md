# Pages

Stateful orchestrator layer — the top of the atomic-design tree. Pages own streaming lifecycle state and wire `useChat` to the rest of the component tree. See `frontend/src/components/README.md` for the full layering rule.

## Files

| File            | Responsibility                                                                                                                                                                                                                                                                                                                       |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `ChatPanel.tsx` | Sole streaming-chat orchestrator. Owns `useChat({ transport, onData, onFinish, onError })`, `chatId`, `abortedTools`, `abortedMessages`, `lastTriggerRef`, `useReasoningStatus`, `useToolProgress`, `LiveStatusAnnouncer` wiring. Composes `MessageList` (templates), `Composer` (organisms), and the live-status announcer (atoms). |

## State rule

Streaming lifecycle state lives here only. Atoms / molecules / organisms never import from `@ai-sdk/react`. Organisms may accept `status` / `messages` as props but must not subscribe to chat state themselves. The reasoning indicator is ephemeral — `data-reasoning-*` parts are filtered out of `message.parts` (D39 belt-and-suspenders) and only drive the indicator through `useReasoningStatus.handleData(onData)`.

## `onFinish` contract

AI SDK v6's `onFinish` payload carries `{ message, messages, isAbort, isDisconnect, isError }`. `ChatPanel` short-circuits `setLastSSEEvent({ type: "finish" })` whenever any of the three failure flags is `true` — otherwise `LiveStatusAnnouncer` would announce "Response complete" on user stop, network disconnect, or SSE error. `handleReasoningData({ type: "finish" })` is still called to latch the reasoning hook's `finishedRef` so late `data-reasoning-status` chunks are dropped.

## Tests

```bash
pnpm -C frontend test -- --run ChatPanel.integration
```

`__tests__/ChatPanel.integration.test.tsx` covers:

- onFinish flag matrix: natural completion announces "Response complete"; abort / isError / isDisconnect do NOT.
- Reasoning indicator lifecycle (clear / hide / reset for new turn).
- Abort-then-resend journey.
- Tool-progress hookup.

E2E specs for cross-page flows live in `frontend/tests/e2e/`. Visual reasoning lifecycle / abort sub-states / multi-provider matrix are covered there with `playwright.config.ts` `use.video: 'on'`.
