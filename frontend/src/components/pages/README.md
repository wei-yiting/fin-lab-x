# Pages

Stateful orchestrator layer — the top of the atomic-design tree. Pages own streaming lifecycle state and wire `useChat` to the rest of the component tree. See `frontend/src/components/README.md` for the full layering rule.

## Files

| File            | Responsibility                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `ChatPanel.tsx` | Sole streaming-chat orchestrator. Owns `useChat({ transport, onData, onFinish })`, `chatId`, `abortedTools`, `interruptedMessages`, `lastTriggerRef`, the chips system's non-derived stores (`useStallTimer`, `useReasoningTimers`, the chip expand/collapse override map, `useDeadAirPlaceholder`'s grace timer), `useToolProgress`, and the inline `role="status"` completion announcement. Composes `MessageList` (templates) and `Composer` (organisms). |

## State rule

Streaming lifecycle state lives here only. Atoms / molecules / organisms never import from `@ai-sdk/react`. Organisms may accept `status` / `messages` as props but must not subscribe to chat state themselves. Reasoning renders from native `reasoning` message parts (chips); everything derives from `(status, messages)` except the stores listed in `src/hooks/README.md`.

## `onFinish` contract

AI SDK v6's `onFinish` payload carries `{ message, messages, isAbort, isDisconnect, isError }`. `ChatPanel` short-circuits `setResponseComplete(true)` whenever any of the three failure flags is `true` — otherwise the inline `role="status"` region would announce `copy.chatPanel.responseComplete` on user stop, network disconnect, or SSE error.

## Tests

```bash
pnpm -C frontend test -- --run ChatPanel.integration
```

`__tests__/ChatPanel.integration.test.tsx` covers smart retry, mid-stream retry, aborted tools via stop, stop during the dead-air placeholder window, the stall-degradation wiring (mocked small threshold + MSW real time — placeholder copy and streaming chip header), stop + clear, the `onFinish` flag matrix (natural completion announces `copy.chatPanel.responseComplete`; abort / isError / isDisconnect do not), the reasoning chips golden path (stream → collapse), abort mid-reasoning → collapsed `copy.reasoningChip.stoppedThoughtFor()` half-chip, and abort-then-resend coexistence.

E2E specs for cross-page flows live in `frontend/tests/e2e/`.
