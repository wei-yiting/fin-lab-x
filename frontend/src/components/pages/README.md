# Pages

Stateful orchestrator layer — the top of the atomic-design tree. Pages own streaming lifecycle state and wire `useChat` to the rest of the component tree. See `frontend/src/components/README.md` for the full layering rule.

## Files

| File            | Responsibility                                                                                                                                                                                                                                                                                                                                                        |
| --------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ChatPanel.tsx` | Sole streaming-chat orchestrator. Owns `useChat({ transport, onData, onFinish })`, `chatId`, `abortedTools`, `lastTriggerRef`, the three non-derived chip stores (`useStallTimer`, `useReasoningTimers`, chip override map), `useDeadAirPlaceholder`, `useToolProgress`, `LiveStatusAnnouncer` wiring. Composes `MessageList` (templates) and `Composer` (organisms). |

## State rule

Streaming lifecycle state lives here only. Atoms / molecules / organisms never import from `@ai-sdk/react`. Organisms may accept `status` / `messages` as props but must not subscribe to chat state themselves. Reasoning renders from native `reasoning` message parts (chips — ADR-0006); everything derives from `(status, messages)` except the three stores listed in `src/hooks/README.md`.

## `onFinish` contract

AI SDK v6's `onFinish` payload carries `{ message, messages, isAbort, isDisconnect, isError }`. `ChatPanel` short-circuits `setLastSSEEvent({ type: "finish" })` whenever any of the three failure flags is `true` — otherwise `LiveStatusAnnouncer` would announce "Response complete" on user stop, network disconnect, or SSE error.

## Tests

```bash
pnpm -C frontend test -- --run ChatPanel.integration
```

`__tests__/ChatPanel.integration.test.tsx` covers:

- onFinish flag matrix: natural completion announces "Response complete"; abort / isError / isDisconnect do NOT.
- Reasoning chips golden path (stream → collapse → post-hoc expand).
- Abort mid-reasoning → collapsed `Stopped — thought for Xs` half-chip; abort-then-resend coexistence.
- The single stall-wiring case (mocked small threshold + MSW real time — F6 ruling).
- Tool-progress hookup.

E2E specs for cross-page flows live in `frontend/tests/e2e/`.
