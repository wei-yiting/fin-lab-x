# Atoms

Single-concern visual elements. No business state, no `useChat`, no streaming-lifecycle subscription — atoms receive everything they need as props. See `frontend/src/components/README.md` for the full layering rule.

## Files

| File                      | Responsibility                                                                                                                                                                                                                                                     |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `ActivityPlaceholder.tsx` | Dead-air placeholder: `Thinking` / `Still working` copy with a CSS-animated dots cycler (`aria-hidden`) for the windows where the screen has no live element. Visibility derived by `ChatPanel` via `useDeadAirPlaceholder`; carries its own `aria-live="polite"`. |
| `Cursor.tsx`              | Blinking cursor appended to a streaming text block.                                                                                                                                                                                                                |
| `InterruptedMarker.tsx`   | "Interrupted" row rendered under a turn the user stopped.                                                                                                                                                                                                          |
| `PromptChip.tsx`          | Clickable prompt suggestion chip in the empty state.                                                                                                                                                                                                               |
| `RefSup.tsx`              | Superscript reference link `[1]` rendered inline in markdown.                                                                                                                                                                                                      |
| `RegenerateButton.tsx`    | "Regenerate" button on the last assistant message.                                                                                                                                                                                                                 |
| `SourceLink.tsx`          | Single source list item under the assistant turn.                                                                                                                                                                                                                  |
| `StatusDot.tsx`           | Tool status indicator dot, rendered by `molecules/ToolRow`.                                                                                                                                                                                                        |
| `UserMessage.tsx`         | User-side message bubble.                                                                                                                                                                                                                                          |

## Testing

Atoms are covered where their behaviour warrants it rather than one test file each; unit tests live in `__tests__/<Component>.test.tsx`. Today that folder holds a single file, `ActivityPlaceholder.test.tsx`, covering both copy states and the `aria-live` contract — the rest of the atoms are pure prop-to-markup and are exercised through their consumers' tests. `ActivityPlaceholder`'s _visibility_ is not this component's concern: it is derived by `useDeadAirPlaceholder` (hook unit tests) and wired in `components/pages/__tests__/ChatPanel.integration.test.tsx`.
