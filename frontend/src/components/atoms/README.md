# Atoms

Single-concern visual elements. No business state, no `useChat`, no streaming-lifecycle subscription — atoms receive everything they need as props. See `frontend/src/components/README.md` for the full layering rule.

## Files

| File                      | Responsibility                                                                                                                                                                                                                                                     |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `ActivityPlaceholder.tsx` | Dead-air placeholder: `Thinking` / `Still working` copy with a CSS-animated dots cycler (`aria-hidden`) for the windows where the screen has no live element. Visibility derived by `ChatPanel` via `useDeadAirPlaceholder`; carries its own `aria-live="polite"`. |
| `Cursor.tsx`              | Blinking cursor appended to a streaming text block.                                                                                                                                                                                                                |
| `LiveStatusAnnouncer.tsx` | Screen-reader announcer for chat lifecycle (`role="status"` + `aria-live="polite"`).                                                                                                                                                                               |
| `live-status-text.ts`     | Pure `(lastEvent) → string` formatter for `LiveStatusAnnouncer`. Exported so the transition table is unit-testable.                                                                                                                                                |
| `InterruptedMarker.tsx`   | "Interrupted" row rendered under a turn the user stopped.                                                                                                                                                                                                          |
| `PromptChip.tsx`          | Clickable prompt suggestion chip in the empty state.                                                                                                                                                                                                               |
| `RefSup.tsx`              | Superscript reference link `[1]` rendered inline in markdown.                                                                                                                                                                                                      |
| `RegenerateButton.tsx`    | "Regenerate" button on the last assistant message.                                                                                                                                                                                                                 |
| `SourceLink.tsx`          | Single source list item under the assistant turn.                                                                                                                                                                                                                  |
| `StatusDot.tsx`           | Tool status indicator dot, rendered by `molecules/ToolRow`.                                                                                                                                                                                                        |
| `UserMessage.tsx`         | User-side message bubble.                                                                                                                                                                                                                                          |

The reasoning surface itself lives two layers up: `organisms/ReasoningChip.tsx` renders each native `reasoning` message part as a collapsible transcript chip.

## ARIA surfaces (minimal `aria-live`)

- **`LiveStatusAnnouncer`** — single `role="status" aria-live="polite"` element for the natural-completion event (`finish`). Errors are announced separately by `ErrorBlock`'s `role="alert"`, so a failure is never read out twice.
- **`ActivityPlaceholder` + `ReasoningChip` header** — each carries `aria-live="polite"` announcing only high-level state (`Thinking…`, `Still working…`, `Thought for Xs`). Reasoning body text is never fed into the polite queue; `ToolCard` remains fully accessible (no `aria-hidden`).

## Stop behavior

- An aborted reasoning part (state stuck `"streaming"` once the chat status leaves the active pair) collapses to a `Stopped — thought for Xs` chip header — derived from part shape, no per-message bookkeeping.
- A running `ToolCard` at stop time flips to the aborted visual state via `ChatPanel`'s `abortedTools` set, with the turn-level `interrupted` record as the fallback for a tool call that arrived inside the throttle window right before Stop.
- `RegenerateButton` never renders for an interrupted turn: `MessageList` only passes `onRegenerate` for the last message of a ready transcript and `AssistantMessage` additionally gates on the turn-level `interrupted` record.

## Testing

Atoms are covered where their behaviour warrants it rather than one test file each; unit tests live in `__tests__/<Component>.test.tsx`. Today that folder holds `ActivityPlaceholder.test.tsx` (both copy states and the `aria-live` contract) and `LiveStatusAnnouncer.test.tsx` (the `formatStatusText` transition table) — the rest of the atoms are pure prop-to-markup and are exercised through their consumers' tests. Chip states are covered in `organisms/__tests__/ReasoningChip.test.tsx`. `ActivityPlaceholder`'s _visibility_ is not this component's concern: it is derived by `useDeadAirPlaceholder` (hook unit tests) and wired in `components/pages/__tests__/ChatPanel.integration.test.tsx`.
