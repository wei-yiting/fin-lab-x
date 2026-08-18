# Pages

Stateful orchestrator layer — the top of the atomic-design tree. Pages own streaming lifecycle state and wire `useChat` to the rest of the component tree. See `frontend/src/components/README.md` for the full layering rule.

## Files

| File            | Responsibility                                                                                                                                                                                                                                                                                                                       |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `ChatPanel.tsx` | Sole streaming-chat orchestrator. Owns `useChat({ transport, onData })`, `chatId`, `abortedTools`, `interruptedMessages`, `lastTriggerRef`, the dead-air placeholder's non-derived state (`useStallTimer`, `useDeadAirPlaceholder`'s grace timer), `useToolProgress`. Composes `MessageList` (templates) and `Composer` (organisms). |

## State rule

Streaming lifecycle state lives here only. Atoms / molecules / organisms never import from `@ai-sdk/react`. Organisms may accept `status` / `messages` as props but must not subscribe to chat state themselves. Everything the dead-air placeholder needs derives from `(status, messages)` except the two stores listed in `src/hooks/README.md`.

## Tests

```bash
pnpm -C frontend test -- --run ChatPanel.integration
```

`__tests__/ChatPanel.integration.test.tsx` covers smart retry, mid-stream retry, aborted tools via stop, stop during the dead-air placeholder window, the stall-degradation wiring (mocked small threshold + MSW real time), and stop + clear.

E2E specs for cross-page flows live in `frontend/tests/e2e/`.
