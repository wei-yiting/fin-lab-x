# Components

Atomic Design 6-layer component tree for the streaming chat UI. Layers are flat folders under `src/components/`.

## Structure Map

- `primitives/` — shadcn-generated, immutable. Do NOT hand-edit; they are overwritten by `pnpm dlx shadcn@latest add`.
- `atoms/` — single-concern visual elements, no business state (e.g. `StatusDot`, `RefSup`, `Cursor`, `PromptChip`, `RegenerateButton`, `TypingIndicator`).
- `molecules/` — small compositions of atoms, no streaming-lifecycle concern (e.g. `SourceLink`, `ToolRow`, `ToolDetail`, `UserMessage`, `Sources`).
- `organisms/` — feature regions that may own local UI state (e.g. `ChatHeader`, `AssistantMessage`, `ToolCard`, `Markdown`, `ErrorBlock`, `Composer`, `EmptyState`).
- `templates/` — layout shells (`MessageList`).
- `pages/` — stateful orchestrators. `ChatPanel` is the sole page; it owns `useChat`, `chatId`, `abortedTools`, `lastTriggerRef`.

## State Rule

Streaming lifecycle state lives in `pages/ChatPanel.tsx` only. Atoms and molecules never import from `@ai-sdk/react`. Organisms may accept `status` / `messages` as props but do not subscribe to chat state themselves.

## Extension Guideline

- A new visual element used in one place should be inlined first; extract to `atoms/` only when reused at least twice.
- Do not create `features/` or `hooks/` subfolders here — hooks live in `frontend/src/hooks/`.
- Do not add new `pages/` files unless scope expands beyond the chat panel.

## Testing

Every non-primitive layer has a sibling `__tests__/` directory. `data-testid="..."` attributes are permanently shipped (see `implementation_prerequisites_streaming_chat_ui.md` §1).
