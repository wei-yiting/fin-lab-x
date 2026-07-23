# Atoms

Single-concern visual elements. No business state, no `useChat`, no streaming-lifecycle subscription — atoms receive everything they need as props. See `frontend/src/components/README.md` for the full layering rule.

## Files

| File                      | Responsibility                                                                                                                                                   |
| ------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Cursor.tsx`              | Blinking cursor appended to a streaming text block.                                                                                                              |
| `LiveStatusAnnouncer.tsx` | Screen-reader announcer for chat lifecycle (`role="status"` + `aria-live="polite"`). Visual indicators are `aria-hidden="true"` — this is the single SR surface. |
| `live-status-text.ts`     | Pure `(status, lastEvent) → string` formatter for `LiveStatusAnnouncer`. Exported so the transition table is unit-testable.                                      |
| `PromptChip.tsx`          | Clickable prompt suggestion chip in the empty state.                                                                                                             |
| `ReasoningIndicator.tsx`  | Ephemeral reasoning status indicator. Renders one of four visual modes from `text` + `state` + `stalled` props.                                                  |
| `RefSup.tsx`              | Superscript reference link `[1]` rendered inline in markdown.                                                                                                    |
| `RegenerateButton.tsx`    | "Regenerate" button on the last assistant message. Gated by `AssistantMessage` C2.a — hidden when there is nothing meaningful to regenerate from.                |
| `SourceLink.tsx`          | Single source list item under the assistant turn.                                                                                                                |
| `StatusDot.tsx`           | Status indicator dot used in `ChatHeader`.                                                                                                                       |
| `UserMessage.tsx`         | User-side message bubble.                                                                                                                                        |

## `ReasoningIndicator` — Visual Modes

A single `.reasoning-status` container renders four visual modes. All modes share the same vertical-slot height (`calc(0.72rem * 1.5)`) so transitions do not produce layout jumps (D5 / D17 / D21).

| `text`       | `state`       | `stalled` | Rendered                                                                                            |
| ------------ | ------------- | --------- | --------------------------------------------------------------------------------------------------- |
| empty / null | `"streaming"` | any       | 3 bouncing idle dots (`.idle-dots`) — pre-response idle.                                            |
| non-empty    | `"streaming"` | `false`   | Trimmed reasoning text + `.reasoning-status-dots-cycler` (`.` → `..` → `...` loop).                 |
| non-empty    | `"streaming"` | `true`    | Same as above, but `.stalled` modifier on the wrapper dims the text and slows the cycler.           |
| non-empty    | `"frozen"`    | any       | Reasoning text at `opacity: 0.65` followed by an inline `STOPPED` label (Stop-B / Stop-C-pre-text). |
| empty / null | `"frozen"`    | any       | `STOPPED` label only — user halted before any reasoning text arrived (Stop-A).                      |

The container is always `aria-hidden="true"` — reasoning text is decorative. `LiveStatusAnnouncer` is the single SR surface for chat lifecycle.

Reasoning text passes through `trimTrailingDelim()` before display: providers emit trailing punctuation (`.`, `。`, `…`, `，`) that would visually collide with the cycler dots and read as two collapsed loaders.

## `LiveStatusAnnouncer` — ARIA Hybrid

The split between this announcer and the visual reasoning / tool affordances follows the hybrid ARIA pattern (D22):

- **Visual ephemeral indicators** (`ReasoningIndicator`, `ToolCard`) — `aria-hidden="true"`. They change too frequently to be polite-queued by a screen reader; queueing every reasoning sentence would lock SR users out of the response.
- **Lifecycle transitions** (`finish` / `error`) — announced through this single `role="status" aria-live="polite"` element. Text comes from `formatStatusText(status, lastEvent)`.

Precedence in `formatStatusText`: `status === "error"` always wins over a stale `finish` event, so SR users hear the failure path even when the last successful chunk was a finish.

AI SDK v6 routes generic SSE chunks (`start`, `tool-input-available`, `tool-output-available`) through state callbacks that are not exposed via `onData` — only `finish` reaches `LiveStatusAnnouncer`, and it arrives via `onFinish` on `useChat`, not `onData`. Tool-call announcements are deferred (would require a `messages.parts` watcher).

## Stop Sub-States

The Stop button can fire at three meaningfully different moments. `ChatPanel.handleStop` captures the in-flight state into `abortedMessages` / `abortedTools` so the renderer can attach the right STOPPED affordance to the right element across the rest of the chat.

| Sub-state | When                                                                              | Affordance                                                                                                                                                        |
| --------- | --------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Stop-A    | No reasoning text yet (pre-response idle, or pure-tool aborts with no reasoning). | `ReasoningIndicator` renders the text-less STOPPED variant. `RegenerateButton` is hidden — there is nothing to regenerate from (`AssistantMessage` C2.a gating).  |
| Stop-B    | Reasoning text was visible at stop time; no assistant text part has streamed yet. | `ReasoningIndicator` renders frozen-with-text: captured reasoning at 65% opacity + inline `STOPPED` label.                                                        |
| Stop-C    | Assistant text was already streaming, or a tool was running.                      | `AssistantMessage` appends an inline `STOPPED` label inside the partial text (`data-testid="text-stopped-label"`). Any running `ToolCard` flips to aborted state. |

Stop-C with text → `RegenerateButton` shows. Stop-A or Stop-C-with-only-tool-parts → `RegenerateButton` hides (the backend regenerate endpoint requires a finalized `AIMessage` in LangGraph state; mid-reasoning aborts often leave the checkpoint without one and the request would 422).

## Testing

Atoms have unit coverage in `__tests__/<Component>.test.tsx`. Reasoning indicator mode transitions, LiveStatusAnnouncer precedence, and Stop A/B/C affordances are exercised at the integration layer in `components/pages/__tests__/ChatPanel.integration.test.tsx` and the visual lifecycle Playwright specs under `frontend/tests/e2e/lifecycle/`.
