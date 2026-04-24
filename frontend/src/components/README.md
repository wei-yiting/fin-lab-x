# Components

Atomic Design 6-layer component tree for the streaming chat UI. Layers are flat folders under `src/components/`.

## Structure Map

- `primitives/` — shadcn-generated, immutable. Do NOT hand-edit; they are overwritten by `pnpm dlx shadcn@latest add`.
- `atoms/` — single-concern visual elements, no business state.
- `molecules/` — small compositions of atoms, no streaming-lifecycle concern.
- `organisms/` — feature regions that may own local UI state.
- `templates/` — layout shells.
- `pages/` — stateful orchestrators. `ChatPanel` is the sole page; it owns `useChat`, `chatId`, `abortedTools`, `lastTriggerRef`.

## State Rule

Streaming lifecycle state lives in `pages/ChatPanel.tsx` only. Atoms and molecules never import from `@ai-sdk/react`. Organisms may accept `status` / `messages` as props but do not subscribe to chat state themselves.

See `docs/frontend_chat_architecture.md` for the full layering rule, composition graph, SSE wire format, and AI SDK v6 contract findings, and `docs/frontend_dom_contract.md` for the `data-testid` / state-attribute contract.
