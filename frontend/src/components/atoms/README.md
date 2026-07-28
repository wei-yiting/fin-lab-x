# Atoms

Single-concern visual elements. No business state, no `useChat`, no streaming-lifecycle subscription — atoms receive everything they need as props. See `frontend/src/components/README.md` for the full layering rule.

## Files

| File                      | Responsibility                                                                                                                                                                                                                              |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ActivityPlaceholder.tsx` | Dead-air placeholder (F6′): `Thinking…` / `Still working…` copy for the two windows where the screen has no live element. Visibility derived by `ChatPanel` via `useDeadAirPlaceholder`; carries its own `aria-live="polite"` (decision 8). |
| `Cursor.tsx`              | Blinking cursor appended to a streaming text block.                                                                                                                                                                                         |
| `LiveStatusAnnouncer.tsx` | Screen-reader announcer for chat lifecycle (`role="status"` + `aria-live="polite"`).                                                                                                                                                        |
| `live-status-text.ts`     | Pure `(status, lastEvent) → string` formatter for `LiveStatusAnnouncer`. Exported so the transition table is unit-testable.                                                                                                                 |
| `PromptChip.tsx`          | Clickable prompt suggestion chip in the empty state.                                                                                                                                                                                        |
| `RefSup.tsx`              | Superscript reference link `[1]` rendered inline in markdown.                                                                                                                                                                               |
| `RegenerateButton.tsx`    | "Regenerate" button on the last assistant message. Gated by `AssistantMessage` C2.a — hidden when there is nothing meaningful to regenerate from.                                                                                           |
| `SourceLink.tsx`          | Single source list item under the assistant turn.                                                                                                                                                                                           |
| `StatusDot.tsx`           | Status indicator dot used in `ChatHeader`.                                                                                                                                                                                                  |
| `UserMessage.tsx`         | User-side message bubble.                                                                                                                                                                                                                   |

The reasoning surface itself lives one layer up: `molecules/ReasoningChip.tsx` renders each native `reasoning` message part as a collapsible transcript chip (ADR-0006). The former `ReasoningIndicator` 19-state system was removed with DEV-106.

## ARIA surfaces (decision 8 — minimal `aria-live`)

- **`LiveStatusAnnouncer`** — single `role="status" aria-live="polite"` element for lifecycle transitions (`finish` / `error`). Precedence in `formatStatusText`: `status === "error"` always wins over a stale `finish` event.
- **`ActivityPlaceholder` + `ReasoningChip` header** — each carries `aria-live="polite"` announcing only high-level state (`Thinking…`, `Still working…`, `Thought for Xs`). Reasoning body text is never fed into the polite queue; `ToolCard` stays `aria-hidden`.

## Stop behavior

Stop affordances are derived from part shapes, with no per-message bookkeeping:

- An aborted reasoning part (state stuck `"streaming"` at `status === "ready"`) collapses to a `Stopped — thought for Xs` chip header (decision 6).
- A running `ToolCard` at stop time flips to the aborted visual state via `ChatPanel`'s `abortedTools` set.
- `RegenerateButton` hides on aborted turns without a text body (the backend regenerate endpoint requires a finalized `AIMessage` in LangGraph state; mid-reasoning aborts often leave the checkpoint without one and the request would 422).

## Testing

Atoms have unit coverage in `__tests__/<Component>.test.tsx`. Chip states, placeholder windows, and abort affordances are exercised in `molecules/__tests__/ReasoningChip.test.tsx`, the hook tests under `src/hooks/__tests__/`, and the integration layer in `components/pages/__tests__/ChatPanel.integration.test.tsx`.
