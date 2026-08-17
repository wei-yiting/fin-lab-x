# Atoms

Single-concern visual elements. No business state, no `useChat`, no streaming-lifecycle subscription — atoms receive everything they need as props. See `frontend/src/components/README.md` for the full layering rule.

## Files

| File                      | Responsibility                                                                                                                                                                                                                                                           |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `ActivityPlaceholder.tsx` | Dead-air placeholder (F6′): `Thinking` / `Still working` copy with a CSS-animated dots cycler (`aria-hidden`) for the windows where the screen has no live element. Visibility derived by `ChatPanel` via `useDeadAirPlaceholder`; carries its own `aria-live="polite"`. |
| `Cursor.tsx`              | Blinking cursor appended to a streaming text block.                                                                                                                                                                                                                      |
| `InterruptedMarker.tsx`   | "Interrupted" row rendered under a turn the user stopped (DEV-109 ruling 11).                                                                                                                                                                                            |
| `PromptChip.tsx`          | Clickable prompt suggestion chip in the empty state.                                                                                                                                                                                                                     |
| `RefSup.tsx`              | Superscript reference link `[1]` rendered inline in markdown.                                                                                                                                                                                                            |
| `RegenerateButton.tsx`    | "Regenerate" button on the last assistant message.                                                                                                                                                                                                                       |
| `SourceLink.tsx`          | Single source list item under the assistant turn.                                                                                                                                                                                                                        |
| `StatusDot.tsx`           | Status indicator dot used in `ChatHeader`.                                                                                                                                                                                                                               |
| `UserMessage.tsx`         | User-side message bubble.                                                                                                                                                                                                                                                |

## Testing

Atoms have unit coverage in `__tests__/<Component>.test.tsx`. `ActivityPlaceholder`'s visibility and stall-degraded copy are exercised at the integration layer in `components/pages/__tests__/ChatPanel.integration.test.tsx`.
